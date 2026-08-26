from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

survey_save_file_markup = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="Ha", callback_data="save_file:yes"),
    InlineKeyboardButton(text="Yo'q", callback_data="save_file:no")
]])

