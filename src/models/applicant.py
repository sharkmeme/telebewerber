"""
Applicant data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List


@dataclass
class Applicant:
    """Represents a job applicant and their application data."""

    user_id: int
    telegram_username: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)

    # Position
    position: Optional[str] = None

    # Personal Information
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    social_links: Optional[str] = None

    # Application Materials
    cv_file_id: Optional[str] = None  # Telegram file ID
    cv_file_path: Optional[str] = None  # Local download path

    # Position-specific answers (question_id -> answer)
    answers: Dict[str, str] = field(default_factory=dict)

    # Proof of work (file IDs or links)
    proof_of_work: List[str] = field(default_factory=list)

    # Quiz results (if applicable)
    quiz_score: Optional[float] = None
    quiz_answers: Dict[str, str] = field(default_factory=dict)

    # AI Evaluation
    ai_rating: Optional[float] = None
    ai_feedback: Optional[str] = None

    # Status
    completed_at: Optional[datetime] = None
    status: str = "in_progress"  # in_progress, completed, quiz_pending

    def to_dict(self) -> dict:
        """Convert applicant to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "telegram_username": self.telegram_username,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "position": self.position,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "social_links": self.social_links,
            "cv_file_id": self.cv_file_id,
            "cv_file_path": self.cv_file_path,
            "answers": self.answers,
            "proof_of_work": self.proof_of_work,
            "quiz_score": self.quiz_score,
            "quiz_answers": self.quiz_answers,
            "ai_rating": self.ai_rating,
            "ai_feedback": self.ai_feedback,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
        }
