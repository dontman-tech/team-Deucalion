from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid

from app.database import get_db
from app.models import (
    User, Parent, Student, UserType, StudentEnrollment,
    Class, AISession, AssignmentSubmission, QuizAttempt,
    LeaderboardEntry, LanguageStream
)
from app.services.auth import get_current_parent, get_current_user, get_password_hash
from app.services.leaderboard import LeaderboardService
from app.config import settings

router = APIRouter(prefix="/parents", tags=["Parents"])


# Pydantic Schemas
class ParentSignup(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str
    email: str
    password: str = Field(..., min_length=8)
    child_tracking_code: Optional[str] = Field(None, description="Child Tracking Code to link (optional)")


class ChildCardResponse(BaseModel):
    id: str
    full_name: str
    class_level: str
    language_stream: str
    school_name: Optional[str]
    region: str
    is_active_recently: bool


class ChildDashboardResponse(BaseModel):
    child_id: str
    child_name: str
    class_level: str
    stream: str
    study_time_this_week: int
    topics_covered: List[str]
    assignments_submitted: int
    assignments_total: int
    ai_sessions_this_week: int
    current_class_rank: int
    current_streak: int
    subject_performance: List[dict]
    ai_summary: str
    recommended_action: str
    upcoming_deadlines: List[dict]


class SubjectPerformance(BaseModel):
    subject: str
    percentage: float
    status: str  # excellent, good, average, needs_improvement


# Routes
@router.post("/register")
async def register_parent(
    data: ParentSignup,
    db: Session = Depends(get_db)
):
    """Register a new parent account. Child Tracking Code is optional."""
    
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
        user_type=UserType.PARENT,
        is_active=True
    )
    db.add(user)
    
    # Create parent profile
    parent = Parent(
        id=str(uuid.uuid4()),
        user_id=user.id
    )
    db.add(parent)
    
    linked_children = []
    
    # Link to child if CTC provided
    if data.child_tracking_code:
        student = db.query(Student).filter(
            Student.child_tracking_code == data.child_tracking_code
        ).first()
        
        if not student:
            # Rollback user creation
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid Child Tracking Code. Please check and try again."
            )
        
        # Check if maximum parents already linked
        from app.models import parent_student_links
        from sqlalchemy import func
        
        parent_count = db.query(func.count(parent_student_links.c.parent_id)).filter(
            parent_student_links.c.student_id == student.id
        ).scalar()
        
        if parent_count >= settings.MAX_PARENTS_PER_STUDENT:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This student account already has the maximum number of parent accounts linked. "
                       "Please contact the school administrator if you believe this is an error."
            )
        
        # Link to child
        parent.children.append(student)
        linked_children.append(student.child_tracking_code)
    
    db.commit()
    
    return {
        "message": "Parent account created successfully",
        "parent_id": parent.id,
        "linked_children": linked_children
    }


@router.get("/dashboard")
async def get_parent_dashboard(
    current_user: User = Depends(get_current_parent),
    db: Session = Depends(get_db)
):
    """Get parent dashboard with overview of all linked children."""
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    children = parent.children
    child_cards = []
    
    for child in children:
        user = db.query(User).filter(User.id == child.user_id).first()
        
        # Check if active recently (within 7 days)
        is_active = False
        if child.last_session_at:
            days_since = (datetime.utcnow() - child.last_session_at).days
            is_active = days_since <= 7
        
        child_cards.append(ChildCardResponse(
            id=child.id,
            full_name=user.full_name if user else "Unknown",
            class_level=child.class_level,
            language_stream=child.language_stream.value,
            school_name=child.school_name,
            region=child.region,
            is_active_recently=is_active
        ))
    
    return {
        "parent_name": current_user.full_name,
        "linked_children_count": len(children),
        "children": child_cards
    }


@router.get("/children/{child_id}/dashboard", response_model=ChildDashboardResponse)
async def get_child_dashboard(
    child_id: str,
    current_user: User = Depends(get_current_parent),
    db: Session = Depends(get_db)
):
    """Get detailed dashboard for a specific child."""
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    # Verify parent has access to this child
    if child_id not in [c.id for c in parent.children]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this child's data"
        )
    
    student = db.query(Student).filter(Student.id == child_id).first()
    user = db.query(User).filter(User.id == student.user_id).first()
    
    # Get enrollments
    enrollments = db.query(StudentEnrollment).filter(
        StudentEnrollment.student_id == student.id,
        StudentEnrollment.is_active == True
    ).all()
    
    class_ids = [e.class_id for e in enrollments]
    
    # Calculate study time this week
    week_ago = datetime.utcnow() - datetime.timedelta(days=7)
    sessions = db.query(AISession).filter(
        AISession.student_id == student.id,
        AISession.created_at >= week_ago
    ).all()
    
    total_study_minutes = sum(s.duration_minutes for s in sessions)
    
    # Get topics covered
    topics_covered = list(set(
        s.current_topic for s in sessions 
        if s.current_topic
    ))
    
    # Get assignments
    if class_ids:
        assignments_submitted = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.student_id == student.id
        ).count()
        
        from app.models import Assignment
        total_assignments = db.query(Assignment).filter(
            Assignment.class_id.in_(class_ids)
        ).count()
    else:
        assignments_submitted = 0
        total_assignments = 0
    
    # AI sessions count
    ai_sessions_count = len(sessions)
    
    # Current streak
    current_streak = student.streak_days
    
    # Subject performance (simulated - would need real grade data)
    subject_performance = [
        SubjectPerformance(
            subject="Mathematics",
            percentage=75.0,
            status="good"
        ),
        SubjectPerformance(
            subject="English Language",
            percentage=82.0,
            status="excellent"
        ),
        SubjectPerformance(
            subject="Science",
            percentage=68.0,
            status="average"
        )
    ]
    
    # Calculate class rank
    if class_ids:
        student_leaderboard = db.query(LeaderboardEntry).filter(
            LeaderboardEntry.student_id == student.id,
            LeaderboardEntry.class_id.in_(class_ids)
        ).first()
        current_rank = student_leaderboard.rank if student_leaderboard else 0
    else:
        current_rank = 0
    
    # Generate AI summary
    ai_summary = (
        f"{user.full_name if user else 'Your child'} is making good progress in their studies. "
        f"They have maintained a {current_streak}-day study streak. "
        f"Mathematics shows steady improvement with recent quiz scores averaging 75%. "
        f"English Language performance is excellent at 82%. "
        f"Science topics related to ecosystems need some review."
    )
    
    recommended_action = (
        "Consider reviewing the ecosystem topic with your child using "
        "real-world Cameroonian examples, such as the forest ecosystems in the South Region."
    )
    
    # Upcoming deadlines
    from app.models import Assignment
    upcoming_deadlines = []
    if class_ids:
        now = datetime.utcnow()
        upcoming = db.query(Assignment).filter(
            Assignment.class_id.in_(class_ids),
            Assignment.due_date > now
        ).order_by(Assignment.due_date).limit(5).all()
        
        for a in upcoming:
            upcoming_deadlines.append({
                "title": a.title,
                "subject": a.subject,
                "due_date": a.due_date.isoformat(),
                "class_level": student.class_level
            })
    
    return ChildDashboardResponse(
        child_id=student.id,
        child_name=user.full_name if user else "Unknown",
        class_level=student.class_level,
        stream=student.language_stream.value,
        study_time_this_week=total_study_minutes,
        topics_covered=topics_covered[:5],  # Limit to 5
        assignments_submitted=assignments_submitted,
        assignments_total=total_assignments,
        ai_sessions_this_week=ai_sessions_count,
        current_class_rank=current_rank,
        current_streak=current_streak,
        subject_performance=subject_performance,
        ai_summary=ai_summary,
        recommended_action=recommended_action,
        upcoming_deadlines=upcoming_deadlines
    )


@router.post("/children/add")
async def add_child(
    child_tracking_code: str,
    current_user: User = Depends(get_current_parent),
    db: Session = Depends(get_db)
):
    """Add another child to parent's dashboard."""
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    # Validate Child Tracking Code
    student = db.query(Student).filter(
        Student.child_tracking_code == child_tracking_code
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid Child Tracking Code. Please check and try again."
        )
    
    # Check if already linked
    if student in parent.children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This child is already linked to your account"
        )
    
    # Check if maximum parents already linked
    from sqlalchemy import func
    from app.models import parent_student_links
    
    parent_count = db.query(func.count(parent_student_links.c.parent_id)).filter(
        parent_student_links.c.student_id == student.id
    ).scalar()
    
    if parent_count >= settings.MAX_PARENTS_PER_STUDENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This student account already has the maximum number of parent accounts linked. "
                   "Please contact the school administrator if you believe this is an error."
        )
    
    # Link child
    parent.children.append(student)
    db.commit()
    
    user = db.query(User).filter(User.id == student.user_id).first()
    
    return {
        "message": "Child added successfully",
        "child_name": user.full_name if user else "Unknown",
        "child_id": student.id
    }


@router.get("/children/{child_id}/progress")
async def get_child_progress(
    child_id: str,
    current_user: User = Depends(get_current_parent),
    db: Session = Depends(get_db)
):
    """Get detailed progress data for a child."""
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    if not parent or child_id not in [c.id for c in parent.children]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this child's data"
        )
    
    student = db.query(Student).filter(Student.id == child_id).first()
    
    # Get recent sessions
    week_ago = datetime.utcnow() - datetime.timedelta(days=7)
    sessions = db.query(AISession).filter(
        AISession.student_id == student.id
    ).order_by(AISession.created_at.desc()).limit(10).all()
    
    session_summaries = []
    for session in sessions:
        session_summaries.append({
            "date": session.created_at.isoformat(),
            "subject": session.subject,
            "topic": session.current_topic,
            "duration": session.duration_minutes,
            "concepts_mastered": session.concepts_mastered or [],
            "mentor_mode": session.mentor_mode
        })
    
    return {
        "child_id": child_id,
        "current_streak": student.streak_days,
        "leaderboard_summary": LeaderboardService.get_student_summary(db, student),
        "recent_sessions": session_summaries
    }


@router.get("/children/{child_id}/assignments")
async def get_child_assignments(
    child_id: str,
    current_user: User = Depends(get_current_parent),
    db: Session = Depends(get_db)
):
    """Get assignment progress for a child."""
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    if not parent or child_id not in [c.id for c in parent.children]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this child's data"
        )
    
    student = db.query(Student).filter(Student.id == child_id).first()
    
    # Get enrollments
    enrollments = db.query(StudentEnrollment).filter(
        StudentEnrollment.student_id == student.id,
        StudentEnrollment.is_active == True
    ).all()
    
    class_ids = [e.class_id for e in enrollments]
    
    from app.models import Assignment, AssignmentSubmission
    
    assignments = []
    if class_ids:
        all_assignments = db.query(Assignment).filter(
            Assignment.class_id.in_(class_ids)
        ).order_by(Assignment.due_date.desc()).limit(20).all()
        
        for assignment in all_assignments:
            submission = db.query(AssignmentSubmission).filter(
                AssignmentSubmission.assignment_id == assignment.id,
                AssignmentSubmission.student_id == student.id
            ).first()
            
            assignments.append({
                "title": assignment.title,
                "subject": assignment.subject,
                "due_date": assignment.due_date.isoformat(),
                "max_score": assignment.max_score,
                "submitted": submission is not None,
                "score": submission.score if submission and submission.score else None,
                "feedback": submission.feedback if submission and submission.feedback else None
            })
    
    return {
        "child_id": child_id,
        "assignments": assignments
    }


@router.get("/children/{child_id}/leaderboard")
async def get_child_leaderboard(
    child_id: str,
    class_id: Optional[str] = None,
    current_user: User = Depends(get_current_parent),
    db: Session = Depends(get_db)
):
    """Get leaderboard data for a child."""
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    
    if not parent or child_id not in [c.id for c in parent.children]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this child's data"
        )
    
    student = db.query(Student).filter(Student.id == child_id).first()
    user = db.query(User).filter(User.id == student.user_id).first()
    
    # Get enrollments
    enrollments = db.query(StudentEnrollment).filter(
        StudentEnrollment.student_id == student.id,
        StudentEnrollment.is_active == True
    ).all()
    
    if class_id:
        class_ids = [class_id]
    else:
        class_ids = [e.class_id for e in enrollments]
    
    result = {
        "child_name": user.full_name if user else "Unknown",
        "class_leaderboards": []
    }
    
    for cid in class_ids:
        class_ = db.query(Class).filter(Class.id == cid).first()
        if class_:
            weekly = LeaderboardService.get_class_leaderboard(db, cid, is_all_time=False)
            all_time = LeaderboardService.get_class_leaderboard(db, cid, is_all_time=True)
            
            # Find child's position
            child_weekly = next(
                (e for e in weekly if e["student_id"] == student.id), 
                None
            )
            child_all_time = next(
                (e for e in all_time if e["student_id"] == student.id), 
                None
            )
            
            result["class_leaderboards"].append({
                "class_id": cid,
                "subject": class_.subject,
                "class_level": class_.class_level,
                "weekly_rank": child_weekly["rank"] if child_weekly else None,
                "weekly_points": child_weekly["points"] if child_weekly else 0,
                "all_time_rank": child_all_time["rank"] if child_all_time else None,
                "all_time_points": child_all_time["points"] if child_all_time else 0,
                "badges": child_all_time["badges"] if child_all_time else []
            })
    
    return result
