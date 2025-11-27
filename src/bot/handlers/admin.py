"""
Admin command handlers and notifications.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import settings
from models.applicant import Applicant
from services.storage import applicant_storage
from services.sheets import sheets_service
from bot.conversations.keyboards import get_admin_action_keyboard

logger = logging.getLogger(__name__)


async def notify_admin_new_applicant(context: ContextTypes.DEFAULT_TYPE, applicant: Applicant) -> None:
    """
    Send notification to admin when a new applicant completes their application.

    Args:
        context: Bot context
        applicant: The completed applicant
    """
    try:
        message = f"""
🆕 <b>New Applicant!</b>

👤 <b>Name:</b> {applicant.full_name}
💼 <b>Position:</b> {applicant.position}
📧 <b>Email:</b> {applicant.email}
📱 <b>Phone:</b> {applicant.phone}
🔗 <b>Telegram:</b> @{applicant.telegram_username or 'N/A'}

🤖 <b>AI Rating:</b> {applicant.ai_rating}/10
💬 <b>AI Feedback:</b> {applicant.ai_feedback}

<b>Answers:</b>
"""
        for question_id, answer in applicant.answers.items():
            message += f"• {question_id}: {answer}\n"

        if applicant.social_links:
            message += f"\n🌐 <b>Links:</b> {applicant.social_links}"

        if applicant.proof_of_work:
            message += f"\n📂 <b>Proof of Work:</b> {len(applicant.proof_of_work)} items"

        await context.bot.send_message(
            chat_id=settings.ADMIN_CHAT_ID,
            text=message,
            parse_mode='HTML',
            reply_markup=get_admin_action_keyboard(applicant.user_id)
        )

        # Send CV if available
        if applicant.cv_file_id:
            await context.bot.send_document(
                chat_id=settings.ADMIN_CHAT_ID,
                document=applicant.cv_file_id,
                caption=f"CV - {applicant.full_name}"
            )

        logger.info(f"Sent admin notification for applicant {applicant.user_id}")

    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")


async def admin_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command."""
    user_id = update.effective_user.id

    if user_id != settings.ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Admin only command.")
        return

    await update.message.reply_text(
        "🔧 <b>Admin Panel</b>\n\n"
        "Available commands:\n"
        "/stats - View application statistics\n"
        "/export - Export all applicants\n\n"
        "You'll receive notifications when new applicants complete their applications.",
        parse_mode='HTML'
    )


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command - show application statistics."""
    user_id = update.effective_user.id

    if user_id != settings.ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Admin only command.")
        return

    # Get stats from storage
    active_sessions = applicant_storage.count()

    # Get stats from sheets
    all_applicants = sheets_service.get_all_applicants()
    total_applicants = len(all_applicants)

    # Count by position
    position_counts = {}
    for applicant in all_applicants:
        position = applicant.get('Position', 'Unknown')
        position_counts[position] = position_counts.get(position, 0) + 1

    message = f"""
📊 <b>Application Statistics</b>

📝 <b>Total Applications:</b> {total_applicants}
🔄 <b>Active Sessions:</b> {active_sessions}

<b>By Position:</b>
"""

    for position, count in position_counts.items():
        message += f"• {position}: {count}\n"

    await update.message.reply_text(message, parse_mode='HTML')
