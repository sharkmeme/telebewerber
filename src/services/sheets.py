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
    Sends applicant data to Google Apps Script Webhook instead of using Google Sheets API.
    """

    def __init__(self):
        self.webhook_url = settings.GOOGLE_SHEETS_WEBHOOK_URL

    def append_applicant_row(self, applicant: Applicant) -> int:
        if not self.webhook_url:
            logger.warning("No Google Sheets webhook URL configured.")
            return 0

        payload = {
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

        requests.post(self.webhook_url, json=payload)
        return 1  # No row index needed anymore

    def update_status(self, row_index: int, status: str):
        if not self.webhook_url:
            return
        # No-op: Apps Script does not support row updates without API credentials.

    def update_ai_result(self, row_index: int, ai_result: Dict[str, Any]):
        if not self.webhook_url:
            return
        # No-op due to webhook architecture.

    def update_quiz(self, row_index: int, quiz_answers: Dict[str, Any]):
        if not self.webhook_url:
            return
        # No-op due to webhook architecture.


sheets_service = SheetsService()
