from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, Float, Table, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
import random
import string

from app.database import Base


class LanguageStream(str, enum.Enum):
    ANGLOPHONE = "anglophone"
    FRANCOPHONE = "francophone"


class TeacherApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UserType(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"


# Association table for teacher-subject-class relationships
teacher_class_subjects = Table(
    'teacher_class_subjects',
    Base.metadata,
    Column('teacher_id', String, ForeignKey('teachers.id')),
    Column('class_id', String, ForeignKey('classes.id')),
    Column('subject', String)
)

# Association table for parent-child tracking
parent_student_links = Table(
    'parent_student_links',
    Base.metadata,
    Column('parent_id', String, ForeignKey('parents.id')),
    Column('student_id', String, ForeignKey('students.id')),
    Column('linked_at', DateTime, default=datetime.utcnow)
)


def generate_lumina_id(region_code: str) -> str:
    """Generate LMN-CM-REGIONCODE-7DIGITS format"""
    digits = ''.join(random.choices(string.digits, k=7))
    return f"LMN-CM-{region_code}-{digits}"


def generate_ctc() -> str:
    """Generate CTC-6ALPHANUMERIC format"""
    chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"CTC-{chars}"


def generate_class_code(subject: str, year: int) -> str:
    """Generate SUBJECTINITIALS-YEAR-5DIGITS format"""
    initials = ''.join(word[0] for word in subject.split() if word[0].isupper() or word[0].islower())
    if len(initials) < 2:
        initials = subject[:2].upper()
    digits = ''.join(random.choices(string.digits, k=5))
    return f"{initials.upper()}-{year}-{digits}"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)
    username = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    user_type = Column(Enum(UserType), nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="user", uselist=False)
    teacher = relationship("Teacher", back_populates="user", uselist=False)
    parent = relationship("Parent", back_populates="user", uselist=False)


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), unique=True)
    lumina_id = Column(String, unique=True, nullable=False)
    child_tracking_code = Column(String, unique=True, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    school_name = Column(String, nullable=True)
    region = Column(String, nullable=False)
    language_stream = Column(Enum(LanguageStream), nullable=False)
    class_level = Column(String, nullable=False)
    is_content_locked = Column(Boolean, default=True)
    content_unlock_override = Column(Boolean, default=False)
    streak_days = Column(Integer, default=0)
    last_session_at = Column(DateTime, nullable=True)
    performance_level = Column(String, default="average")  # low, average, high, gifted
    learning_style = Column(String, default="visual")  # visual, auditory, kinesthetic
    iep_flag = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="student")
    enrollments = relationship("StudentEnrollment", back_populates="student")
    parent_links = relationship("Parent", secondary=parent_student_links, back_populates="children")
    sessions = relationship("AISession", back_populates="student")
    submissions = relationship("AssignmentSubmission", back_populates="student")
    quiz_attempts = relationship("QuizAttempt", back_populates="student")
    leaderboard_entries = relationship("LeaderboardEntry", back_populates="student")


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), unique=True)
    employee_id = Column(String, nullable=True)
    gce_board_id = Column(String, nullable=True)
    school_name = Column(String, nullable=False)
    school_region = Column(String, nullable=False)
    language_stream = Column(Enum(LanguageStream), nullable=False)
    approval_status = Column(Enum(TeacherApprovalStatus), default=TeacherApprovalStatus.PENDING)
    approval_admin_id = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    is_read_only = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="teacher")
    classes = relationship("Class", back_populates="teacher")
    teacher_subjects = relationship("TeacherSubject", back_populates="teacher")
    assignments = relationship("Assignment", back_populates="teacher")
    flags = relationship("StudentFlag", back_populates="teacher")


class TeacherSubject(Base):
    __tablename__ = "teacher_subjects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(String, ForeignKey('teachers.id'))
    subject = Column(String, nullable=False)
    class_levels = Column(JSON, default=list)  # List of class levels teacher teaches
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="teacher_subjects")


class Parent(Base):
    __tablename__ = "parents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="parent")
    children = relationship("Student", secondary=parent_student_links, back_populates="parent_links")


class Class(Base):
    __tablename__ = "classes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(String, ForeignKey('teachers.id'))
    subject = Column(String, nullable=False)
    class_level = Column(String, nullable=False)
    language_stream = Column(Enum(LanguageStream), nullable=False)
    class_code = Column(String, unique=True, nullable=False)
    is_permanent = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="classes")
    enrollments = relationship("StudentEnrollment", back_populates="class_")
    materials = relationship("Material", back_populates="class_")
    assignments = relationship("Assignment", back_populates="class_")


class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey('students.id'))
    class_id = Column(String, ForeignKey('classes.id'))
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    student = relationship("Student", back_populates="enrollments")
    class_ = relationship("Class", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint('student_id', 'class_id', name='unique_enrollment'),
    )


class Material(Base):
    __tablename__ = "materials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String, ForeignKey('classes.id'))
    teacher_id = Column(String, ForeignKey('teachers.id'))
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    class_level = Column(String, nullable=False)
    term = Column(Integer, nullable=True)  # 1, 2, or 3
    topic = Column(String, nullable=True)
    is_visible_to_students = Column(Boolean, default=False)
    for_lumina_internal_use = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class_ = relationship("Class", back_populates="materials")


class AISession(Base):
    __tablename__ = "ai_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey('students.id'))
    class_id = Column(String, ForeignKey('classes.id'), nullable=True)
    mentor_mode = Column(String, default="guide")  # guide, explain, quiz, writing_coach, debate, explore
    subject = Column(String, nullable=True)
    current_topic = Column(String, nullable=True)
    duration_minutes = Column(Integer, default=0)
    concepts_mastered = Column(JSON, default=list)
    concepts_struggling = Column(JSON, default=list)
    emotional_state = Column(String, default="neutral")
    content_source = Column(String, nullable=True)  # "teacher_upload" or "general_curriculum"
    content_document_title = Column(String, nullable=True)
    academic_integrity_flag = Column(Boolean, default=False)
    safety_flag = Column(Boolean, default=False)
    safety_note = Column(Text, nullable=True)
    leaderboard_points = Column(Integer, default=0)
    session_number = Column(Integer, default=1)
    is_exam_prep_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="sessions")
    messages = relationship("AIMessage", back_populates="session")


class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey('ai_sessions.id'))
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    mentor_mode = Column(String, default="guide")
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("AISession", back_populates="messages")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String, ForeignKey('classes.id'))
    teacher_id = Column(String, ForeignKey('teachers.id'))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=False)
    max_score = Column(Integer, default=100)
    rubric = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class_ = relationship("Class", back_populates="assignments")
    teacher = relationship("Teacher", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment")


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_id = Column(String, ForeignKey('assignments.id'))
    student_id = Column(String, ForeignKey('students.id'))
    content = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    score = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    graded_by_teacher_id = Column(String, Foreign=True('teachers.id'), nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    graded_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String, ForeignKey('classes.id'), nullable=True)
    teacher_id = Column(String, ForeignKey('teachers.id'), nullable=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    class_level = Column(String, nullable=False)
    duration_minutes = Column(Integer, default=30)
    total_questions = Column(Integer, default=20)
    difficulty = Column(String, default="medium")  # easy, medium, hard
    source = Column(String, default="general_curriculum")  # or "teacher_upload"
    is_exam_style = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("QuizQuestion", back_populates="quiz")
    attempts = relationship("QuizAttempt", back_populates="quiz")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey('quizzes.id'))
    question_text = Column(Text, nullable=False)
    question_type = Column(String, default="multiple_choice")  # multiple_choice, short_answer, structured, essay
    options = Column(JSON, nullable=True)  # For multiple choice
    correct_answer = Column(Text, nullable=True)
    points = Column(Integer, default=1)
    topic = Column(String, nullable=True)
    order = Column(Integer, default=0)

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey('quizzes.id'))
    student_id = Column(String, ForeignKey('students.id'))
    score = Column(Integer, nullable=True)
    percentage = Column(Float, nullable=True)
    answers = Column(JSON, default=dict)  # {question_id: answer}
    is_complete = Column(Boolean, default=False)
    time_taken_minutes = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student", back_populates="quiz_attempts")


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey('students.id'))
    class_id = Column(String, ForeignKey('classes.id'), nullable=True)
    category = Column(String, nullable=False)  # participation, speed, quiz
    points = Column(Integer, default=0)
    rank = Column(Integer, default=0)
    week_number = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    is_all_time = Column(Boolean, default=False)
    badges = Column(JSON, default=list)
    updated_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="leaderboard_entries")
    class_ = relationship("Class", foreign_keys=[class_id])


class StudentFlag(Base):
    __tablename__ = "student_flags"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey('students.id'))
    teacher_id = Column(String, ForeignKey('teachers.id'))
    flag_type = Column(String, nullable=False)  # "at_risk", "parent_notification", "safety"
    reason = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="flags")
    student = relationship("Student")


# Cameroon-specific data constants
CAMEROON_REGIONS = [
    "Adamawa", "Centre", "East", "Far North", "Littoral", 
    "North", "North-West", "West", "South", "South-West"
]

REGION_CODES = {
    "Adamawa": "ADM", "Centre": "CEN", "East": "EST", 
    "Far North": "FNO", "Littoral": "LIT", "North": "NOR",
    "North-West": "NWE", "West": "OUE", "South": "SUD", "South-West": "SWE"
}

ANGLOPHONE_PRIMARY_LEVELS = ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6"]
ANGLOPHONE_O_LEVEL = ["Form 1", "Form 2", "Form 3", "Form 4", "Form 5"]
ANGLOPHONE_A_LEVEL = ["Lower Sixth", "Upper Sixth"]

FRANCOPHONE_PRIMARY_LEVELS = ["SIL", "CP", "CE1", "CE2", "CM1", "CM2"]
FRANCOPHONE_COLLEGE_LEVELS = ["6eme", "5eme", "4eme", "3eme"]
FRANCOPHONE_LYCEE_LEVELS = ["2nde", "1ere", "Terminale"]

ANGLOPHONE_PRIMARY_SUBJECTS = [
    "English Language", "Mathematics", "General Science", "Social Studies",
    "Moral Education", "Physical Education", "Religious Studies", "Creative Arts"
]

ANGLOPHONE_O_LEVEL_SUBJECTS = [
    "English Language", "Literature in English", "Mathematics", "Additional Mathematics",
    "Physics", "Chemistry", "Biology", "Further Mathematics", "Geography", "History",
    "Economics", "Commerce", "Computer Science", "Food and Nutrition", "Agriculture",
    "French Language", "Religious Studies", "Physical Education"
]

ANGLOPHONE_A_LEVEL_SUBJECTS = {
    "Science": ["Mathematics", "Further Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "Geography"],
    "Arts": ["Literature in English", "History", "Geography", "Economics", "Religious Studies", "French", "Sociology", "Philosophy"],
    "Commercial": ["Principles of Accounts", "Economics", "Commerce", "Mathematics", "Business Studies", "Computer Science"]
}

FRANCOPHONE_PRIMARY_SUBJECTS = [
    "Francais", "Mathematiques", "Sciences et Technologie", "Histoire-Geographie",
    "Education Morale", "Education Physique", "Anglais Introduction", "Arts Plastiques"
]

FRANCOPHONE_COLLEGE_SUBJECTS = [
    "Francais", "Mathematiques", "Physique-Chimie", "Sciences de la Vie et de la Terre",
    "Histoire-Geographie", "Education Physique", "Anglais", "Informatique", "Education a la Citoyennete"
]

FRANCOPHONE_BAC_SUBJECTS = {
    "A": ["Francais", "Philosophie", "Histoire-Geographie", "Anglais", "Mathematiques", "Sciences Economiques"],
    "C": ["Mathematiques", "Physique-Chimie", "Sciences de la Vie", "Philosophie", "Francais", "Anglais"],
    "D": ["Sciences de la Vie et de la Terre", "Mathematiques", "Physique-Chimie", "Francais", "Philosophie"],
    "E": ["Mathematiques", "Sciences Industrielles", "Physique", "Technologie"]
}
