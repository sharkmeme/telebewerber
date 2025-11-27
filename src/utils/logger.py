"""
Logging configuration for the application.
"""

import logging
import sys
from config.settings import settings


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Reduce noise from telegram library
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
