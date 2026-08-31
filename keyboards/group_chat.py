from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.queries import get_grades, get_groups

DAY_BUTTONS = [
    ("🟡 Dushanba", "monday"),
    ("🔴 Seshanba", "tuesday"),
    ("🟢 Chorshanba", "wednesday"),
    ("🟣 Payshanba", "thursday"),
    ("🔵 Juma", "friday"),
    ("🟠 Shanba", "saturday"),
]


def get_group_grades_markup():
    markup = InlineKeyboardBuilder()
    for grade in get_grades():
        markup.button(
            text=f"{grade.grade}-sinf",
            callback_data=f"groupchat:grade:{grade.id}",
        )
    markup.adjust(2)
    return markup.as_markup()


def get_group_classes_markup(grade_id: int):
    markup = InlineKeyboardBuilder()
    for group in get_groups(grade_id):
        markup.button(
            text=group.name,
            callback_data=f"groupchat:select:{group.id}",
        )
    markup.adjust(2)
    markup.row(
        InlineKeyboardButton(text="⬅️ Ortga", callback_data="groupchat:grades")
    )
    return markup.as_markup()


def get_group_start_markup(group_id: int | None = None):
    markup = InlineKeyboardBuilder()
    for label, day_key in DAY_BUTTONS:
        markup.button(text=label, callback_data=f"show_day:{group_id}:{day_key}")
    markup.adjust(2)
    markup.row(
        InlineKeyboardButton(text="🔄 Jadvalni o'zgartirish", callback_data="groupchat:grades"),
        InlineKeyboardButton(text="📅 To'liq jadval", callback_data=f"show_table:{group_id}"),
    )
    return markup.as_markup()