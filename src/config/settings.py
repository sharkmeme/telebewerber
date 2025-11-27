"""
Application settings loaded from environment variables.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    ADMIN_CHAT_ID: int

    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_FILE: Optional[str] = None
    GOOGLE_SHEETS_ID: str = ""

    # AI Evaluation
    AI_PROVIDER: str = "anthropic"  # 'anthropic' or 'openai'
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    AI_MODEL: str = "claude-3-5-sonnet-20241022"  # or 'gpt-4o' for OpenAI

    # Application Settings
    LOG_LEVEL: str = "INFO"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "pdf,jpg,jpeg,png,mp4,mov"
    HOMEPAGE_URL: str = "https://yourcompany.com"
    INTERVIEW_LINK: str = "https://calendly.com/yourcompany/interview"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
