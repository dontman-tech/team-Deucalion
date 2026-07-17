from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid

from app.database import get_db
from app.models import (
    User, Student, AISession, AIMessage, Material,
    Class, LanguageStream, StudentEnrollment
)
from app.services.auth import get_current_student, get_current_user, get_current_teacher
from app.services.lumina import LuminaService
from app.services.deepseek import get_deepseek_service
from app.services.leaderboard import LeaderboardService

router = APIRouter(prefix="/ai", tags=["AI Sessions"])


# Pydantic Schemas
class StartSessionRequest(BaseModel):
    subject: str
    class_id: Optional[str] = None
    mentor_mode: str = "guide"  # guide, explain, quiz, writing_coach, debate, explore
    current_topic: Optional[str] = None


class ChatMessage(BaseModel):
    content: str


class SessionResponse(BaseModel):
    id: str
    subject: str
    mentor_mode: str
    current_topic: Optional[str]
    started_at: datetime
    duration_minutes: int


class ChatResponse(BaseModel):
    response: str
    mode: str
    suggestions: Optional[List[str]] = None
    switch_to_explain: Optional[bool] = None
    error: Optional[str] = None


# Routes
@router.post("/sessions/start", response_model=SessionResponse)
async def start_session(
    data: StartSessionRequest,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Start a new AI tutoring session."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Get teacher material if class specified
    teacher_material = []
    teacher_context = None
    if data.class_id:
        materials = db.query(Material).filter(
            Material.class_id == data.class_id,
            Material.for_lumina_internal_use == True
        ).all()
        teacher_material = materials
        if materials:
            teacher_context = "\n".join([
                f"- {m.title} ({m.subject}, {m.class_level})"
                for m in materials
            ])
    
    # Count existing sessions for session number
    session_count = db.query(AISession).filter(
        AISession.student_id == student.id
    ).count()
    
    # Check if exam season
    now = datetime.utcnow()
    is_exam_season = now.month in [3, 4, 5, 6]
    
    session = AISession(
        id=str(uuid.uuid4()),
        student_id=student.id,
        class_id=data.class_id,
        mentor_mode=data.mentor_mode,
        subject=data.subject,
        current_topic=data.current_topic,
        session_number=session_count + 1,
        is_exam_prep_active=is_exam_season
    )
    db.add(session)
    
    # Update student's last session
    student.last_session_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    
    # Award participation points for starting session
    LeaderboardService.award_participation_points(
        db, student, "ai_study_session_15min"
    )
    
    return SessionResponse(
        id=session.id,
        subject=session.subject,
        mentor_mode=session.mentor_mode,
        current_topic=session.current_topic,
        started_at=session.created_at,
        duration_minutes=0
    )


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def send_message(
    session_id: str,
    message: ChatMessage,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Send a message to Lumina AI powered by DeepSeek."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    session = db.query(AISession).filter(
        AISession.id == session_id,
        AISession.student_id == student.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Save user message
    user_message = AIMessage(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="user",
        content=message.content,
        mentor_mode=session.mentor_mode
    )
    db.add(user_message)
    
    # Get chat history
    chat_history = db.query(AIMessage).filter(
        AIMessage.session_id == session.id
    ).order_by(AIMessage.created_at).all()
    history_dict = [
        {"role": msg.role, "content": msg.content}
        for msg in chat_history[:-1]  # Exclude the message just added
    ]
    
    # Get teacher material context
    teacher_context = None
    if session.class_id:
        materials = db.query(Material).filter(
            Material.class_id == session.class_id,
            Material.for_lumina_internal_use == True
        ).all()
        if materials:
            teacher_context = "\n".join([
                f"- {m.title} ({m.subject}, {m.class_level})"
                for m in materials
            ])
            session.content_source = "teacher_upload"
            session.content_document_title = materials[0].title if materials else None
    
    # Initialize Lumina service for emotional detection
    lumina = LuminaService(student, session, [])
    
    # Detect emotional state
    emotional_state = lumina.detect_emotional_state(message.content)
    if emotional_state != "neutral":
        session.emotional_state = emotional_state
    
    # Try to use DeepSeek API
    try:
        deepseek = get_deepseek_service()
        
        result = deepseek.chat(
            message=message.content,
            student_name=current_user.full_name,
            class_level=student.class_level,
            language_stream=student.language_stream.value,
            mentor_mode=session.mentor_mode,
            subject=session.subject,
            current_topic=session.current_topic,
            chat_history=history_dict,
            teacher_material_context=teacher_context,
            is_exam_season=session.is_exam_prep_active
        )
        
        if result["success"]:
            response_text = result["response"]
        else:
            # Fallback to LuminaService if API fails
            response_text = _get_fallback_response(session, message.content, lumina)
            
    except Exception as e:
        # Fallback to LuminaService if DeepSeek not available
        response_text = _get_fallback_response(session, message.content, lumina)
    
    # Generate emotional response if needed
    if emotional_state != "neutral":
        emotional_response = lumina.generate_emotional_response(emotional_state)
        response_text = f"{emotional_response}\n\n{response_text}"
    
    # Save AI response
    ai_message = AIMessage(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="assistant",
        content=response_text,
        mentor_mode=session.mentor_mode
    )
    db.add(ai_message)
    
    db.commit()
    
    return ChatResponse(
        response=response_text,
        mode=session.mentor_mode,
        suggestions=None,
        switch_to_explain=False
    )


def _get_fallback_response(session: AISession, message: str, lumina: LuminaService) -> str:
    """Fallback response when DeepSeek API is unavailable."""
    if session.mentor_mode == LuminaService.GUIDE:
        guide_result = lumina.guide_mode(message)
        return guide_result["response"]
    elif session.mentor_mode == LuminaService.EXPLAIN:
        explain_result = lumina.explain_mode(session.current_topic or "the topic")
        return "\n\n".join(explain_result["methods"])
    elif session.mentor_mode == LuminaService.QUIZ:
        quiz_result = lumina.quiz_mode(session.current_topic)
        return f"Quiz mode for {quiz_result['topic']}. Difficulty: {quiz_result['difficulty']}"
    elif session.mentor_mode == LuminaService.WRITING_COACH:
        coach_result = lumina.writing_coach_mode()
        return f"**{coach_result['title']}**\n\n{coach_result['instruction']}"
    elif session.mentor_mode == LuminaService.EXPLORE:
        explore_result = lumina.explore_mode(session.current_topic or "general")
        return f"**Hook:** {explore_result['hook']}\n\nExplore: {explore_result['three_directions'][0]}"
    else:
        return "I'm here to help you learn! What would you like to explore today?"


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """End an AI tutoring session."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    session = db.query(AISession).filter(
        AISession.id == session_id,
        AISession.student_id == student.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Calculate duration
    if session.ended_at is None:
        session.ended_at = datetime.utcnow()
        duration = (session.ended_at - session.created_at).total_seconds() / 60
        session.duration_minutes = int(duration)
    
    # Update student streak
    if session.duration_minutes >= 15:
        student.last_session_at = datetime.utcnow()
        student.streak_days += 1
    
    # Award leaderboard points
    LeaderboardService.award_participation_points(
        db, student, "ai_study_session_15min"
    )
    session.leaderboard_points = 5  # Base points
    
    # Generate session log
    lumina = LuminaService(student, session)
    session_log = lumina.generate_session_log()
    
    db.commit()
    
    return {
        "message": "Session ended successfully",
        "duration_minutes": session.duration_minutes,
        "points_earned": session.leaderboard_points,
        "session_log": session_log
    }


@router.get("/sessions/history")
async def get_session_history(
    limit: int = 20,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get history of AI sessions."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    sessions = db.query(AISession).filter(
        AISession.student_id == student.id
    ).order_by(AISession.created_at.desc()).limit(limit).all()
    
    return {
        "sessions": [
            {
                "id": s.id,
                "subject": s.subject,
                "mentor_mode": s.mentor_mode,
                "current_topic": s.current_topic,
                "duration_minutes": s.duration_minutes,
                "concepts_mastered": s.concepts_mastered or [],
                "concepts_struggling": s.concepts_struggling or [],
                "created_at": s.created_at.isoformat(),
                "content_source": s.content_source
            }
            for s in sessions
        ]
    }


@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get detailed session information."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    session = db.query(AISession).filter(
        AISession.id == session_id,
        AISession.student_id == student.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Get messages
    messages = db.query(AIMessage).filter(
        AIMessage.session_id == session.id
    ).order_by(AIMessage.created_at).all()
    
    return {
        "session": {
            "id": session.id,
            "subject": session.subject,
            "mentor_mode": session.mentor_mode,
            "current_topic": session.current_topic,
            "duration_minutes": session.duration_minutes,
            "concepts_mastered": session.concepts_mastered or [],
            "concepts_struggling": session.concepts_struggling or [],
            "emotional_state": session.emotional_state,
            "content_source": session.content_source,
            "content_document_title": session.content_document_title,
            "created_at": session.created_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None
        },
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }


@router.post("/sessions/{session_id}/switch-mode")
async def switch_mentor_mode(
    session_id: str,
    new_mode: str,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Switch the mentor mode for an active session."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    session = db.query(AISession).filter(
        AISession.id == session_id,
        AISession.student_id == student.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    valid_modes = ["guide", "explain", "quiz", "writing_coach", "debate", "explore"]
    if new_mode not in valid_modes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode. Must be one of: {valid_modes}"
        )
    
    session.mentor_mode = new_mode
    db.commit()
    
    return {
        "message": f"Switched to {new_mode} mode",
        "new_mode": new_mode
    }


@router.post("/sessions/{session_id}/safety-flag")
async def flag_safety_concern(
    session_id: str,
    concern_type: str,
    details: str = None,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Flag a safety concern during session."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    session = db.query(AISession).filter(
        AISession.id == session_id,
        AISession.student_id == student.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    session.safety_flag = True
    session.safety_note = f"Type: {concern_type}. Details: {details}"
    db.commit()
    
    return {
        "message": "Safety concern flagged. A teacher will be notified.",
        "resources": {
            "sos_cameroun": "+237 222 22 11 11",
            "message": "If you are in immediate danger, please contact emergency services."
        }
    }


# DeepSeek-powered generation endpoints
class GenerateQuizRequest(BaseModel):
    topic: str
    subject: str
    num_questions: int = 5
    difficulty: str = "medium"


class GenerateLessonPlanRequest(BaseModel):
    topic: str
    subject: str
    duration_minutes: int = 60


class GenerateAssignmentRequest(BaseModel):
    topic: str
    subject: str
    assignment_type: str = "general"


@router.post("/generate/quiz")
async def generate_quiz(
    data: GenerateQuizRequest,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Generate quiz questions using DeepSeek AI."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    try:
        deepseek = get_deepseek_service()
        result = deepseek.generate_quiz_questions(
            topic=data.topic,
            subject=data.subject,
            class_level=student.class_level,
            language_stream=student.language_stream.value,
            num_questions=data.num_questions,
            difficulty=data.difficulty
        )
        
        if result["success"]:
            return {
                "success": True,
                "questions": result["questions"],
                "topic": data.topic,
                "subject": data.subject,
                "class_level": student.class_level
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate quiz")
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI service unavailable: {str(e)}"
        }


@router.post("/generate/assignment")
async def generate_assignment(
    data: GenerateAssignmentRequest,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Generate an assignment using DeepSeek AI."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    try:
        deepseek = get_deepseek_service()
        result = deepseek.generate_assignment(
            topic=data.topic,
            subject=data.subject,
            class_level=student.class_level,
            language_stream=student.language_stream.value,
            assignment_type=data.assignment_type
        )
        
        if result["success"]:
            return {
                "success": True,
                "assignment": result["assignment"],
                "topic": data.topic,
                "subject": data.subject
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate assignment")
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI service unavailable: {str(e)}"
        }


@router.post("/generate/lesson-plan")
async def generate_lesson_plan(
    data: GenerateLessonPlanRequest,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Generate a lesson plan using DeepSeek AI (for teachers)."""
    from app.models import Teacher
    
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    try:
        deepseek = get_deepseek_service()
        result = deepseek.generate_lesson_plan(
            topic=data.topic,
            subject=data.subject,
            class_level=data.subject,  # This should come from request in real implementation
            language_stream=teacher.language_stream.value,
            duration_minutes=data.duration_minutes
        )
        
        if result["success"]:
            return {
                "success": True,
                "lesson_plan": result["lesson_plan"],
                "topic": data.topic,
                "subject": data.subject
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate lesson plan")
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI service unavailable: {str(e)}"
        }
