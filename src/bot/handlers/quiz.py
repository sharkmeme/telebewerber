"""
Quiz handler for evaluating applicants.
"""

import logging
from typing import Any, Dict

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters

from bot.conversations.states import QuizState
from models.quiz_config import QUIZ
from services.storage import applicant_storage
from services.sheets import sheets_service
from config.settings import settings

logger = logging.getLogger(__name__)


def get_next_quiz_question(applicant):
    answered = len(applicant.quiz_answers)
    if answered >= len(QUIZ):
        return None
    return QUIZ[answered]


async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the quiz for the applicant."""
    # Identify applicant - admin triggered it, so context.user_data must track target
    # But admin handler already knows applicant, so we assume user_id == applicant
    # and admin already messaged the applicant personally.

    # We handle this correctly when admin initiates quiz:
    # bot.send_message(to applicant)
    # start_quiz(fake_update)
    # So update.message is None in admin flow.
    # We fallback to applicant from storage.

    applicant = None

    # If update.message exists → user started quiz normally
    if update.message:
        applicant = applicant_storage.get(update.effective_user.id)
    else:
        # else admin triggered; context should have been set earlier
        # We assume admin pass update through fake_update
        # So use context.chat_data['applicant_id']
        # If missing, fallback to user id
        user_id = context.chat_data.get("applicant_id", None)
        if user_id:
            applicant = applicant_storage.get(user_id)

    if not applicant:
        return ConversationHandler.END

    applicant.quiz_answers = {}

    # Ask first question
    q = QUIZ[0]
    await ask_quiz_question(update, context, applicant, q)
    return QuizState.QUIZ_QUESTION


async def ask_quiz_question(update_or_query, context, applicant, question):
    qtype = question["type"]
    qtext = question["q"]

    if qtype == "text":
        await update_or_query.effective_message.reply_text(qtext)

    elif qtype == "choice":
        buttons = [[InlineKeyboardButton(opt, callback_data=f"quiz_choice_{opt}")] for opt in question["options"]]
        await update_or_query.effective_message.reply_text(qtext, reply_markup=InlineKeyboardMarkup(buttons))

    elif qtype == "multi_choice":
        buttons = [[InlineKeyboardButton(f"[ ] {opt}", callback_data=f"quiz_multi_{opt}")] for opt in question["options"]]
        buttons.append([InlineKeyboardButton("Done", callback_data="quiz_multi_done")])
        await update_or_query.effective_message.reply_text(qtext, reply_markup=InlineKeyboardMarkup(buttons))


async def handle_text_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    applicant = applicant_storage.get(update.effective_user.id)
    q = get_next_quiz_question(applicant)
    applicant.quiz_answers[q["id"]] = update.message.text.strip()

    next_q = get_next_quiz_question(applicant)
    if next_q:
        await ask_quiz_question(update, context, applicant, next_q)
        return QuizState.QUIZ_QUESTION

    return await finish_quiz(update, context, applicant)


async def handle_choice_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    applicant = applicant_storage.get(query.from_user.id)
    q = get_next_quiz_question(applicant)

    choice = query.data.replace("quiz_choice_", "", 1)
    applicant.quiz_answers[q["id"]] = choice

    next_q = get_next_quiz_question(applicant)
    if next_q:
        await ask_quiz_question(update, context, applicant, next_q)
        return QuizState.QUIZ_QUESTION

    return await finish_quiz(update, context, applicant)


async def handle_multi_choice_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    applicant = applicant_storage.get(query.from_user.id)
    q = get_next_quiz_question(applicant)

    if q["id"] not in applicant.quiz_answers:
        applicant.quiz_answers[q["id"]] = []

    if query.data == "quiz_multi_done":
        next_q = get_next_quiz_question(applicant)
        if next_q:
            await ask_quiz_question(update, context, applicant, next_q)
            return QuizState.QUIZ_QUESTION

        return await finish_quiz(update, context, applicant)

    choice = query.data.replace("quiz_multi_", "", 1)
    if choice not in applicant.quiz_answers[q["id"]]:
        applicant.quiz_answers[q["id"]].append(choice)

    return QuizState.QUIZ_QUESTION


async def finish_quiz(update_or_query, context, applicant):
    """Finish quiz, save to Sheets, notify admin."""
    # Save quiz answers in sheet
    sheets_service.update_quiz(applicant.sheet_row_index, applicant.quiz_answers)
    sheets_service.update_status(applicant.sheet_row_index, "quiz_completed")
    applicant.status = "quiz_completed"

    await update_or_query.effective_message.reply_text("Thank you! Your quiz is complete.")

    # Notify admin
    await context.bot.send_message(
        chat_id=settings.ADMIN_CHAT_ID,
        text=f"Applicant {applicant.full_name} (@{applicant.telegram_username}) has completed the quiz."
    )

    return ConversationHandler.END


def get_quiz_conversation_handler():
    return ConversationHandler(
        entry_points=[],
        states={
            QuizState.QUIZ_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_quiz_answer),
                CallbackQueryHandler(handle_choice_quiz_answer, pattern="^quiz_choice_"),
                CallbackQueryHandler(handle_multi_choice_quiz, pattern="^quiz_multi_|quiz_multi_done"),
            ],
        },
        fallbacks=[],
    )
