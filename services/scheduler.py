import asyncio
import os
from datetime import datetime, timedelta, timezone

# Uzbekistan is UTC+5 (no DST), so a fixed offset is correct.
UZ_TZ = timezone(timedelta(hours=5))


def _now_uz() -> datetime:
    """Return the current time in Uzbekistan (UTC+5)."""
    return datetime.now(UZ_TZ)

from bot.bootstrap import bot
from db.queries import (
    get_all_users,
    get_group,
    get_all_group_chats,
    get_all_admins,
    get_tasks_due_today,
    get_tasks_due_now,
    upload_table,
    update_task_status,
    delete_completed_tasks,
)
from db.schemas import User


def _format_table(group, day_key: str | None = None) -> str:
    """Format a group's timetable into a readable message.

    If `day_key` is given, only that day is shown (used for daily sends).
    Otherwise the full weekly schedule is shown.
    """
    day_names = {
        "monday": "Dushanba", "tuesday": "Seshanba", "wednesday": "Chorshanba",
        "thursday": "Payshanba", "friday": "Juma", "saturday": "Shanba",
    }
    today = _now_uz().strftime("%A").lower()
    lines = [f"📅 {group.name} guruhi jadvali"]
    for day, name in day_names.items():
        subjects = group.table.get(day, []) if group.table else []
        if not subjects:
            continue
        if day_key is not None and day != day_key:
            continue
        marker = "📍" if day == today else "▪️"
        lines.append(
            f"\n{marker} {name}:\n" + "\n".join(
                f"{index}. {subject}" for index, subject in enumerate(subjects, 1)
            )
        )
    return "\n".join(lines)


async def send_daily_timetables():
    """Send today's timetable to all users with auto_send enabled."""
    users = get_all_users(only_active=True)
    for user in users:
        tables = user.tables or []
        for group_id in tables:
            group = get_group(group_id)
            if group is None or not group.table:
                continue
            try:
                await bot.send_message(
                    chat_id=user.chat_id, text=_format_table(group)
                )
            except Exception:
                continue
            await asyncio.sleep(0.05)  # be polite to Telegram rate limits


async def send_tomorrow_to_groups():
    """Send tomorrow's schedule to every bound group chat."""
    day_key = (_now_uz() + timedelta(days=1)).strftime("%A").lower()
    for gc in get_all_group_chats():
        group = get_group(gc.group_id)
        if group is None or not group.table:
            continue
        subjects = group.table.get(day_key, []) if group.table else []
        if not subjects:
            continue
        text = (
            f"📅 Ertangi ({day_key}) jadvali — {group.name}:\n\n"
            + "\n".join(
                f"{index}. {subject}" for index, subject in enumerate(subjects, 1)
            )
        )
        try:
            await bot.send_message(chat_id=gc.chat_id, text=text)
        except Exception:
            continue
        await asyncio.sleep(0.05)


def _format_tomorrow_for_user(group) -> str:
    """Format tomorrow's schedule for a single class."""
    day_key = (_now_uz() + timedelta(days=1)).strftime("%A").lower()
    day_names = {
        "monday": "Dushanba", "tuesday": "Seshanba", "wednesday": "Chorshanba",
        "thursday": "Payshanba", "friday": "Juma", "saturday": "Shanba",
    }
    subjects = group.table.get(day_key, []) if group.table else []
    name = day_names.get(day_key, day_key)
    if not subjects:
        return f"📅 {group.name} — Ertangi ({name}): bo'sh (dars yo'q)"
    lines = [f"📅 {group.name} — Ertangi ({name}):"]
    lines.append("\n".join(f"{index}. {subject}" for index, subject in enumerate(subjects, 1)))
    return "\n".join(lines)


async def notify_users_schedule_updated():
    """Warn all users that the schedule was updated and send their new schedule.

    If the current time is after 16:00, send tomorrow's schedule instead of the
    full weekly one.
    """
    send_tomorrow = _now_uz().hour >= 18
    users = get_all_users()
    for user in users:
        tables = user.tables or []
        if not tables:
            continue
        try:
            await bot.send_message(
                chat_id=user.chat_id,
                text="⚠️ Dars jadval yangilandi! Yangi jadvalingiz:",
            )
        except Exception:
            continue
        for group_id in tables:
            group = get_group(group_id)
            if group is None or not group.table:
                continue
            try:
                if send_tomorrow:
                    text = _format_tomorrow_for_user(group)
                else:
                    text = _format_table(group)
                await bot.send_message(chat_id=user.chat_id, text=text)
            except Exception:
                continue
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.05)


async def send_today_to_groups():
    """Send today's schedule to every bound group chat."""
    day_key = _now_uz().strftime("%A").lower()
    for group_chat in get_all_group_chats():
        group = get_group(group_chat.group_id)
        if group is None or not group.table:
            continue
        subjects = group.table.get(day_key, []) if group.table else []
        if not subjects:
            continue
        text = (
            f"📅 Bugungi ({day_key}) jadvali — {group.name}:\n\n"
            + "\n".join(
                f"{index}. {subject}" for index, subject in enumerate(subjects, 1)
            )
        )
        try:
            await bot.send_message(chat_id=group_chat.chat_id, text=text)
        except Exception:
            continue
        await asyncio.sleep(0.05)


async def notify_tasks_starting_today():
    """Notify admins when a task is starting to complete today."""
    tasks = get_tasks_due_today()
    if not tasks:
        return
    admins = get_all_admins()
    if not admins:
        return
    lines = ["📢 Bugun boshlanadigan vazifalar:\n"]
    for task in tasks:
        when = task.date.strftime("%d.%m.%Y %H:%M") if task.date else "—"
        lines.append(f"• {when} — {task.file_path or 'fayl'}")
    text = "\n".join(lines)
    for admin in admins:
        try:
            await bot.send_message(chat_id=admin.chat_id, text=text)
        except Exception:
            continue
        await asyncio.sleep(0.05)


async def execute_due_tasks():
    """Execute tasks whose date has arrived by uploading their schedule to the DB.

    - Notifies admins when the task starts uploading.
    - After processing, notifies all users that the schedule changed and sends
      them their new schedule (tomorrow's if after 16:00).
    """
    tasks = get_tasks_due_now()
    for task in tasks:
        if not task.file_path:
            continue

        # Mark as running.
        update_task_status(task.id, "running")

        # Notify admins that the task is starting to upload.
        admins = get_all_admins()
        when = task.date.strftime("%d.%m.%Y %H:%M") if task.date else "—"
        for admin in admins:
            try:
                await bot.send_message(
                    chat_id=admin.chat_id,
                    text=f"📢 Vazifa boshlanmoqda: {when}\nJadval yuklab olinmoqda...",
                )
            except Exception:
                continue
            await asyncio.sleep(0.05)

        # Upload the schedule to the DB.
        try:
            upload_table(task.file_path)
        except Exception:
            update_task_status(task.id, "failed")
            # Notify admins that the task failed.
            for admin in get_all_admins():
                try:
                    await bot.send_message(
                        chat_id=admin.chat_id,
                        text=f"❌ Vazifa bajarilmadi: {when}\nFayl xatolik sababli yuklanmadi.",
                    )
                except Exception:
                    continue
                await asyncio.sleep(0.05)
            continue

        update_task_status(task.id, "completed")

        # After processing, notify all users about the schedule change.
        await notify_users_schedule_updated()

        # Notify admins that the task completed successfully.
        for admin in get_all_admins():
            try:
                await bot.send_message(
                    chat_id=admin.chat_id,
                    text=f"✅ Vazifa muvaffaqiyatli yakunlandi: {when}\n"
                         "Barcha foydalanuvchilarga yangi jadval yuborildi.",
                )
            except Exception:
                continue
            await asyncio.sleep(0.05)

        # The schedule has been uploaded — remove the temporary file.
        try:
            if os.path.exists(task.file_path):
                os.remove(task.file_path)
        except OSError:
            pass


async def scheduler_loop():
    """Run the scheduler forever, checking every minute (Uzbekistan time, UTC+5).

    - 05:00  -> send today's schedule to group chats and to users with auto_send
    - 18:00  -> send tomorrow's schedule to group chats
    """
    last_run = {}  # track which hour-tasks already ran today
    while True:
        now = _now_uz()
        hour = now.hour

        try:
            # Execute tasks whose date has arrived.
            await execute_due_tasks()

            # Notify admins about tasks starting today (once per day).
            if last_run.get("notify") != now.date():
                await notify_tasks_starting_today()
                last_run["notify"] = now.date()

            # Clean up completed tasks (date passed) once per day.
            if last_run.get("cleanup") != now.date():
                delete_completed_tasks(now)
                last_run["cleanup"] = now.date()

            if hour == 5 and last_run.get(5) != now.date():
                await send_today_to_groups()
                await send_daily_timetables()
                last_run[5] = now.date()
            elif hour == 18 and last_run.get(18) != now.date():
                await send_tomorrow_to_groups()
                last_run[18] = now.date()
        except Exception:
            # Keep the loop alive even if a send fails.
            pass

        # Wait one minute before checking again.
        await asyncio.sleep(60)