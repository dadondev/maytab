from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.queries import get_group


def get_my_tables_markup(tables: list[int]):
    markup = InlineKeyboardBuilder()
    for class_id in tables:
        group = get_group(class_id)
        label = group.name if group else f"Jadval #{class_id}"
        markup.button(text=f"📅 {label}", callback_data=f"show_table:{class_id}")
        markup.button(text="🗑 O'chirish", callback_data=f"remove_table:{class_id}")
    markup.adjust(2)
    markup.row(
        InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_menu"),
        InlineKeyboardButton(text="➕ Jadval qo'shish", callback_data="add_user_table"),
    )
    return markup.as_markup()
