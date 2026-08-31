from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup

admin_menu_markup = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📥 Jadvalni yuklash 📥", callback_data="upload_table")
    ],
    [
        InlineKeyboardButton(text="📬 Xabar yuborish 📬", callback_data="send_message")
    ],
    [
        InlineKeyboardButton(text="🏫 Maktablar 🏫", callback_data="schools")
    ],
    [
        InlineKeyboardButton(text="📋 Vazifalar 📋", callback_data="tasks")
    ],
    [
        InlineKeyboardButton(text="👮‍♀️ Qo'riqchilar 👮‍♀️", callback_data="security")
    ]
])

back_admin_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish ❌", callback_data="back_admin_menu")]])