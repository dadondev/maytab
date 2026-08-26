from aiogram import Router, F
from aiogram.types import ChatMemberUpdated, CallbackQuery

from keyboards.group_chat import (
    get_group_grades_markup,
    get_group_classes_markup,
)
from db.queries import get_group, set_group_chat

group_router = Router()


@group_router.my_chat_member()
async def on_bot_added_to_group(event: ChatMemberUpdated):
    """When the bot is added to a group, ask which class to bind."""
    if event.new_chat_member.status != "member":
        return
    if event.new_chat_member.user.id != event.bot.id:
        return

    chat = event.chat
    await event.bot.send_message(
        chat_id=chat.id,
        text=(
            "Assalomu alaykum! Ushbu guruhga qaysi sinf jadvalini "
            "yuborishni xohlasiz? Sinfni tanlang:"
        ),
        reply_markup=get_group_grades_markup(),
    )


@group_router.callback_query(F.data == "groupchat:grades")
async def groupchat_grades_handler(cb: CallbackQuery):
    await cb.message.edit_text(
        "Sinfni tanlang:", reply_markup=get_group_grades_markup()
    )


@group_router.callback_query(F.data.regexp(r"^groupchat:grade:\d+$"))
async def groupchat_grade_handler(cb: CallbackQuery):
    grade_id = int(cb.data.split(":")[2])
    await cb.message.edit_text(
        "Guruhni tanlang:", reply_markup=get_group_classes_markup(grade_id)
    )


@group_router.callback_query(F.data.regexp(r"^groupchat:select:\d+$"))
async def groupchat_select_handler(cb: CallbackQuery):
    group_id = int(cb.data.split(":")[2])
    group = get_group(group_id)
    if group is None:
        await cb.answer("Jadval topilmadi.", show_alert=True)
        return

    chat_id = cb.message.chat.id
    title = cb.message.chat.title
    set_group_chat(chat_id, group_id, title)

    await cb.message.edit_text(
        f"✅ Ushbu guruhga <b>{group.name}</b> sinf jadvali biriktildi!\n\n"
        "Endi bot har kuni ertangi jadvalni soat 16:00 da va "
        "bugungi jadvalni soat 05:00 da yuboradi.",
        parse_mode="HTML",
    )