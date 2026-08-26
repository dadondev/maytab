from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.queries import get_grades, get_groups


def get_guard_menu_markup():
    markup = InlineKeyboardBuilder()
    markup.button(text="📅 Ertangi jadval", callback_data="guard:tomorrow")
    markup.button(text="📋 Sinf jadvalni ko'rish", callback_data="guard:grades")
    markup.adjust(2)
    markup.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_menu"))
    return markup.as_markup()


def get_guard_grades_markup(back_callback: str = "guard:menu"):
    markup = InlineKeyboardBuilder()
    for grade in get_grades():
        markup.button(
            text=f"{grade.grade}-sinf",
            callback_data=f"guard:grade:{grade.id}",
        )
    markup.adjust(2)
    markup.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback))
    return markup.as_markup()


def get_guard_groups_markup(grade_id: int, back_callback: str = "guard:grades"):
    markup = InlineKeyboardBuilder()
    for group in get_groups(grade_id):
        markup.button(
            text=group.name,
            callback_data=f"guard:show:{group.id}",
        )
    markup.adjust(2)
    markup.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback))
    return markup.as_markup()