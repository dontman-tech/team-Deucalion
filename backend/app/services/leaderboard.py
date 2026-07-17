from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import isoweek

from app.models import (
    Student, LeaderboardEntry, AISession, AssignmentSubmission, 
    QuizAttempt, StudentEnrollment, Class
)
from app.config import settings


class LeaderboardService:
    """Service for managing leaderboard points and rankings."""
    
    # Participation points
    PARTICIPATION_POINTS = {
        "live_class_attendance": 10,
        "answer_teacher_question": 5,
        "ai_study_session_15min": 5,
        "read_knowledge_article": 3,
        "daily_login": 3,
        "post_study_question": 8,
        "answer_classmate_question": 5
    }
    
    # Submission speed points
    SPEED_POINTS = {
        "early_48h": 50,
        "early_24h": 35,
        "on_time_6h": 20,
        "on_due_date": 10,
        "late_1day": 0,
        "not_submitted": -15
    }
    
    # Quality modifiers
    QUALITY_MODIFIERS = {
        "excellent": 1.5,  # 80-100%
        "good": 1.25,      # 60-79%
        "average": 1.0,     # 50-59%
        "poor": 0.5        # <50%
    }
    
    # Quiz points
    QUIZ_POINTS = {
        "perfect": 100,
        "excellent": 75,   # 80-99%
        "good": 50,        # 60-79%
        "fair": 25,        # 40-59%
        "participation": 10  # <40%
    }
    
    @staticmethod
    def get_streak_multiplier(streak_days: int) -> float:
        """Get point multiplier based on streak days."""
        multipliers = settings.STREAK_MULTIPLIERS
        if streak_days >= 30:
            return multipliers[30]
        elif streak_days >= 14:
            return multipliers[14]
        elif streak_days >= 7:
            return multipliers[7]
        elif streak_days >= 3:
            return multipliers[3]
        return 1.0
    
    @staticmethod
    def calculate_streak(participant_points: int, multiplier: float) -> int:
        return int(participant_points * multiplier)
    
    @classmethod
    def award_participation_points(
        cls, 
        db: Session, 
        student: Student, 
        action: str,
        class_id: Optional[str] = None
    ) -> int:
        """Award points for participation activities."""
        if action not in cls.PARTICIPATION_POINTS:
            return 0
        
        base_points = cls.PARTICIPATION_POINTS[action]
        multiplier = cls.get_streak_multiplier(student.streak_days)
        points = cls.calculate_streak(base_points, multiplier)
        
        # Get current week info
        now = datetime.utcnow()
        week = isoweek.Week.now()
        
        # Update or create weekly entry
        entry = db.query(LeaderboardEntry).filter(
            LeaderboardEntry.student_id == student.id,
            LeaderboardEntry.class_id == class_id,
            LeaderboardEntry.category == "participation",
            LeaderboardEntry.week_number == week.week,
            LeaderboardEntry.year == week.year,
            LeaderboardEntry.is_all_time == False
        ).first()
        
        if entry:
            entry.points += points
        else:
            entry = LeaderboardEntry(
                student_id=student.id,
                class_id=class_id,
                category="participation",
                points=points,
                week_number=week.week,
                year=week.year
            )
            db.add(entry)
        
        db.commit()
        return points
    
    @classmethod
    def award_submission_speed_points(
        cls,
        db: Session,
        student: Student,
        submission_time: datetime,
        due_date: datetime,
        grade_percentage: Optional[float] = None,
        class_id: Optional[str] = None
    ) -> int:
        """Award points for assignment submission speed."""
        hours_early = (due_date - submission_time).total_seconds() / 3600
        
        if hours_early > 48:
            base_points = cls.SPEED_POINTS["early_48h"]
            bonus = "Lightning Bonus"
        elif hours_early > 24:
            base_points = cls.SPEED_POINTS["early_24h"]
            bonus = "Early Bird Bonus"
        elif hours_early > 6:
            base_points = cls.SPEED_POINTS["on_time_6h"]
            bonus = "On Time Bonus"
        elif hours_early >= 0:
            base_points = cls.SPEED_POINTS["on_due_date"]
            bonus = None
        else:
            days_late = abs(hours_early) / 24
            if days_late <= 1:
                base_points = cls.SPEED_POINTS["late_1day"]
            else:
                base_points = cls.SPEED_POINTS["not_submitted"] + int(days_late * 5)
            bonus = None
        
        # Apply quality modifier
        if grade_percentage is not None:
            if grade_percentage >= 80:
                modifier = cls.QUALITY_MODIFIERS["excellent"]
            elif grade_percentage >= 60:
                modifier = cls.QUALITY_MODIFIERS["good"]
            elif grade_percentage >= 50:
                modifier = cls.QUALITY_MODIFIERS["average"]
            else:
                modifier = cls.QUALITY_MODIFIERS["poor"]
            base_points = int(base_points * modifier)
        
        # Update leaderboard
        now = datetime.utcnow()
        week = isoweek.Week.now()
        
        entry = db.query(LeaderboardEntry).filter(
            LeaderboardEntry.student_id == student.id,
            LeaderboardEntry.class_id == class_id,
            LeaderboardEntry.category == "speed",
            LeaderboardEntry.week_number == week.week,
            LeaderboardEntry.year == week.year,
            LeaderboardEntry.is_all_time == False
        ).first()
        
        if entry:
            entry.points += base_points
        else:
            entry = LeaderboardEntry(
                student_id=student.id,
                class_id=class_id,
                category="speed",
                points=base_points,
                week_number=week.week,
                year=week.year
            )
            db.add(entry)
        
        db.commit()
        return base_points
    
    @classmethod
    def award_quiz_points(
        cls,
        db: Session,
        student: Student,
        percentage: float,
        is_first_in_class: bool = False,
        is_improvement: bool = False,
        is_retake: bool = False,
        is_top_score: bool = False,
        class_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Award points for quiz performance."""
        points_awarded = {}
        
        # Base score points
        if percentage == 100:
            base_points = cls.QUIZ_POINTS["perfect"]
            badge = "Perfect"
        elif percentage >= 80:
            base_points = cls.QUIZ_POINTS["excellent"]
            badge = None
        elif percentage >= 60:
            base_points = cls.QUIZ_POINTS["good"]
            badge = None
        elif percentage >= 40:
            base_points = cls.QUIZ_POINTS["fair"]
            badge = None
        else:
            base_points = cls.QUIZ_POINTS["participation"]
            badge = None
        
        points_awarded["base"] = base_points
        points_awarded["total"] = base_points
        
        # Bonus points
        bonus_points = 0
        bonuses_earned = []
        
        if is_first_in_class:
            bonus_points += 20
            bonuses_earned.append("First in Class (+20)")
        
        if is_improvement:
            bonus_points += 15
            bonuses_earned.append("Improved Score (+15)")
        
        if is_retake and percentage == 100:
            bonus_points += 30
            bonuses_earned.append("Perfect Retake (+30)")
        
        if is_top_score:
            bonus_points += 25
            badge = "Crown"
            bonuses_earned.append("Class Top Score (+25)")
        
        points_awarded["bonuses"] = bonus_points
        points_awarded["bonuses_earned"] = bonuses_earned
        points_awarded["total"] += bonus_points
        
        # Update leaderboard
        now = datetime.utcnow()
        week = isoweek.Week.now()
        
        entry = db.query(LeaderboardEntry).filter(
            LeaderboardEntry.student_id == student.id,
            LeaderboardEntry.class_id == class_id,
            LeaderboardEntry.category == "quiz",
            LeaderboardEntry.week_number == week.week,
            LeaderboardEntry.year == week.year,
            LeaderboardEntry.is_all_time == False
        ).first()
        
        if entry:
            entry.points += points_awarded["total"]
            if badge and badge not in (entry.badges or []):
                entry.badges = (entry.badges or []) + [badge]
        else:
            entry = LeaderboardEntry(
                student_id=student.id,
                class_id=class_id,
                category="quiz",
                points=points_awarded["total"],
                week_number=week.week,
                year=week.year,
                badges=[badge] if badge else []
            )
            db.add(entry)
        
        db.commit()
        return points_awarded
    
    @classmethod
    def get_class_leaderboard(
        cls,
        db: Session,
        class_id: str,
        category: Optional[str] = None,
        is_all_time: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        """Get leaderboard for a class."""
        query = db.query(LeaderboardEntry, Student).join(
            Student, LeaderboardEntry.student_id == Student.id
        ).filter(
            LeaderboardEntry.class_id == class_id
        )
        
        if category:
            query = query.filter(LeaderboardEntry.category == category)
        
        if is_all_time:
            query = query.filter(LeaderboardEntry.is_all_time == True)
        else:
            week = isoweek.Week.now()
            query = query.filter(
                LeaderboardEntry.week_number == week.week,
                LeaderboardEntry.year == week.year,
                LeaderboardEntry.is_all_time == False
            )
        
        query = query.order_by(desc(LeaderboardEntry.points))
        
        results = []
        for rank, (entry, student) in enumerate(query.limit(limit).all(), 1):
            results.append({
                "rank": rank,
                "student_id": student.id,
                "student_name": student.user.full_name if student.user else "Unknown",
                "category": entry.category,
                "points": entry.points,
                "badges": entry.badges or [],
                "is_all_time": entry.is_all_time
            })
        
        return results
    
    @classmethod
    def update_ranks(cls, db: Session, class_id: str, category: str):
        """Update ranks for a specific class and category."""
        entries = db.query(LeaderboardEntry).filter(
            LeaderboardEntry.class_id == class_id,
            LeaderboardEntry.category == category
        ).order_by(desc(LeaderboardEntry.points)).all()
        
        for rank, entry in enumerate(entries, 1):
            entry.rank = rank
        
        db.commit()
    
    @classmethod
    def get_student_summary(
        cls,
        db: Session,
        student: Student,
        class_id: Optional[str] = None
    ) -> Dict:
        """Get summary of student's leaderboard status."""
        week = isoweek.Week.now()
        
        categories = []
        for cat in ["participation", "speed", "quiz"]:
            entry = db.query(LeaderboardEntry).filter(
                LeaderboardEntry.student_id == student.id,
                LeaderboardEntry.class_id == class_id,
                LeaderboardEntry.category == cat,
                LeaderboardEntry.week_number == week.week,
                LeaderboardEntry.year == week.year
            ).first()
            
            categories.append({
                "category": cat,
                "points": entry.points if entry else 0,
                "rank": entry.rank if entry else 0
            })
        
        # Calculate overall
        total_points = sum(c["points"] for c in categories)
        total_rank = sum(c["rank"] for c in categories) // len(categories) if categories else 0
        
        return {
            "participation": categories[0],
            "speed": categories[1],
            "quiz": categories[2],
            "total_points": total_points,
            "overall_rank": total_rank,
            "streak_days": student.streak_days,
            "streak_multiplier": cls.get_streak_multiplier(student.streak_days)
        }
