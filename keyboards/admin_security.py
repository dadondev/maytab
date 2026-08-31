from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.queries import get_all_guards, get_all_school_counselors


def get_security_menu_markup():
    markup = InlineKeyboardBuilder()
    markup.button(text="🛡️ Qo'riqchilar ro'yxati", callback_data="security:guards")
    markup.button(text="🎓 Maktab maslahatchilari", callback_data="security:school_counselors")
    markup.adjust(1)
    markup.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin_menu"))
    return markup.as_markup()


def get_security_user_list_markup(list_type: str, back_callback: str):
    markup = InlineKeyboardBuilder()
    rows = get_all_guards() if list_type == "guards" else get_all_school_counselors()
    for user in rows:
        prefix = "🛡️" if list_type == "guards" else "🎓"
        markup.button(
            text=f"{prefix} {user.chat_id}",
            callback_data=f"security:user:{user.id}:{list_type}",
        )
    markup.adjust(1)
    if list_type == "guards":
        markup.row(
            InlineKeyboardButton(
                text="➕ Qo'riqchi qo'shish",
                callback_data="security:add_guard",
            ),
            InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback),
        )
    else:
        markup.row(
            InlineKeyboardButton(
                text="➕ Maslahatchi qo'shish",
                callback_data="security:add_school_counselor",
            ),
            InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback),
        )
    return markup.as_markup()


def get_security_user_actions_markup(user_id: int, list_type: str):
    role_label = "Qo'riqchilikdan olib tashlash" if list_type == "guards" else "Maslahatchilikdan olib tashlash"
    markup = InlineKeyboardBuilder()
    markup.button(
        text=f"🗑 {role_label}",
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