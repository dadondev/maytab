from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admit_task_markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="O'zgartirish", callback_data=f"admit_task_date:edit"),
        InlineKeyboardButton(text="Tastiqlayman", callback_data=f"admit_task_date:accept")
    ]])