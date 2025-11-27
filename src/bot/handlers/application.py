"""
Main application conversation handler.

Handles the applicant flow from greeting to submission.
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot.conversations.states import ApplicationState
from bot.conversations.keyboards import (
    get_positions_keyboard,
    get_choice_keyboard,
    get_skip_keyboard,
    get_confirm_keyboard,
)
from models.applicant import Applicant
from models.position import get_position, QuestionType
from services.storage import applicant_storage
from services.ai_evaluator import ai_evaluator
from services.sheets import sheets_service
from bot.handlers.admin import notify_admin_new_applicant

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the application process."""
    user = update.effective_user

    # Create new applicant session
    applicant = applicant_storage.create(
        user_id=user.id,
        telegram_username=user.username
    )

    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        f"Welcome to our job application bot. "
        f"We're excited that you're interested in joining our team!\n\n"
        f"Visit our homepage: [Your Company Website]\n\n"
        f"Let's get started! Which position are you applying for?",
        reply_markup=get_positions_keyboard()
    )

    return ApplicationState.POSITION_SELECT


async def select_position(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle position selection."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    applicant = applicant_storage.get(user_id)

    if not applicant:
        await query.message.reply_text("Session expired. Please /start again.")
        return ConversationHandler.END

    # Extract position ID from callback data
    position_id = query.data.replace("pos_", "")
    position = get_position(position_id)

    if not position:
        await query.message.reply_text("Invalid position. Please try again.")
        return ApplicationState.POSITION_SELECT

    applicant.position = position.name
    applicant_storage.update(applicant)

    # Store position and question index in context
    context.user_data['position'] = position
    context.user_data['current_question'] = 0

    await query.edit_message_text(
        f"Great! You're applying for: {position.name}\n\n"
        f"{position.description}\n\n"
        f"I'll ask you a few questions about your background."
    )

    # Start asking questions
    return await ask_next_question(update, context)


async def ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the next position-specific question."""
    position = context.user_data.get('position')
    question_index = context.user_data.get('current_question', 0)

    if question_index >= len(position.questions):
        # Done with questions, move to personal info
        return await ask_name(update, context)

    question = position.questions[question_index]

    # Build keyboard based on question type
    keyboard = None
    if question.question_type == QuestionType.CHOICE:
        keyboard = get_choice_keyboard(question.choices)

    if update.callback_query:
        await update.callback_query.message.reply_text(
            question.text,
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            question.text,
            reply_markup=keyboard
        )

    context.user_data['current_question_obj'] = question

    return ApplicationState.ASKING_QUESTIONS


async def handle_question_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle answer to position-specific question."""
    user_id = update.effective_user.id
    applicant = applicant_storage.get(user_id)

    if not applicant:
        await update.message.reply_text("Session expired. Please /start again.")
        return ConversationHandler.END

    question = context.user_data.get('current_question_obj')

    # Get answer based on message type
    if update.callback_query:
        answer = update.callback_query.data.replace("choice_", "")
        await update.callback_query.answer()
    else:
        answer = update.message.text

    # Store answer
    applicant.answers[question.id] = answer
    applicant_storage.update(applicant)

    # Move to next question
    context.user_data['current_question'] += 1

    return await ask_next_question(update, context)


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask for applicant's full name."""
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "Now, let's get your contact information.\n\n"
            "What's your full name?"
        )
    else:
        await update.message.reply_text(
            "Now, let's get your contact information.\n\n"
            "What's your full name?"
        )

    return ApplicationState.ASK_NAME


async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle name input."""
    user_id = update.effective_user.id
    applicant = applicant_storage.get(user_id)

    applicant.full_name = update.message.text
    applicant_storage.update(applicant)

    await update.message.reply_text("What's your email address?")
    return ApplicationState.ASK_EMAIL


async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle email input."""
    user_id = update.effective_user.id
    applicant = applicant_storage.get(user_id)

    applicant.email = update.message.text
    applicant_storage.update(applicant)

    await update.message.reply_text("What's your phone number?")
    return ApplicationState.ASK_PHONE


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle phone input."""
    user_id = update.effective_user.id
    applicant = applicant_storage.get(user_id)

    applicant.phone = update.message.text
    applicant_storage.update(applicant)

    await update.message.reply_text(
        "Do you have any social media or portfolio links you'd like to share?\n"
        "(LinkedIn, GitHub, personal website, etc.)\n\n"
        "Send them or type 'skip' to continue."
    )
    return ApplicationState.ASK_SOCIALS


async def handle_socials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle socials input."""
    user_id = update.effective_user.id
    applicant = applicant_storage.get(user_id)

    if update.message.text.lower() != 'skip':
        applicant.social_links = update.message.text
        applicant_storage.update(applicant)

    await update.message.reply_text(
        "📄 Please upload your CV (PDF only)."
    )
    return ApplicationState.ASK_CV


async def handle_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle CV upload."""
    user_id = update.effective_user.id
    applicant = applicant_storage.get(user_id)

    if update.message.document:
        applicant.cv_file_id = update.message.document.file_id
        applicant_storage.update(applicant)

        position = context.user_data.get('position')

        if position.requires_proof_of_work:
            await update.message.reply_text(
                f"Great! CV received.\n\n"
                f"{position.proof_of_work_description}\n\n"
                f"Please share links or upload files (images/videos).\n"
                f"Type 'done' when finished."
            )
            context.user_data['proof_of_work'] = []
            return ApplicationState.ASK_PROOF_OF_WORK
        else:
            return await finalize_application(update, context)
    else:
        await update.message.reply_text("Please send a PDF file.")
        return ApplicationState.ASK_CV


async def handle_proof_of_work(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle proof of work uploads."""
    user_id = update.effective_user.id
    applicant = applicant_storage.get(user_id)

    if update.message.text and update.message.text.lower() == 'done':
        return await finalize_application(update, context)

    # Collect file IDs or links
    proof_item = None
    if update.message.photo:
        proof_item = update.message.photo[-1].file_id
    elif update.message.video:
        proof_item = update.message.video.file_id
    elif update.message.text:
        proof_item = update.message.text

    if proof_item:
        applicant.proof_of_work.append(proof_item)
        applicant_storage.update(applicant)
        await update.message.reply_text("Added! Send more or type 'done' to continue.")

    return ApplicationState.ASK_PROOF_OF_WORK


async def finalize_application(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Finalize and submit the application."""
    user_id = update.effective_user.id
    applicant = applicant_storage.get(user_id)

    applicant.completed_at = datetime.now()
    applicant.status = "completed"

    # Run AI evaluation
    await update.message.reply_text("Processing your application... 🤖")

    rating, feedback = ai_evaluator.evaluate(applicant)
    applicant.ai_rating = rating
    applicant.ai_feedback = feedback

    applicant_storage.update(applicant)

    # Save to Google Sheets
    sheets_service.save_applicant(applicant)

    # Notify admin
    await notify_admin_new_applicant(context, applicant)

    await update.message.reply_text(
        "✅ Thank you for applying!\n\n"
        "We've received your application and will review it carefully.\n"
        "We'll be in touch if your profile matches what we're looking for.\n\n"
        "Good luck! 🍀"
    )

    # Clean up session
    applicant_storage.delete(user_id)
    context.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the application."""
    user_id = update.effective_user.id
    applicant_storage.delete(user_id)
    context.user_data.clear()

    await update.message.reply_text(
        "Application cancelled. Feel free to /start again when you're ready!"
    )
    return ConversationHandler.END


def get_application_conversation_handler() -> ConversationHandler:
    """Build and return the application conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ApplicationState.POSITION_SELECT: [
                CallbackQueryHandler(select_position, pattern="^pos_")
            ],
            ApplicationState.ASKING_QUESTIONS: [
                CallbackQueryHandler(handle_question_answer, pattern="^choice_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question_answer),
            ],
            ApplicationState.ASK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)
            ],
            ApplicationState.ASK_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)
            ],
            ApplicationState.ASK_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
            ApplicationState.ASK_SOCIALS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_socials)
            ],
            ApplicationState.ASK_CV: [
                MessageHandler(filters.Document.PDF, handle_cv)
            ],
            ApplicationState.ASK_PROOF_OF_WORK: [
                MessageHandler(
                    filters.TEXT | filters.PHOTO | filters.VIDEO,
                    handle_proof_of_work
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
