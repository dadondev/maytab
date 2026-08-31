from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

menu_markup = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="📅 Mening jadvallarim 📅", callback_data="my_tables")
], [
    InlineKeyboardButton(text="📋 Umumiy jadval 📋", callback_data="general_tables")
], [
    InlineKeyboardButton(text="⚙️ Sozlamalar ⚙️", callback_data="settings")
]])

group_menu_markup = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="📋 Umumiy jadval 📋", callback_data="general_tables")
]])
