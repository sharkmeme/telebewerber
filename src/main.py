"""
Telegram Job Application Bot - Main Entry Point

This bot automates job applications via Telegram, collects applicant data,
evaluates candidates using AI, and stores results in Google Sheets.
"""

import logging
from telegram.ext import Application, CommandHandler

from config.settings import settings
from bot.handlers.application import get_application_conversation_handler
from bot.handlers.admin import admin_start_handler, stats_handler
from utils.logger import setup_logging


def main() -> None:
    """Start the bot."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Telegram Job Application Bot...")
    logger.info(f"Bot token: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
    logger.info(f"Admin chat ID: {settings.ADMIN_CHAT_ID}")

    # Create application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(get_application_conversation_handler())
    application.add_handler(CommandHandler("admin", admin_start_handler))
    application.add_handler(CommandHandler("stats", stats_handler))

    # Start the bot
    logger.info("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
