"""
In-memory storage for active applicant sessions.

In production, this could be replaced with Redis or a database.
"""

import logging
from typing import Dict, Optional

from models.applicant import Applicant

logger = logging.getLogger(__name__)


class ApplicantStorage:
    """
    Simple in-memory storage for applicant sessions.
    Maps user_id -> Applicant object.
    """

    def __init__(self):
        self._storage: Dict[int, Applicant] = {}

    def save(self, applicant: Applicant):
        """Store or replace an applicant object by user_id."""
        self._storage[applicant.user_id] = applicant

    def get(self, user_id: int) -> Optional[Applicant]:
        """Retrieve an applicant object by user_id."""
        return self._storage.get(user_id)

    def delete(self, user_id: int):
        """Remove applicant session."""
        if user_id in self._storage:
            del self._storage[user_id]


# Singleton instance
applicant_storage = ApplicantStorage()
