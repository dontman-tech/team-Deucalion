from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional
import uuid

from app.database import get_db
from app.models import (
    User, Student, UserType, LanguageStream,
    Class, StudentEnrollment, Teacher,
    generate_lumina_id, generate_ctc,
    REGION_CODES
)
from app.services.auth import get_current_student
from app.services.leaderboard import LeaderboardService
from app.config import settings

router = APIRouter(prefix="/students", tags=["Students"])


# Pydantic Schemas
class StudentSignup(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date
    gender: str = Field(..., pattern="^(male|female|other)$")
    school_name: Optional[str] = None
    region: str
    language_stream: LanguageStream
    class_level: str
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class StudentProfileResponse(BaseModel):
    id: str
    lumina_id: str
    child_tracking_code: str
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    school_name: Optional[str] = None
    region: str
    language_stream: str
    class_level: str
    streak_days: int
    performance_level: str
    learning_style: str
    is_content_locked: bool
    content_unlock_override: bool
    created_at: datetime

    class Config:
        from_attributes = True


class JoinClassRequest(BaseModel):
    class_code: str


class ClassCodeResponse(BaseModel):
    id: str
    subject: str
    class_level: str
    teacher_name: str
    enrolled_at: datetime


# Routes
@router.post("/register", response_model=StudentProfileResponse)
async def register_student(
    data: StudentSignup,
    db: Session = Depends(get_db)
):
    """Register a new student account."""
    
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == data.username) | (User.email == f"{data.username}@lumina.cm")
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Validate region
    if data.region not in REGION_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region. Must be one of: {list(REGION_CODES.keys())}"
        )
    
    # Generate unique IDs
    region_code = REGION_CODES[data.region]
    lumina_id = generate_lumina_id(region_code)
    ctc = generate_ctc()
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        username=data.username,
        email=f"{data.username}@lumina.cm",
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        user_type=UserType.STUDENT,
        is_active=True
    )
    db.add(user)
    
    # Create student profile
    student = Student(
        id=str(uuid.uuid4()),
        user_id=user.id,
        lumina_id=lumina_id,
        child_tracking_code=ctc,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        school_name=data.school_name,
        region=data.region,
        language_stream=data.language_stream,
        class_level=data.class_level,
        is_content_locked=True,
        performance_level="average",
        learning_style="visual"
    )
    db.add(student)
    
    db.commit()
    db.refresh(student)
    
    return StudentProfileResponse(
        id=student.id,
        lumina_id=student.lumina_id,
        child_tracking_code=student.child_tracking_code,
        full_name=user.full_name,
        date_of_birth=student.date_of_birth,
        gender=student.gender,
        school_name=student.school_name,
        region=student.region,
        language_stream=student.language_stream.value,
        class_level=student.class_level,
        streak_days=student.streak_days,
        performance_level=student.performance_level,
        learning_style=student.learning_style,
        is_content_locked=student.is_content_locked,
        content_unlock_override=student.content_unlock_override,
        created_at=student.created_at
    )


@router.get("/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get current student's profile."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    return StudentProfileResponse(
        id=student.id,
        lumina_id=student.lumina_id,
        child_tracking_code=student.child_tracking_code,
        full_name=current_user.full_name,
        date_of_birth=student.date_of_birth,
        gender=student.gender,
        school_name=student.school_name,
        region=student.region,
        language_stream=student.language_stream.value,
        class_level=student.class_level,
        streak_days=student.streak_days,
        performance_level=student.performance_level,
        learning_style=student.learning_style,
        is_content_locked=student.is_content_locked,
        content_unlock_override=student.content_unlock_override,
        created_at=student.created_at
    )


@router.post("/join-class", response_model=ClassCodeResponse)
async def join_class(
    data: JoinClassRequest,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Join a class using class code."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Find class by code
    class_ = db.query(Class).filter(
        Class.class_code == data.class_code,
        Class.is_active == True
    ).first()
    
    if not class_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or code expired"
        )
    
    # Check if class is expired
    if class_.expires_at and class_.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class code has expired"
        )
    
    # Check if already enrolled
    existing = db.query(StudentEnrollment).filter(
        StudentEnrollment.student_id == student.id,
        StudentEnrollment.class_id == class_.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this class"
        )
    
    # Enroll student
    enrollment = StudentEnrollment(
        id=str(uuid.uuid4()),
        student_id=student.id,
        class_id=class_.id,
        is_active=True
    )
    db.add(enrollment)
    db.commit()
    
    # Award participation points
    LeaderboardService.award_participation_points(
        db, student, "join_class", class_.id
    )
    
    # Get teacher name
    teacher = db.query(Teacher).filter(Teacher.id == class_.teacher_id).first()
    teacher_name = teacher.user.full_name if teacher and teacher.user else "Unknown Teacher"
    
    return ClassCodeResponse(
        id=class_.id,
        subject=class_.subject,
        class_level=class_.class_level,
        teacher_name=teacher_name,
        enrolled_at=enrollment.enrolled_at
    )


@router.get("/classes", response_model=List[ClassCodeResponse])
async def get_enrolled_classes(
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get all classes the student is enrolled in."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    enrollments = db.query(StudentEnrollment).filter(
        StudentEnrollment.student_id == student.id,
        StudentEnrollment.is_active == True
    ).all()
    
    result = []
    for enrollment in enrollments:
        class_ = db.query(Class).filter(Class.id == enrollment.class_id).first()
        if class_:
            teacher = db.query(Teacher).filter(Teacher.id == class_.teacher_id).first()
            teacher_name = teacher.user.full_name if teacher and teacher.user else "Unknown Teacher"
            
            result.append(ClassCodeResponse(
                id=class_.id,
                subject=class_.subject,
                class_level=class_.class_level,
                teacher_name=teacher_name,
                enrolled_at=enrollment.enrolled_at
            ))
    
    return result


@router.get("/leaderboard/summary")
async def get_leaderboard_summary(
    class_id: Optional[str] = None,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get student's leaderboard summary."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    return LeaderboardService.get_student_summary(db, student, class_id)


@router.get("/leaderboard/class/{class_id}")
async def get_class_leaderboard(
    class_id: str,
    category: Optional[str] = None,
    is_all_time: bool = False,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get class leaderboard."""
    return LeaderboardService.get_class_leaderboard(
        db, class_id, category, is_all_time
    )


@router.put("/profile/preferences")
async def update_preferences(
    learning_style: Optional[str] = None,
    performance_level: Optional[str] = None,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Update student preferences."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    if learning_style:
        student.learning_style = learning_style
    if performance_level:
        student.performance_level = performance_level
    
    db.commit()
    
    return {"message": "Preferences updated successfully"}
