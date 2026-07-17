from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional
import uuid
import os
import aiofiles
from fastapi.staticfiles import StaticFiles

from app.database import get_db
from app.models import (
    User, Teacher, TeacherSubject, Student, StudentEnrollment, Class, Material,
    UserType, LanguageStream, TeacherApprovalStatus, Assignment,
    generate_class_code, AssignmentSubmission, StudentFlag
)
from app.services.auth import get_current_teacher, get_current_user
from app.services.leaderboard import LeaderboardService
from app.config import settings

router = APIRouter(prefix="/teachers", tags=["Teachers"])


# Pydantic Schemas
class TeacherSignup(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    employee_id: Optional[str] = None
    gce_board_id: Optional[str] = None
    school_name: str
    school_region: str
    language_stream: LanguageStream
    subjects: List[str]
    class_levels: List[str]
    email: str
    phone: str
    password: str = Field(..., min_length=8)


class TeacherProfileResponse(BaseModel):
    id: str
    full_name: str
    employee_id: Optional[str] = None
    gce_board_id: Optional[str] = None
    school_name: str
    school_region: str
    language_stream: str
    subjects: List[str]
    class_levels: List[str]
    approval_status: str
    is_read_only: bool
    is_approved: bool

    class Config:
        from_attributes = True


class CreateClassRequest(BaseModel):
    subject: str
    class_level: str
    language_stream: LanguageStream
    is_permanent: bool = False
    expires_in_days: int = 7


class ClassResponse(BaseModel):
    id: str
    subject: str
    class_level: str
    class_code: str
    is_permanent: bool
    expires_at: Optional[datetime]
    student_count: int
    has_uploaded_material: bool

    class Config:
        from_attributes = True


class MaterialUpload(BaseModel):
    title: str
    subject: str
    class_level: str
    term: Optional[int] = None
    topic: Optional[str] = None
    is_visible_to_students: bool = False


class MaterialResponse(BaseModel):
    id: str
    title: str
    subject: str
    class_level: str
    term: Optional[int]
    topic: Optional[str]
    is_visible_to_students: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StudentListResponse(BaseModel):
    id: str
    full_name: str
    lumina_id: str
    child_tracking_code: str
    class_level: str
    region: str
    streak_days: int
    last_session: Optional[datetime]


class CreateAssignmentRequest(BaseModel):
    class_id: str
    title: str
    description: Optional[str] = None
    subject: str
    due_date: datetime
    max_score: int = 100
    rubric: Optional[dict] = None


class AssignmentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    subject: str
    due_date: datetime
    max_score: int
    submission_count: int
    graded_count: int

    class Config:
        from_attributes = True


# Routes
@router.post("/register", response_model=TeacherProfileResponse)
async def register_teacher(
    data: TeacherSignup,
    db: Session = Depends(get_db)
):
    """Register a new teacher account (requires admin approval)."""
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        phone=data.phone,
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        user_type=UserType.TEACHER,
        is_active=True
    )
    db.add(user)
    
    # Create teacher profile
    teacher = Teacher(
        id=str(uuid.uuid4()),
        user_id=user.id,
        employee_id=data.employee_id,
        gce_board_id=data.gce_board_id,
        school_name=data.school_name,
        school_region=data.school_region,
        language_stream=data.language_stream,
        approval_status=TeacherApprovalStatus.PENDING,
        is_read_only=True  # Read-only until approved
    )
    db.add(teacher)
    
    # Add subjects
    for subject in data.subjects:
        teacher_subject = TeacherSubject(
            id=str(uuid.uuid4()),
            teacher_id=teacher.id,
            subject=subject,
            class_levels=data.class_levels
        )
        db.add(teacher_subject)
    
    db.commit()
    db.refresh(teacher)
    
    return TeacherProfileResponse(
        id=teacher.id,
        full_name=user.full_name,
        employee_id=teacher.employee_id,
        gce_board_id=teacher.gce_board_id,
        school_name=teacher.school_name,
        school_region=teacher.school_region,
        language_stream=teacher.language_stream.value,
        subjects=data.subjects,
        class_levels=data.class_levels,
        approval_status=teacher.approval_status.value,
        is_read_only=teacher.is_read_only,
        is_approved=False
    )


@router.get("/profile", response_model=TeacherProfileResponse)
async def get_teacher_profile(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get current teacher's profile."""
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    subjects = [ts.subject for ts in teacher.teacher_subjects]
    class_levels = []
    for ts in teacher.teacher_subjects:
        class_levels.extend(ts.class_levels or [])
    class_levels = list(set(class_levels))
    
    return TeacherProfileResponse(
        id=teacher.id,
        full_name=current_user.full_name,
        employee_id=teacher.employee_id,
        gce_board_id=teacher.gce_board_id,
        school_name=teacher.school_name,
        school_region=teacher.school_region,
        language_stream=teacher.language_stream.value,
        subjects=subjects,
        class_levels=class_levels,
        approval_status=teacher.approval_status.value,
        is_read_only=teacher.is_read_only,
        is_approved=teacher.approval_status == TeacherApprovalStatus.APPROVED
    )


@router.post("/classes", response_model=ClassResponse)
async def create_class(
    data: CreateClassRequest,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new class with join code."""
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    if teacher.is_read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not yet approved. Uploaded content is read-only."
        )
    
    # Generate unique class code
    class_code = generate_class_code(data.subject, datetime.utcnow().year)
    
    # Ensure unique code
    while db.query(Class).filter(Class.class_code == class_code).first():
        class_code = generate_class_code(data.subject, datetime.utcnow().year)
    
    expires_at = None
    if not data.is_permanent:
        expires_at = datetime.utcnow() + timedelta(days=data.expires_in_days)
    
    class_ = Class(
        id=str(uuid.uuid4()),
        teacher_id=teacher.id,
        subject=data.subject,
        class_level=data.class_level,
        language_stream=data.language_stream,
        class_code=class_code,
        is_permanent=data.is_permanent,
        expires_at=expires_at,
        is_active=True
    )
    db.add(class_)
    db.commit()
    db.refresh(class_)
    
    return ClassResponse(
        id=class_.id,
        subject=class_.subject,
        class_level=class_.class_level,
        class_code=class_.class_code,
        is_permanent=class_.is_permanent,
        expires_at=class_.expires_at,
        student_count=0,
        has_uploaded_material=False
    )


@router.get("/classes", response_model=List[ClassResponse])
async def get_teacher_classes(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all classes for current teacher."""
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    classes = db.query(Class).filter(Class.teacher_id == teacher.id).all()
    
    result = []
    for class_ in classes:
        student_count = db.query(StudentEnrollment).filter(
            StudentEnrollment.class_id == class_.id,
            StudentEnrollment.is_active == True
        ).count()
        
        has_material = db.query(Material).filter(
            Material.class_id == class_.id
        ).first() is not None
        
        result.append(ClassResponse(
            id=class_.id,
            subject=class_.subject,
            class_level=class_.class_level,
            class_code=class_.class_code,
            is_permanent=class_.is_permanent,
            expires_at=class_.expires_at,
            student_count=student_count,
            has_uploaded_material=has_material
        ))
    
    return result


@router.get("/classes/{class_id}/students", response_model=List[StudentListResponse])
async def get_class_students(
    class_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all students enrolled in a class."""
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Verify teacher owns this class
    class_ = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher.id
    ).first()
    
    if not class_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    enrollments = db.query(StudentEnrollment).filter(
        StudentEnrollment.class_id == class_id,
        StudentEnrollment.is_active == True
    ).all()
    
    result = []
    for enrollment in enrollments:
        student = db.query(Student).filter(Student.id == enrollment.student_id).first()
        if student:
            user = db.query(User).filter(User.id == student.user_id).first()
            result.append(StudentListResponse(
                id=student.id,
                full_name=user.full_name if user else "Unknown",
                lumina_id=student.lumina_id,
                child_tracking_code=student.child_tracking_code,
                class_level=student.class_level,
                region=student.region,
                streak_days=student.streak_days,
                last_session=student.last_session_at
            ))
    
    return result


@router.post("/classes/{class_id}/upload-material", response_model=MaterialResponse)
async def upload_material(
    class_id: str,
    file: UploadFile = File(...),
    title: str = "",
    subject: str = "",
    class_level: str = "",
    term: Optional[int] = None,
    topic: Optional[str] = None,
    is_visible_to_students: bool = False,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Upload curriculum material to a class."""
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Verify teacher owns this class
    class_ = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher.id
    ).first()
    
    if not class_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(class_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{file_id}{ext}")
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Create material record
    material = Material(
        id=str(uuid.uuid4()),
        class_id=class_id,
        teacher_id=teacher.id,
        title=title or file.filename,
        file_path=file_path,
        file_type=ext,
        subject=subject or class_.subject,
        class_level=class_level or class_.class_level,
        term=term,
        topic=topic,
        is_visible_to_students=is_visible_to_students,
        for_lumina_internal_use=True
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    
    return MaterialResponse(
        id=material.id,
        title=material.title,
        subject=material.subject,
        class_level=material.class_level,
        term=material.term,
        topic=material.topic,
        is_visible_to_students=material.is_visible_to_students,
        created_at=material.created_at
    )


@router.get("/classes/{class_id}/materials", response_model=List[MaterialResponse])
async def get_class_materials(
    class_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all materials uploaded to a class."""
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Verify teacher owns this class
    class_ = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher.id
    ).first()
    
    if not class_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    materials = db.query(Material).filter(
        Material.class_id == class_id
    ).all()
    
    return [MaterialResponse(
        id=m.id,
        title=m.title,
        subject=m.subject,
        class_level=m.class_level,
        term=m.term,
        topic=m.topic,
        is_visible_to_students=m.is_visible_to_students,
        created_at=m.created_at
    ) for m in materials]


@router.post("/assignments", response_model=AssignmentResponse)
async def create_assignment(
    data: CreateAssignmentRequest,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new assignment for a class."""
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    if teacher.is_read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not yet approved"
        )
    
    # Verify teacher owns this class
    class_ = db.query(Class).filter(
        Class.id == data.class_id,
        Class.teacher_id == teacher.id
    ).first()
    
    if not class_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    assignment = Assignment(
        id=str(uuid.uuid4()),
        class_id=data.class_id,
        teacher_id=teacher.id,
        title=data.title,
        description=data.description,
        subject=data.subject,
        due_date=data.due_date,
        max_score=data.max_score,
        rubric=data.rubric
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    submission_count = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment.id
    ).count()
    
    graded_count = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment.id,
        AssignmentSubmission.score.isnot(None)
    ).count()
    
    return AssignmentResponse(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        subject=assignment.subject,
        due_date=assignment.due_date,
        max_score=assignment.max_score,
        submission_count=submission_count,
        graded_count=graded_count
    )


@router.get("/assignments", response_model=List[AssignmentResponse])
async def get_teacher_assignments(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all assignments created by teacher."""
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    assignments = db.query(Assignment).filter(
        Assignment.teacher_id == teacher.id
    ).all()
    
    result = []
    for assignment in assignments:
        submission_count = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == assignment.id
        ).count()
        
        graded_count = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == assignment.id,
            AssignmentSubmission.score.isnot(None)
        ).count()
        
        result.append(AssignmentResponse(
            id=assignment.id,
            title=assignment.title,
            description=assignment.description,
            subject=assignment.subject,
            due_date=assignment.due_date,
            max_score=assignment.max_score,
            submission_count=submission_count,
            graded_count=graded_count
        ))
    
    return result


@router.post("/students/{student_id}/flag")
async def flag_student(
    student_id: str,
    flag_type: str,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Flag a student for parent notification or risk."""
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Verify teacher has this student in a class
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    flag = StudentFlag(
        id=str(uuid.uuid4()),
        student_id=student_id,
        teacher_id=teacher.id,
        flag_type=flag_type,
        reason=reason
    )
    db.add(flag)
    db.commit()
    
    return {"message": "Student flagged successfully", "flag_id": flag.id}


@router.get("/dashboard/summary")
async def get_teacher_dashboard(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get teacher dashboard summary."""
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Get class stats
    classes = db.query(Class).filter(Class.teacher_id == teacher.id).all()
    
    total_students = 0
    classes_needing_material = 0
    
    for class_ in classes:
        student_count = db.query(StudentEnrollment).filter(
            StudentEnrollment.class_id == class_.id,
            StudentEnrollment.is_active == True
        ).count()
        total_students += student_count
        
        has_material = db.query(Material).filter(
            Material.class_id == class_.id
        ).first() is not None
        
        if not has_material:
            classes_needing_material += 1
    
    # Get pending flags
    pending_flags = db.query(StudentFlag).filter(
        StudentFlag.teacher_id == teacher.id,
        StudentFlag.is_resolved == False
    ).count()
    
    return {
        "approval_status": teacher.approval_status.value,
        "is_read_only": teacher.is_read_only,
        "total_classes": len(classes),
        "total_students": total_students,
        "classes_needing_material": classes_needing_material,
        "pending_flags": pending_flags,
        "message": (
            "You still have subjects without uploaded material for some of your classes. "
            "Uploading your notes or syllabus will help Lumina teach your students more accurately."
            if classes_needing_material > 0 else
            "Your classes are well-equipped with materials!"
        )
    }
