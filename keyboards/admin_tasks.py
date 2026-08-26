from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_tasks_list_markup(tasks):
    markup = InlineKeyboardBuilder()
    for task in tasks:
        when = task.date.strftime("%d.%m.%Y %H:%M") if task.date else "—"
        status_emoji = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
        }.get(task.status, "❓")
        markup.button(
            text=f"{status_emoji} {when}",
            callback_data=f"task:show:{task.id}",
        )
    markup.adjust(1)
    markup.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin_menu"))
    return markup.as_markup()


def get_task_actions_markup(task_id: int):
    markup = InlineKeyboardBuilder()
    markup.button(text="✅ Yakunlash va o'chirish", callback_data=f"task:finish:{task_id}")
    markup.button(text="🗑 O'chirish", callback_data=f"task:delete:{task_id}")
    markup.adjust(1)
    markup.row(InlineKeyboardButton(text="⬅️ Vazifalar", callback_data="tasks"))
    return markup.as_markup()