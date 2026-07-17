from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid

from app.database import get_db
from app.models import (
    User, Student, Teacher, Parent, Class, UserType,
    LanguageStream, School, TeacherApprovalStatus
)
from app.services.auth import get_password_hash
from app.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])


# Pydantic Schemas
class SchoolCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    region: str
    language_stream: str = Field(..., pattern="^(anglophone|francophone)$")
    address: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class SchoolResponse(BaseModel):
    id: str
    name: str
    region: str
    language_stream: str
    address: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    is_active: bool
    created_at: datetime


class TeacherApprovalRequest(BaseModel):
    teacher_id: str
    approved: bool


class AdminLogin(BaseModel):
    username: str
    password: str


# Admin authentication (simple check)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin1234"


def verify_admin(username: str, password: str) -> bool:
    """Verify admin credentials."""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


# Routes
@router.post("/login")
async def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    """Admin login endpoint."""
    if not verify_admin(data.username, data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )
    
    return {
        "message": "Admin login successful",
        "admin_username": data.username,
        "role": "admin"
    }


@router.get("/schools", response_model=List[SchoolResponse])
async def list_schools(
    db: Session = Depends(get_db)
):
    """List all schools registered on the platform."""
    schools = db.query(School).order_by(School.created_at.desc()).all()
    
    return [
        SchoolResponse(
            id=s.id,
            name=s.name,
            region=s.region,
            language_stream=s.language_stream or "anglophone",
            address=s.address,
            contact_email=s.contact_email,
            contact_phone=s.contact_phone,
            is_active=s.is_active,
            created_at=s.created_at
        )
        for s in schools
    ]


@router.post("/schools", response_model=SchoolResponse)
async def create_school(
    data: SchoolCreate,
    db: Session = Depends(get_db)
):
    """Create a new school on the platform."""
    # Check if school name already exists
    existing = db.query(School).filter(School.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School with this name already exists"
        )
    
    school = School(
        id=str(uuid.uuid4()),
        name=data.name,
        region=data.region,
        language_stream=data.language_stream,
        address=data.address,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        is_active=True
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    
    return SchoolResponse(
        id=school.id,
        name=school.name,
        region=school.region,
        language_stream=school.language_stream or "anglophone",
        address=school.address,
        contact_email=school.contact_email,
        contact_phone=school.contact_phone,
        is_active=school.is_active,
        created_at=school.created_at
    )


@router.put("/schools/{school_id}/toggle-active")
async def toggle_school_active(
    school_id: str,
    db: Session = Depends(get_db)
):
    """Toggle school active status."""
    school = db.query(School).filter(School.id == school_id).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    school.is_active = not school.is_active
    db.commit()
    
    return {
        "message": f"School {'activated' if school.is_active else 'deactivated'} successfully",
        "school_id": school_id,
        "is_active": school.is_active
    }


@router.delete("/schools/{school_id}")
async def delete_school(
    school_id: str,
    db: Session = Depends(get_db)
):
    """Delete a school."""
    school = db.query(School).filter(School.id == school_id).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    db.delete(school)
    db.commit()
    
    return {"message": "School deleted successfully"}


@router.get("/pending-teachers")
async def list_pending_teachers(
    db: Session = Depends(get_db)
):
    """List all teachers awaiting approval."""
    teachers = db.query(Teacher).filter(
        Teacher.approval_status == "pending"
    ).all()
    
    result = []
    for teacher in teachers:
        user = db.query(User).filter(User.id == teacher.user_id).first()
        result.append({
            "id": teacher.id,
            "user_id": teacher.user_id,
            "full_name": user.full_name if user else "Unknown",
            "email": user.email if user else "",
            "phone": user.phone if user else "",
            "school_name": teacher.school_name,
            "school_region": teacher.school_region,
            "subjects": teacher.subjects or [],
            "class_levels": teacher.class_levels or [],
            "approval_status": teacher.approval_status,
            "created_at": teacher.created_at.isoformat() if teacher.created_at else None
        })
    
    return result


@router.post("/teachers/{teacher_id}/approve")
async def approve_teacher(
    teacher_id: str,
    db: Session = Depends(get_db)
):
    """Approve a teacher's registration."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    teacher.approval_status = "approved"
    teacher.is_approved = True
    
    # Activate the user account
    user = db.query(User).filter(User.id == teacher.user_id).first()
    if user:
        user.is_active = True
    
    db.commit()
    
    return {
        "message": "Teacher approved successfully",
        "teacher_id": teacher_id
    }


@router.post("/teachers/{teacher_id}/reject")
async def reject_teacher(
    teacher_id: str,
    db: Session = Depends(get_db)
):
    """Reject a teacher's registration."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    teacher.approval_status = "rejected"
    
    db.commit()
    
    return {
        "message": "Teacher rejected",
        "teacher_id": teacher_id
    }


@router.get("/stats")
async def get_platform_stats(
    db: Session = Depends(get_db)
):
    """Get platform statistics."""
    total_students = db.query(Student).count()
    total_teachers = db.query(Teacher).count()
    total_parents = db.query(Parent).count()
    total_schools = db.query(School).count()
    approved_teachers = db.query(Teacher).filter(Teacher.approval_status == TeacherApprovalStatus.APPROVED).count()
    pending_teachers = db.query(Teacher).filter(Teacher.approval_status == TeacherApprovalStatus.PENDING).count()
    
    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "approved_teachers": approved_teachers,
        "pending_teachers": pending_teachers,
        "total_parents": total_parents,
        "total_schools": total_schools
    }
