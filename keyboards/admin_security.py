from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.queries import get_all_guards


def get_security_menu_markup():
    markup = InlineKeyboardBuilder()
    markup.button(text="🛡️ Qo'riqchilar ro'yxati", callback_data="security:guards")
    markup.adjust(1)
    markup.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin_menu"))
    return markup.as_markup()


def get_security_user_list_markup(list_type: str, back_callback: str):
    markup = InlineKeyboardBuilder()
    rows = get_all_guards()
    for user in rows:
        markup.button(
            text=f"🛡️ {user.name}",
            callback_data=f"security:user:{user.id}:{list_type}",
        )
    markup.adjust(1)
    markup.row(
        InlineKeyboardButton(
            text="➕ Qo'riqchi qo'shish",
            callback_data=f"security:add_guard",
        ),
        InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback),
    )
    return markup.as_markup()


def get_security_user_actions_markup(user_id: int, list_type: str):
    markup = InlineKeyboardBuilder()
    markup.button(
        text="🗑 Qo'riqchilikdan olib tashlash",
        callback_data=f"security:demote:{user_id}:{list_type}",
    )
    markup.button(
        text="🚫 Foydalanuvchini o'chirish",
        callback_data=f"security:delete:{user_id}:{list_type}",
    )
    markup.adjust(1)
    markup.row(
        InlineKeyboardButton(
            text="⬅️ Ortga",
            callback_data=f"security:{list_type}",
        )
    )
    return markup.as_markup()