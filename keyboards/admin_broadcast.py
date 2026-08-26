from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_broadcast_confirm_markup():
    markup = InlineKeyboardBuilder()
    markup.button(text="✅ Yuborish", callback_data="broadcast:send")
    markup.button(text="↩️ Qayta yozish", callback_data="broadcast:rewrite")
    markup.button(text="❌ Bekor qilish", callback_data="back_admin_menu")
    markup.adjust(2)
    return markup.as_markup()