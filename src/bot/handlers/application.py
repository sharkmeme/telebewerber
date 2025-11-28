"""
Main application conversation handler.

Handles the applicant flow from greeting to submission.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputFile,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot.conversations.states import ApplicationState
from config.settings import settings
from models.applicant import Applicant
from models.question_config import POSITIONS
from services.storage import applicant_storage
from services.sheets import sheets_service
from bot.handlers.admin import notify_admin_new_applicant

logger = logging.getLogger(__name__)


# Helper: build inline keyboard for positions
def build_positions_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    for pid, pdata in POSITIONS.items():
        keyboard.append([InlineKeyboardButton(pdata["name"], callback_data=f"pos_{pid}")])
    return InlineKeyboardMarkup(keyboard)


# Helper: navigation buttons (Skip/Back)
def nav_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Skip ⏭️", callback_data="skip_current")],
        [InlineKeyboardButton("Back ⬅️", callback_data="go_back")]
    ])


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user

    # Create new applicant session
    applicant = Applicant(
        user_id=user.id,
        telegram_username=user.username,
    )
    applicant_storage.save(applicant)

    greet = (
        "Welcome! 👋\n\n"
        "Thank you for applying at Bunny Honey Club.\n\n"
        "Our hiring process is simple:\n"
        "1) Apply using this bot\n"
        "2) You may receive a short quiz\n"
        "3) We evaluate your answers\n"
        "4) Selected applicants receive an interview invitation\n\n"
        f"Homepage: {settings.HOMEPAGE_URL}\n\n"
        "Please select the position you are applying for:"
    )

    await update.message.reply_text(greet, reply_markup=build_positions_keyboard())
    return ApplicationState.SELECT_POSITION


# Handle position click
async def position_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    applicant = applicant_storage.get(query.from_user.id)
    if not applicant:
        await query.message.reply_text("Session expired. Please /start again.")
        return ConversationHandler.END

    # Extract position id
    pos_raw = query.data.replace("pos_", "", 1)
    applicant.position = pos_raw

    if pos_raw == "other":
        await query.message.reply_text("Please type the job position you want to apply for:")
        return ApplicationState.OTHER_POSITION_TEXT

    # Load role questions
    applicant.answers = {}
    await ask_next_position_question(update, context, applicant)
    return ApplicationState.POSITION_QUESTIONS


# Handle custom "Other" position text
async def handle_other_position_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    applicant = applicant_storage.get(update.effective_user.id)
    applicant.custom_position = update.message.text.strip()

    applicant.answers = {}
    await ask_next_position_question(update, context, applicant)
    return ApplicationState.POSITION_QUESTIONS


# Helper: ask next question
def get_question_list(applicant: Applicant) -> List[Dict[str, Any]]:
    if applicant.position == "other":
        return []
    return POSITIONS[applicant.position]["questions"]


def get_next_question(applicant: Applicant) -> Optional[Dict[str, Any]]:
    questions = get_question_list(applicant)
    answered = len(applicant.answers)
    if answered >= len(questions):
        return None
    return questions[answered]


async def ask_next_position_question(update_or_query, context, applicant: Applicant):
    applicant.history.append("POSITION_QUESTIONS")
    question = get_next_question(applicant)
    if not question:
        # Move to personal info
        await update_or_query.effective_message.reply_text("What is your full name?", reply_markup=nav_keyboard())
        context.user_data["state"] = ApplicationState.COLLECT_NAME
        return ApplicationState.COLLECT_NAME

    qtext = question["q"]
    qtype = question["type"]

    if qtype == "text":
        await update_or_query.effective_message.reply_text(qtext)
    elif qtype == "choice":
        buttons = [[InlineKeyboardButton(opt, callback_data=f"ans_{opt}")] for opt in question["options"]]
        await update_or_query.effective_message.reply_text(qtext, reply_markup=InlineKeyboardMarkup(buttons))
    elif qtype == "multi_choice":
        buttons = [
            [InlineKeyboardButton(f"[ ] {opt}", callback_data=f"mul_{opt}")]
            for opt in question["options"]
        ]
        buttons.append([InlineKeyboardButton("Done ✅", callback_data="mul_done")])
        note = "\n\n<i>💡 Note: You can select multiple answers</i>"
        await update_or_query.effective_message.reply_text(qtext + note, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))

    context.user_data["state"] = ApplicationState.POSITION_QUESTIONS
    return ApplicationState.POSITION_QUESTIONS


# Handle answers
async def handle_text_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    applicant = applicant_storage.get(update.effective_user.id)
    q = get_next_question(applicant)
    applicant.answers[q["id"]] = update.message.text.strip()

    # Ask next question
    if get_next_question(applicant):
        await ask_next_position_question(update, context, applicant)
        return ApplicationState.POSITION_QUESTIONS

    # Move to personal info
    await update.message.reply_text("What is your full name?", reply_markup=nav_keyboard())
    return ApplicationState.COLLECT_NAME


async def handle_choice_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    applicant = applicant_storage.get(query.from_user.id)
    q = get_next_question(applicant)
    choice = query.data.replace("ans_", "", 1)
    applicant.answers[q["id"]] = choice

    # Ask next
    if get_next_question(applicant):
        await ask_next_position_question(update, context, applicant)
        return ApplicationState.POSITION_QUESTIONS

    await query.message.reply_text("What is your full name?", reply_markup=nav_keyboard())
    return ApplicationState.COLLECT_NAME


async def handle_multi_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    applicant = applicant_storage.get(query.from_user.id)

    # Find the current multi-choice question in progress
    questions = get_question_list(applicant)
    q = None
    for question in questions:
        if question["type"] == "multi_choice" and question["id"] in applicant.answers and isinstance(applicant.answers[question["id"]], list):
            q = question
            break

    # If no in-progress multi-choice found, this must be the first click
    if not q:
        q = get_next_question(applicant)
        if not q or q["type"] != "multi_choice":
            await query.answer("No active multi-choice question.")
            context.user_data["state"] = ApplicationState.POSITION_QUESTIONS
            return ApplicationState.POSITION_QUESTIONS
        # Initialize answer array
        applicant.answers[q["id"]] = []

    if query.data == "mul_done":
        # Completed multi-selection - move to next question
        return await ask_next_position_question(update, context, applicant)

    # Add the selected option
    choice = query.data.replace("mul_", "", 1)
    if choice not in applicant.answers[q["id"]]:
        applicant.answers[q["id"]].append(choice)

    await query.answer("Added")
    context.user_data["state"] = ApplicationState.POSITION_QUESTIONS
    return ApplicationState.POSITION_QUESTIONS


# Skip current question
async def skip_current(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Skipped.")
    applicant = applicant_storage.get(query.from_user.id)
    state = context.user_data.get("state")

    # POSITION QUESTIONS
    if state == ApplicationState.POSITION_QUESTIONS:
        q = get_next_question(applicant)
        if q:
            applicant.answers[q["id"]] = ""
        return await ask_next_position_question(update, context, applicant)

    # NAME
    if state == ApplicationState.COLLECT_NAME:
        applicant.full_name = ""
        await query.message.reply_text(
            "Your email address:", reply_markup=nav_keyboard()
        )
        context.user_data["state"] = ApplicationState.COLLECT_EMAIL
        return ApplicationState.COLLECT_EMAIL

    # EMAIL
    if state == ApplicationState.COLLECT_EMAIL:
        applicant.email = ""
        await query.message.reply_text(
            "Your phone number:", reply_markup=nav_keyboard()
        )
        context.user_data["state"] = ApplicationState.COLLECT_PHONE
        return ApplicationState.COLLECT_PHONE

    # PHONE
    if state == ApplicationState.COLLECT_PHONE:
        applicant.phone = ""
        await query.message.reply_text(
            "Your social media links or usernames:", reply_markup=nav_keyboard()
        )
        context.user_data["state"] = ApplicationState.COLLECT_SOCIALS
        return ApplicationState.COLLECT_SOCIALS

    # SOCIALS
    if state == ApplicationState.COLLECT_SOCIALS:
        applicant.socials = ""
        await query.message.reply_text(
            "Please upload your CV as a PDF file.\nOr tap Skip.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Skip CV", callback_data="skip_cv")],
                [InlineKeyboardButton("Back", callback_data="go_back")]
            ])
        )
        context.user_data["state"] = ApplicationState.UPLOAD_CV
        return ApplicationState.UPLOAD_CV

    return ApplicationState.SELECT_POSITION


# Back navigation
async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    applicant = applicant_storage.get(query.from_user.id)

    if not applicant.history:
        await query.message.reply_text("Cannot go back further.")
        context.user_data["state"] = ApplicationState.SELECT_POSITION
        return ApplicationState.SELECT_POSITION

    last = applicant.history.pop()

    if last == "POSITION_QUESTIONS":
        return await ask_next_position_question(update, context, applicant)

    if last == "COLLECT_NAME":
        await query.message.reply_text("What is your full name?", reply_markup=nav_keyboard())
        context.user_data["state"] = ApplicationState.COLLECT_NAME
        return ApplicationState.COLLECT_NAME

    if last == "COLLECT_EMAIL":
        await query.message.reply_text("Your email address:", reply_markup=nav_keyboard())
        context.user_data["state"] = ApplicationState.COLLECT_EMAIL
        return ApplicationState.COLLECT_EMAIL

    if last == "COLLECT_PHONE":
        await query.message.reply_text("Your phone number:", reply_markup=nav_keyboard())
        context.user_data["state"] = ApplicationState.COLLECT_PHONE
        return ApplicationState.COLLECT_PHONE

    if last == "COLLECT_SOCIALS":
        await query.message.reply_text("Your social media links or usernames:", reply_markup=nav_keyboard())
        context.user_data["state"] = ApplicationState.COLLECT_SOCIALS
        return ApplicationState.COLLECT_SOCIALS

    context.user_data["state"] = ApplicationState.SELECT_POSITION
    return ApplicationState.SELECT_POSITION


# Skip CV upload
async def skip_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    applicant = applicant_storage.get(query.from_user.id)
    applicant.cv_file_id = None

    await query.message.reply_text(
        'Please upload portfolio files.\nWhen done, type "done".'
    )
    return ApplicationState.UPLOAD_PORTFOLIO


# Personal info
async def handle_name(update: Update, context):
    applicant = applicant_storage.get(update.effective_user.id)
    applicant.history.append("COLLECT_NAME")
    applicant.full_name = update.message.text.strip()
    context.user_data["state"] = ApplicationState.COLLECT_EMAIL
    await update.message.reply_text("Your email address:", reply_markup=nav_keyboard())
    return ApplicationState.COLLECT_EMAIL


async def handle_email(update: Update, context):
    applicant = applicant_storage.get(update.effective_user.id)
    applicant.history.append("COLLECT_EMAIL")
    applicant.email = update.message.text.strip()
    context.user_data["state"] = ApplicationState.COLLECT_PHONE
    await update.message.reply_text("Your phone number:", reply_markup=nav_keyboard())
    return ApplicationState.COLLECT_PHONE


async def handle_phone(update: Update, context):
    applicant = applicant_storage.get(update.effective_user.id)
    applicant.history.append("COLLECT_PHONE")
    applicant.phone = update.message.text.strip()
    context.user_data["state"] = ApplicationState.COLLECT_SOCIALS
    await update.message.reply_text("Your social media links or usernames:", reply_markup=nav_keyboard())
    return ApplicationState.COLLECT_SOCIALS


async def handle_socials(update: Update, context):
    applicant = applicant_storage.get(update.effective_user.id)
    applicant.history.append("COLLECT_SOCIALS")
    applicant.socials = update.message.text.strip()
    context.user_data["state"] = ApplicationState.UPLOAD_CV
    await update.message.reply_text(
        "Please upload your CV as a PDF file.\n\nIf you don't have a CV, tap Skip.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Skip CV", callback_data="skip_cv")]
        ])
    )
    return ApplicationState.UPLOAD_CV


# Handle CV upload
async def handle_cv(update: Update, context):
    applicant = applicant_storage.get(update.effective_user.id)

    if not update.message.document:
        await update.message.reply_text("Please upload a **PDF CV**.")
        return ApplicationState.UPLOAD_CV

    doc = update.message.document
    if doc.mime_type != "application/pdf":
        await update.message.reply_text("Only PDF files are accepted. Upload your CV again.")
        return ApplicationState.UPLOAD_CV

    # Get Telegram file URL instead of storing file_id
    tg_file = await context.bot.get_file(doc.file_id)
    cv_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{tg_file.file_path}"
    applicant.cv_file_id = cv_url

    # Portfolio step
    await update.message.reply_text(
        "Please upload portfolio files (images, videos, documents, or links).\n"
        "Send as many as you like.\n"
        'When done, type "done".'
    )
    return ApplicationState.UPLOAD_PORTFOLIO


# Handle portfolio
async def handle_portfolio(update: Update, context):
    applicant = applicant_storage.get(update.effective_user.id)

    if update.message.text and update.message.text.lower().strip() == "done":
        # Move to confirmation
        summary = build_summary(applicant)
        await update.message.reply_html(summary)
        await update.message.reply_text("Submit application? (yes / no)")
        return ApplicationState.CONFIRM_SUBMIT

    # Document or media - convert to Telegram file URLs
    file_url = None
    if update.message.document:
        tg_file = await context.bot.get_file(update.message.document.file_id)
        file_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{tg_file.file_path}"
    elif update.message.photo:
        tg_file = await context.bot.get_file(update.message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{tg_file.file_path}"
    elif update.message.video:
        tg_file = await context.bot.get_file(update.message.video.file_id)
        file_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{tg_file.file_path}"
    elif update.message.text:
        # User-provided text link (not a file upload)
        file_url = update.message.text.strip()

    if file_url:
        applicant.portfolio_files.append(file_url)
        await update.message.reply_text("Added. Send more or type 'done'.")
    else:
        await update.message.reply_text("Unsupported file type. Send a file or a link.")
    return ApplicationState.UPLOAD_PORTFOLIO


# Summary builder
def build_summary(applicant: Applicant) -> str:
    pos_name = (
        applicant.custom_position
        if applicant.position == "other"
        else POSITIONS[applicant.position]["name"]
    )

    lines = [f"<b>Position:</b> {pos_name}"]

    lines.append("\n<b>Answers:</b>")
    for qid, ans in applicant.answers.items():
        lines.append(f"- <b>{qid}</b>: {ans}")

    lines.append("\n<b>Personal Info</b>")
    lines.append(f"Name: {applicant.full_name}")
    lines.append(f"Email: {applicant.email}")
    lines.append(f"Phone: {applicant.phone}")
    lines.append(f"Socials: {applicant.socials}")

    lines.append("\n<b>Files</b>")
    lines.append(f"CV: {'Uploaded' if applicant.cv_file_id else 'Missing'}")
    lines.append(f"Portfolio files: {len(applicant.portfolio_files)}")

    return "\n".join(lines)


# Final confirmation
async def handle_confirmation(update: Update, context):
    applicant = applicant_storage.get(update.effective_user.id)
    decision = update.message.text.lower().strip()

    if decision not in ["yes", "y"]:
        await update.message.reply_text("Application cancelled.")
        return ConversationHandler.END

    # Save to Google Sheets
    row_index = sheets_service.append_applicant_row(applicant)
    applicant.sheet_row_index = row_index
    applicant.status = "submitted"

    # Notify admin
    await notify_admin_new_applicant(context, applicant)

    await update.message.reply_text("Application submitted. Thank you!")
    return ConversationHandler.END


# Conversation handler builder
def get_application_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ApplicationState.SELECT_POSITION: [CallbackQueryHandler(position_selected)],
            ApplicationState.OTHER_POSITION_TEXT: [MessageHandler(filters.TEXT, handle_other_position_text)],
            ApplicationState.POSITION_QUESTIONS: [
                # TEXT answers
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_answer),

                # Multi-choice DONE FIRST
                CallbackQueryHandler(handle_multi_choice, pattern="^mul_done$"),

                # Multi-choice options
                CallbackQueryHandler(handle_multi_choice, pattern="^mul_"),

                # Single-choice
                CallbackQueryHandler(handle_choice_answer, pattern="^ans_"),

                # Navigation
                CallbackQueryHandler(skip_current, pattern="^skip_current$"),
                CallbackQueryHandler(go_back, pattern="^go_back$"),
            ],
            ApplicationState.COLLECT_NAME: [
                MessageHandler(filters.TEXT, handle_name),
                CallbackQueryHandler(skip_current, pattern="^skip_current$"),
                CallbackQueryHandler(go_back, pattern="^go_back$"),
            ],
            ApplicationState.COLLECT_EMAIL: [
                MessageHandler(filters.TEXT, handle_email),
                CallbackQueryHandler(skip_current, pattern="^skip_current$"),
                CallbackQueryHandler(go_back, pattern="^go_back$"),
            ],
            ApplicationState.COLLECT_PHONE: [
                MessageHandler(filters.TEXT, handle_phone),
                CallbackQueryHandler(skip_current, pattern="^skip_current$"),
                CallbackQueryHandler(go_back, pattern="^go_back$"),
            ],
            ApplicationState.COLLECT_SOCIALS: [
                MessageHandler(filters.TEXT, handle_socials),
                CallbackQueryHandler(skip_current, pattern="^skip_current$"),
                CallbackQueryHandler(go_back, pattern="^go_back$"),
            ],
            ApplicationState.UPLOAD_CV: [
                MessageHandler(filters.Document.ALL, handle_cv),
                CallbackQueryHandler(skip_cv, pattern="^skip_cv$"),
            ],
            ApplicationState.UPLOAD_PORTFOLIO: [
                MessageHandler(filters.ALL, handle_portfolio)
            ],
            ApplicationState.CONFIRM_SUBMIT: [MessageHandler(filters.TEXT, handle_confirmation)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
