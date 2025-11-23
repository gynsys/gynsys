# features/share_link/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_share_link_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for returning to patient main menu."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔙 Volver", callback_data="patient_main_menu"),
            ]
        ]
    )


def get_doctor_share_link_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for returning to doctor main menu."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔙 Volver", callback_data="doctor_main_menu"),
            ]
        ]
    )

