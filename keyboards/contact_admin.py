from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_contact_admin_back_markup():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Ortga", callback_data="contact_admin_back")
    ]])


def get_admin_reply_markup(user_chat_id: int) -> InlineKeyboardMarkup:
    """Keyboard for the admin to reply to a user's contact request.

    The user's chat ID is embedded in the callback_data so the admin can
    directly reply to that user.
    """
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="↩️ Javob berish",
            callback_data=f"reply_user:{user_chat_id}",
        )
    ]])


def get_admin_reply_back_markup() -> InlineKeyboardMarkup:
    """Back/cancel keyboard for the admin reply flow (returns to admin menu)."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❌ Bekor qilish ❌", callback_data="return_admin_menu")
    ]])