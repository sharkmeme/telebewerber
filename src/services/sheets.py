"""
Google Sheets integration for storing applicant data.
"""

import logging
from typing import List, Optional
from datetime import datetime

from config.settings import settings
from models.applicant import Applicant

logger = logging.getLogger(__name__)


class SheetsService:
    """Google Sheets service for storing applicant data."""

    def __init__(self):
        self.sheet_id = settings.GOOGLE_SHEETS_ID
        self.credentials_file = settings.GOOGLE_SHEETS_CREDENTIALS_FILE
        self.client = None
        self.sheet = None

        if self.credentials_file and self.sheet_id:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize Google Sheets API client."""
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )

            self.client = gspread.authorize(credentials)
            self.sheet = self.client.open_by_key(self.sheet_id).sheet1

            # Ensure headers exist
            self._ensure_headers()

            logger.info("Google Sheets client initialized successfully")

        except ImportError:
            logger.error("gspread not installed. Run: pip install gspread google-auth")
        except FileNotFoundError:
            logger.error(f"Credentials file not found: {self.credentials_file}")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")

    def _ensure_headers(self):
        """Ensure the spreadsheet has proper headers."""
        if not self.sheet:
            return

        headers = [
            "Timestamp",
            "User ID",
            "Telegram Username",
            "Position",
            "Full Name",
            "Email",
            "Phone",
            "Social Links",
            "CV File ID",
            "Answers",
            "Proof of Work",
            "Quiz Score",
            "AI Rating",
            "AI Feedback",
            "Status",
        ]

        try:
            existing_headers = self.sheet.row_values(1)
            if not existing_headers:
                self.sheet.append_row(headers)
                logger.info("Created headers in Google Sheet")
        except Exception as e:
            logger.error(f"Failed to ensure headers: {e}")

    def save_applicant(self, applicant: Applicant) -> bool:
        """
        Save applicant data to Google Sheets.

        Args:
            applicant: The applicant to save

        Returns:
            True if successful, False otherwise
        """
        if not self.sheet:
            logger.warning("Google Sheets not configured, skipping save")
            return False

        try:
            row = [
                applicant.completed_at.isoformat() if applicant.completed_at else datetime.now().isoformat(),
                applicant.user_id,
                applicant.telegram_username or "",
                applicant.position or "",
                applicant.full_name or "",
                applicant.email or "",
                applicant.phone or "",
                applicant.social_links or "",
                applicant.cv_file_id or "",
                str(applicant.answers),
                ", ".join(applicant.proof_of_work),
                applicant.quiz_score or "",
                applicant.ai_rating or "",
                applicant.ai_feedback or "",
                applicant.status,
            ]

            self.sheet.append_row(row)
            logger.info(f"Saved applicant {applicant.user_id} to Google Sheets")
            return True

        except Exception as e:
            logger.error(f"Failed to save applicant to Google Sheets: {e}")
            return False

    def get_all_applicants(self) -> List[dict]:
        """Get all applicants from the sheet."""
        if not self.sheet:
            logger.warning("Google Sheets not configured")
            return []

        try:
            return self.sheet.get_all_records()
        except Exception as e:
            logger.error(f"Failed to get applicants from Google Sheets: {e}")
            return []


# Global sheets service instance
sheets_service = SheetsService()
