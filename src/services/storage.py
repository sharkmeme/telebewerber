"""
In-memory storage for active applicant sessions.

In production, this could be replaced with Redis or a database.
"""

from typing import Dict, Optional
import logging

from models.applicant import Applicant

logger = logging.getLogger(__name__)


class ApplicantStorage:
    """Simple in-memory storage for active applicant sessions."""

    def __init__(self):
        self._storage: Dict[int, Applicant] = {}

    def create(self, user_id: int, telegram_username: Optional[str] = None) -> Applicant:
        """Create a new applicant session."""
        applicant = Applicant(user_id=user_id, telegram_username=telegram_username)
        self._storage[user_id] = applicant
        logger.info(f"Created new applicant session for user {user_id}")
        return applicant

    def get(self, user_id: int) -> Optional[Applicant]:
        """Get an applicant session by user ID."""
        return self._storage.get(user_id)

    def update(self, applicant: Applicant) -> None:
        """Update an applicant session."""
        self._storage[applicant.user_id] = applicant
        logger.debug(f"Updated applicant session for user {applicant.user_id}")

    def delete(self, user_id: int) -> None:
        """Delete an applicant session."""
        if user_id in self._storage:
            del self._storage[user_id]
            logger.info(f"Deleted applicant session for user {user_id}")

    def get_all(self) -> Dict[int, Applicant]:
        """Get all active applicant sessions."""
        return self._storage.copy()

    def count(self) -> int:
        """Get count of active sessions."""
        return len(self._storage)


# Global storage instance
applicant_storage = ApplicantStorage()
