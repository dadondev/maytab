from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

register_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Ro'yhatdan o'tish", callback_data="register")]])

register_phone_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Telefon raqamingizni yuboring", request_contact=True)]], resize_keyboard=True)

register_auto_send_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Ha, avtomatik yuboring ✅"), KeyboardButton(text="❌ Yo'q, avtomatik yubormang ❌")]], resize_keyboard=True)
