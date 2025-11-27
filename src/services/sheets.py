"""
Google Sheets integration for storing applicant data.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import gspread
from google.oauth2.service_account import Credentials

from config.settings import settings
from models.applicant import Applicant

logger = logging.getLogger(__name__)


class SheetsService:
    """
    Google Sheets integration following the 16-column MASTER SPEC schema.
    """

    def __init__(self):
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS_CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        self.sheet = client.open_by_key(settings.GOOGLE_SHEETS_ID).sheet1

    def append_applicant_row(self, applicant: Applicant) -> int:
        """Append a new applicant row and return the row index."""
        position = applicant.custom_position if applicant.position == "other" else applicant.position

        row = [
            datetime.utcnow().isoformat(),          # 1 timestamp
            applicant.user_id,                       # 2 telegram_user_id
            applicant.telegram_username or "",       # 3 telegram_username
            applicant.full_name or "",               # 4 full_name
            applicant.email or "",                   # 5 email
            applicant.phone or "",                   # 6 phone
            applicant.socials or "",                 # 7 socials
            position or "",                          # 8 position
            json.dumps(applicant.answers),           # 9 answers_json
            applicant.cv_file_id or "",              #10 cv_file_id
            json.dumps(applicant.portfolio_files),   #11 portfolio_json
            "",                                      #12 ai_recommendation
            "",                                      #13 ai_scores_json
            "",                                      #14 ai_summary
            "",                                      #15 ai_red_flags_json
            applicant.status or "submitted",         #16 status
        ]

        self.sheet.append_row(row)
        return len(self.sheet.get_all_values())

    def update_status(self, row_index: int, status: str) -> None:
        """Update the status column."""
        self.sheet.update_cell(row_index, 16, status)

    def update_ai_result(self, row_index: int, ai_result: Dict[str, Any]) -> None:
        """Write AI evaluation results."""
        self.sheet.update_cell(row_index, 12, ai_result.get("overall_recommendation", ""))
        self.sheet.update_cell(row_index, 13, json.dumps(ai_result.get("scores", {})))
        self.sheet.update_cell(row_index, 14, ai_result.get("short_summary", ""))
        self.sheet.update_cell(row_index, 15, json.dumps(ai_result.get("red_flags", [])))

    def update_quiz(self, row_index: int, quiz_answers: Dict[str, Any]) -> None:
        """Merge quiz answers into the answers_json field."""
        existing_raw = self.sheet.cell(row_index, 9).value or "{}"
        try:
            existing = json.loads(existing_raw)
        except Exception:
            existing = {}

        existing["quiz"] = quiz_answers
        self.sheet.update_cell(row_index, 9, json.dumps(existing))


# Singleton instance
sheets_service = SheetsService()
