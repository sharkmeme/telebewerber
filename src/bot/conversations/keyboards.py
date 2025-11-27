"""
Telegram keyboard layouts and builders.
"""

from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from models.position import get_all_positions


def get_positions_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with available positions."""
    positions = get_all_positions()
    keyboard = []

    for position in positions:
        keyboard.append([
            InlineKeyboardButton(position.name, callback_data=f"pos_{position.id}")
        ])

    return InlineKeyboardMarkup(keyboard)


def get_choice_keyboard(choices: List[str]) -> InlineKeyboardMarkup:
    """Create keyboard for multiple choice questions."""
    keyboard = []

    for choice in choices:
        keyboard.append([
            InlineKeyboardButton(choice, callback_data=f"choice_{choice}")
        ])

    return InlineKeyboardMarkup(keyboard)


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with skip button."""
    keyboard = [[InlineKeyboardButton("Skip", callback_data="skip")]]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for confirmation."""
    keyboard = [
        [InlineKeyboardButton("✅ Submit", callback_data="confirm_yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="confirm_no")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_action_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for admin actions on applicant."""
    keyboard = [
        [InlineKeyboardButton("📝 Send Quiz", callback_data=f"admin_quiz_{user_id}")],
        [InlineKeyboardButton("📅 Send Interview Link", callback_data=f"admin_interview_{user_id}")],
        [InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{user_id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{user_id}")],
    ]
    return InlineKeyboardMarkup(keyboard)
