"""
Admin command handlers and notifications.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import logging

from config.settings import settings
from models.applicant import Applicant
from services.storage import applicant_storage
from services.sheets import sheets_service
from services.ai_evaluator import ai_evaluator

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id == settings.ADMIN_CHAT_ID


def build_admin_keyboard(applicant: Applicant) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 AI Rate Candidate", callback_data=f"admin_ai_rate_{applicant.user_id}")],
        [InlineKeyboardButton("📝 Send Quiz", callback_data=f"admin_send_quiz_{applicant.user_id}")],
        [InlineKeyboardButton("📅 Send Interview Link", callback_data=f"admin_send_interview_{applicant.user_id}")]
    ])


async def notify_admin_new_applicant(context: ContextTypes.DEFAULT_TYPE, applicant: Applicant) -> None:
    """Send admin the applicant summary after submission."""
    position = (
        applicant.custom_position
        if applicant.position == "other"
        else applicant.position
    )

    text = (
        "📨 <b>New Applicant Submitted</b>\n\n"
        f"<b>Name:</b> {applicant.full_name}\n"
        f"<b>Username:</b> @{applicant.telegram_username}\n"
        f"<b>Position:</b> {position}\n"
        f"<b>Sheets Row:</b> {applicant.sheet_row_index}\n\n"
        "<b>Answers:</b>\n"
        f"{applicant.answers}"
    )

    await context.bot.send_message(
        chat_id=settings.ADMIN_CHAT_ID,
        text=text,
        parse_mode="HTML",
        reply_markup=build_admin_keyboard(applicant)
    )


async def admin_ai_rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    applicant_id = int(query.data.replace("admin_ai_rate_", ""))
    applicant = applicant_storage.get(applicant_id)
    if not applicant:
        await query.message.reply_text("Applicant not found.")
        return

    include_quiz = bool(applicant.quiz_answers)
    result = ai_evaluator.evaluate(applicant, include_quiz=include_quiz)
    applicant.ai_result = result
    sheets_service.update_ai_result(applicant.sheet_row_index, result)

    formatted = (
        "<b>AI Evaluation Result</b>\n\n"
        f"Recommendation: {result.get('overall_recommendation')}\n"
        f"Scores: {result.get('scores')}\n"
        f"Summary: {result.get('short_summary')}\n"
        f"Red Flags: {result.get('red_flags')}\n"
    )

    await query.message.reply_html(formatted)


async def admin_send_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    applicant_id = int(query.data.replace("admin_send_quiz_", ""))
    applicant = applicant_storage.get(applicant_id)
    if not applicant:
        await query.message.reply_text("Applicant not found.")
        return

    applicant.status = "quiz_sent"
    sheets_service.update_status(applicant.sheet_row_index, "quiz_sent")

    await context.bot.send_message(
        chat_id=applicant.user_id,
        text="You have received a quiz. Tap below to begin.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Start Quiz", callback_data="start_quiz_now")]
        ])
    )

    await query.message.reply_text("Quiz sent.")


async def admin_send_interview_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    applicant_id = int(query.data.replace("admin_send_interview_", ""))
    applicant = applicant_storage.get(applicant_id)
    if not applicant:
        await query.message.reply_text("Applicant not found.")
        return

    await context.bot.send_message(
        chat_id=applicant.user_id,
        text=f"You have been invited to an interview:\n{settings.INTERVIEW_LINK}"
    )

    applicant.status = "interview_sent"
    sheets_service.update_status(applicant.sheet_row_index, "interview_sent")

    await query.message.reply_text("Interview link sent.")
