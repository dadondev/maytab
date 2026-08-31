from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_settings_markup(user):
    auto_text = "✅ Avtomatik yuborish: yoqilgan" if user.auto_send else "❌ Avtomatik yuborish: o'chirilgan"
    school_name = getattr(user, "school_name", None) or "Maktab tanlanmagan"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=auto_text, callback_data="toggle_setting:auto_send")],
        [InlineKeyboardButton(text=f"🏫 Maktab: {school_name}", callback_data="change_school")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_menu")],
    ])