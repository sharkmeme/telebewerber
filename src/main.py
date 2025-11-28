"""
Telegram Job Application Bot - Main Entry Point

Supports both polling (local development) and webhook (Railway deployment) modes.
"""

import logging
import os
from telegram.ext import Application, CallbackQueryHandler
from telegram.ext import ApplicationBuilder

from config.settings import settings
from bot.handlers.application import get_application_conversation_handler
from bot.handlers.admin import (
    admin_ai_rate_callback,
    admin_send_quiz_callback,
    admin_send_interview_callback,
)
from bot.handlers.quiz import get_quiz_conversation_handler


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def setup_webhook(application: Application):
    """Configure Telegram webhook for Railway deployment."""
    webhook_url = f"{settings.WEBHOOK_URL}/{settings.TELEGRAM_BOT_TOKEN}"

    logger.info(f"Setting webhook to: {webhook_url}")
    await application.bot.set_webhook(
        url=webhook_url,
        allowed_updates=["message", "callback_query"],
    )


def main():
    logger.info("Starting Telegram bot...")

    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Admin callback handlers (MUST be added BEFORE ConversationHandlers)
    application.add_handler(CallbackQueryHandler(admin_ai_rate_callback, pattern="^admin_ai_rate_"))
    application.add_handler(CallbackQueryHandler(admin_send_quiz_callback, pattern="^admin_send_quiz_"))
    application.add_handler(CallbackQueryHandler(admin_send_interview_callback, pattern="^admin_send_interview_"))

    # Add main application handler
    application.add_handler(get_application_conversation_handler())

    # Quiz handler
    application.add_handler(get_quiz_conversation_handler())

    # Local polling mode
    if settings.MODE == "polling":
        logger.info("Running in POLLING mode")
        application.run_polling()

    # Railway webhook mode
    else:
        logger.info("Running in WEBHOOK mode")
        port = settings.PORT
        logger.info(f"Listening on port {port}")

        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=settings.TELEGRAM_BOT_TOKEN,
            webhook_url=f"{settings.WEBHOOK_URL}/{settings.TELEGRAM_BOT_TOKEN}",
        )


if __name__ == "__main__":
    main()
