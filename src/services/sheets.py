"""
Google Sheets integration for storing applicant data.
"""

import json
import logging
import requests
from datetime import datetime
from typing import Any, Dict

from config.settings import settings
from models.applicant import Applicant

logger = logging.getLogger(__name__)


class SheetsService:
    """
    Google Sheets integration via Apps Script Webhook.
    Supports append and row updates without Google API credentials.
    """

    def __init__(self):
        self.webhook_url = settings.GOOGLE_SHEETS_WEBHOOK_URL

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to POST JSON to Apps Script backend."""
        if not self.webhook_url:
            logger.error("No GOOGLE_SHEETS_WEBHOOK_URL configured.")
            return {"success": False}

        try:
            response = requests.post(self.webhook_url, json=payload)
            return response.json()
        except Exception as e:
            logger.error(f"Sheets webhook error: {e}")
            return {"success": False}

    def append_applicant_row(self, applicant: Applicant) -> int:
        """
        Sends a new applicant row to Apps Script.
        Receives a real row index from the backend.
        """
        payload = {
            "action": "append",
            "timestamp": datetime.utcnow().isoformat(),
            "telegram_user_id": applicant.user_id,
            "telegram_username": applicant.telegram_username,
            "full_name": applicant.full_name,
            "email": applicant.email,
            "phone": applicant.phone,
            "socials": applicant.socials,
            "position": applicant.custom_position if applicant.position == "other" else applicant.position,
            "answers": applicant.answers,
            "cv_file_id": applicant.cv_file_id,
            "portfolio": applicant.portfolio_files,
            "ai_recommendation": "",
            "ai_scores": {},
            "ai_summary": "",
            "red_flags": [],
            "status": applicant.status,
        }

        result = self._post(payload)
        return result.get("row_index", 0)

    def update_status(self, row_index: int, status: str):
        """Update the status column for an existing row."""
        self._post({
            "action": "updateStatus",
            "row_index": row_index,
            "status": status
        })

    def update_ai_result(self, row_index: int, ai_result: Dict[str, Any]):
        """Update AI evaluation columns for an existing row."""
        self._post({
            "action": "updateAI",
            "row_index": row_index,
            "ai_recommendation": ai_result.get("overall_recommendation"),
            "ai_scores": ai_result.get("scores", {}),
            "ai_summary": ai_result.get("short_summary"),
            "red_flags": ai_result.get("red_flags", [])
        })

    def update_quiz(self, row_index: int, quiz_answers: Dict[str, Any]):
        """Update quiz results for an applicant row."""
        self._post({
            "action": "updateQuiz",
            "row_index": row_index,
            "answers": quiz_answers
        })


sheets_service = SheetsService()
