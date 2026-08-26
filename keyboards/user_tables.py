from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

DAY_BUTTONS = [
    ("🟡 Dushanba", "monday"),
    ("🔴 Seshanba", "tuesday"),
    ("🟢 Chorshanba", "wednesday"),
    ("🟣 Payshanba", "thursday"),
    ("🔵 Juma", "friday"),
    ("🟠 Shanba", "saturday"),
]


def get_grades_markup(grades, source: str = "general", back_callback: str = "back_menu"):
    markup = InlineKeyboardBuilder()
    for grade in grades:
        markup.button(text=f"📚 {grade.grade}-sinf", callback_data=f"select_grade:{source}:{grade.id}")
    markup.adjust(2)
    markup.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback))
    return markup.as_markup()


def get_groups_markup(groups, back_callback: str = "general_tables"):
    markup = InlineKeyboardBuilder()
    for group in groups:
        markup.button(text=f"🏫 {group.name}", callback_data=f"show_table:{group.id}")
    markup.adjust(2)
    markup.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback))
    return markup.as_markup()


def get_table_markup(group_id: int, selected: bool = False, back_callback: str = "general_tables"):
    markup = InlineKeyboardBuilder()
    if selected:
        markup.button(text="🗑 O'chirish", callback_data=f"remove_table:{group_id}")
    else:
        markup.button(text="➕ Mening jadvallarimga qo'shish", callback_data=f"add_table:{group_id}")
    markup.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback))
    return markup.as_markup()


def get_table_days_markup(group_id: int, back_callback: str = "general_tables"):
    """Show day buttons for a class schedule."""
    markup = InlineKeyboardBuilder()
    for label, day_key in DAY_BUTTONS:
        markup.button(text=label, callback_data=f"show_day:{group_id}:{day_key}")
    markup.adjust(2)
    markup.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback))
    return markup.as_markup()