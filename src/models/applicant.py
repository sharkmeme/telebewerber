"""
Applicant data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any


@dataclass
class Applicant:
    """
    Complete applicant session model for the Telegram job application bot.
    Follows the exact MASTER SPEC fields.
    """

    # Telegram identifiers
    user_id: int
    telegram_username: Optional[str] = None

    # Position
    position: Optional[str] = None
    custom_position: Optional[str] = None

    # Collected answers
    answers: Dict[str, Any] = field(default_factory=dict)

    # Personal info
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    socials: Optional[str] = None

    # Files
    cv_file_id: Optional[str] = None
    portfolio_files: List[str] = field(default_factory=list)

    # Quiz
    quiz_answers: Dict[str, Any] = field(default_factory=dict)

    # AI evaluation
    ai_result: Dict[str, Any] = field(default_factory=dict)

    # Workflow status
    status: str = "in_progress"

    # Google Sheets row
    sheet_row_index: Optional[int] = None

    # Navigation history for back button
    history: List[str] = field(default_factory=list)

    # Internal metadata
    started_at: datetime = field(default_factory=datetime.utcnow)
