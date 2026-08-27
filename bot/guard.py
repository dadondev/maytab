from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from middlewares.isGuardMiddleware import isGuardMiddleware
from keyboards.guard_menu import (
    get_guard_menu_markup,
    get_guard_grades_markup,
    get_guard_groups_markup,
)
from db.queries import get_groups, get_group

guard_router = Router()

guard_router.message.middleware(isGuardMiddleware())
guard_router.callback_query.middleware(isGuardMiddleware())

DAY_NAMES = {
    "monday": "Dushanba",
    "tuesday": "Seshanba",
    "wednesday": "Chorshanba",
    "thursday": "Payshanba",
    "friday": "Juma",
    "saturday": "Shanba",
}


def _today_day_key() -> str:
    """Return the lowercase English day name for today."""
    return datetime.now().strftime("%A").lower()


def _tomorrow_day_key() -> str:
    """Return the lowercase English day name for tomorrow."""
    return (datetime.now() + timedelta(days=1)).strftime("%A").lower()


def _format_class_schedule(group) -> str:
    lines = [f"📅 {group.name} guruhi jadvali"]
    for day, name in DAY_NAMES.items():
        subjects = group.table.get(day, []) if group.table else []
        if subjects:
            lines.append(
                f"\n{name}:\n"
                + "\n".join(
                    f"{index}. {subject}" for index, subject in enumerate(subjects, 1)
                )
            )
    return "\n".join(lines)


def _format_grouped_schedule(title: str, groups: list, day_key: str) -> str | None:
    """Group classes by lesson count, then by grade, and format the message.

    Class names look like "1-A", "10-B", etc. Within each lesson-count group,
    classes are shown per grade as "1-sinflar: A, B".
    """
    import re

    # Group classes by how many lessons they have on the given day.
    by_count = {}
    for group in groups:
        subjects = group.table.get(day_key, []) if group.table else []
        if subjects:
            by_count.setdefault(len(subjects), []).append(group.name)

    if not by_count:
        return None

    lines = [f"{title}\n"]
    for count in sorted(by_count):
        # Group class names by grade number.
        by_grade = {}
        for name in by_count[count]:
            m = re.match(r"^(\d+)-([A-Za-z]+)$", name)
            if m:
                grade_num = int(m.group(1))
                letter = m.group(2)
                by_grade.setdefault(grade_num, []).append(letter)
            else:
                # Fallback for names that don't match the pattern.
                by_grade.setdefault(name, []).append("")

        lines.append(f"{count}-soat dars borlar:")
        for grade_num in sorted(by_grade):
            letters = ", ".join(sorted(by_grade[grade_num]))
            lines.append(f"  {grade_num}-sinflar: {letters}")
        lines.append("")

    return "\n".join(lines)


@guard_router.message(Command("guard"))
async def guard_command(message: Message):
    await message.answer(
        "Qo'riqchi paneli! Xush kelamiz!", reply_markup=get_guard_menu_markup()
    )


@guard_router.callback_query(F.data == "guard:menu")
async def guard_menu_handler(cb: CallbackQuery):
    await cb.message.edit_text(
        "Qo'riqchi panel. Nima qilmoqchisiz?", reply_markup=get_guard_menu_markup()
    )


@guard_router.callback_query(F.data == "guard:today")
async def guard_today_handler(cb: CallbackQuery):
    """Show today's schedule grouped by lesson count, then by grade."""
    day_key = _today_day_key()
    text = _format_grouped_schedule(
        f"📅 Bugungi ({day_key}) dars jadvali:", get_groups(), day_key
    )
    if text is None:
        await cb.message.edit_text(
            "Bugungi kun uchun jadvallar topilmadi.",
            reply_markup=get_guard_menu_markup(),
        )
        return
    await cb.message.edit_text(text, reply_markup=get_guard_menu_markup())


@guard_router.callback_query(F.data == "guard:tomorrow")
async def guard_tomorrow_handler(cb: CallbackQuery):
    """Show tomorrow's schedule grouped by lesson count, then by grade."""
    day_key = _tomorrow_day_key()
    text = _format_grouped_schedule(
        f"📅 Ertangi ({day_key}) dars jadvali:", get_groups(), day_key
    )
    if text is None:
        await cb.message.edit_text(
            "Ertangi kun uchun jadvallar topilmadi.",
            reply_markup=get_guard_menu_markup(),
        )
        return
    await cb.message.edit_text(text, reply_markup=get_guard_menu_markup())


@guard_router.callback_query(F.data == "guard:grades")
async def guard_grades_handler(cb: CallbackQuery):
    await cb.message.edit_text(
        "Sinfni tanlang:", reply_markup=get_guard_grades_markup()
    )


@guard_router.callback_query(F.data.regexp(r"^guard:grade:\d+$"))
async def guard_grade_handler(cb: CallbackQuery):
    grade_id = int(cb.data.split(":")[2])
    groups = get_groups(grade_id)
    if not groups:
        await cb.answer("Bu sinf uchun jadvallar mavjud emas.", show_alert=True)
        return
    await cb.message.edit_text(
        "Guruhni tanlang:", reply_markup=get_guard_groups_markup(grade_id)
    )


@guard_router.callback_query(F.data.regexp(r"^guard:show:\d+$"))
async def guard_show_handler(cb: CallbackQuery):
    group = get_group(int(cb.data.split(":")[2]))
    if group is None:
        await cb.answer("Jadval topilmadi.", show_alert=True)
        return
    if not group.table:
        await cb.message.edit_text(
            f"😕 {group.name} guruhi uchun hozircha jadval mavjud emas.",
            reply_markup=get_guard_groups_markup(group.grade),
        )
        return
    await cb.message.edit_text(
        _format_class_schedule(group),
        reply_markup=get_guard_groups_markup(group.grade),
    )