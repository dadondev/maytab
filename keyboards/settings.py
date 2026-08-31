from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_settings_markup(user):
    auto_text = "✅ Avtomatik yuborish: yoqilgan" if user.auto_send else "❌ Avtomatik yuborish: o'chirilgan"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=auto_text, callback_data="toggle_setting:auto_send")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_menu")],
    ])