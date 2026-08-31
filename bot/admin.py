from datetime import datetime
import os
import asyncio

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from files.file import save_file_handler
from middlewares.isAdminMiddleware import isAdminMiddleware
from bot.bootstrap import bot

from states.setting_state import SettingsState
from keyboards.admin_menu import admin_menu_markup, back_admin_menu
from keyboards.admin_admit_task_date import admit_task_markup
from keyboards.admin_broadcast import get_broadcast_confirm_markup
from keyboards.admin_tasks import get_tasks_list_markup, get_task_actions_markup
from keyboards.admin_security import (
    get_security_menu_markup,
    get_security_user_list_markup,
    get_security_user_actions_markup,
)

from db.queries import (
    create_task,
    upload_table,
    get_all_users,
    get_user,
    get_user_by_id,
    get_group,
    get_active_tasks,
    get_all_tasks,
    delete_all_tasks,
    delete_task,
    finish_task,
    set_user_role,
    delete_user,
)
from config.utils import admit_task_regex

admin_router = Router()

admin_router.message.middleware(isAdminMiddleware())
admin_router.callback_query.middleware(isAdminMiddleware())


def delete_uploaded_file(file_path: str | None) -> None:
    """Remove the downloaded schedule file after it has been processed."""
    if not file_path:
        return
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        pass


def _format_user_schedule(group) -> str:
    """Format a group's full weekly schedule for a user message."""
    day_names = {
        "monday": "Dushanba", "tuesday": "Seshanba", "wednesday": "Chorshanba",
        "thursday": "Payshanba", "friday": "Juma", "saturday": "Shanba",
    }
    lines = [f"📅 {group.name} guruhi jadvali"]
    for day, name in day_names.items():
        subjects = group.table.get(day, []) if group.table else []
        if subjects:
            lines.append(
                f"\n{name}:\n"
                + "\n".join(
                    f"{index}. {subject}" for index, subject in enumerate(subjects, 1)
                )
            )
    return "\n".join(lines)


async def notify_users_schedule_updated():
    """Warn all users that the schedule was updated and send their new schedule."""
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
                await bot.send_message(
                    chat_id=user.chat_id, text=_format_user_schedule(group)
                )
            except Exception:
                continue
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.05)


@admin_router.message(Command("admin"))
async def admin_command(message: Message):
    # Secret admin CRUD: /admin create <chat_id> <password> | list <password> | remove <chat_id> <password>
    text = (message.text or "").strip()
    parts = text.split()
    if len(parts) > 1:
        await admin_secret_command(message, parts)
        return
    await message.answer("Siz admin menyusidasiz!", reply_markup=admin_menu_markup)


def _check_admin_password(given: str) -> bool:
    from config.utils import ADMIN_PASSWORD
    return bool(ADMIN_PASSWORD) and given == ADMIN_PASSWORD


async def admin_secret_command(message: Message, parts: list[str]):
    """Handle /admin create|list|remove with password from env."""
    from db.queries import get_user, get_all_admins

    action = parts[1].lower()

    if action == "list":
        # /admin list <password>
        if len(parts) != 3 or not _check_admin_password(parts[2]):
            await message.answer("❌ Noto'g'ri buyruq yoki parol!")
            return
        admins = get_all_admins()
        if not admins:
            await message.answer("👮‍♀️ Hozircha adminlar mavjud emas.")
            return
        lines = ["👮‍♀️ Adminlar ro'yxati:"]
        for admin in admins:
            lines.append(f"• Foydalanuvchi (chat_id: {admin.chat_id})")
        await message.answer("\n".join(lines))
        return

    # create / remove need chat_id + password
    if len(parts) != 4:
        await message.answer("❌ Buyruq formati: /admin <create|remove> <chat_id> <password>")
        return

    try:
        chat_id = int(parts[2])
    except ValueError:
        await message.answer("❌ Chat ID raqam bo'lishi kerak!")
        return

    if not _check_admin_password(parts[3]):
        await message.answer("❌ Noto'g'ri parol!")
        return

    user = get_user(chat_id)
    if user is None:
        await message.answer("❌ Bunday foydalanuvchi topilmadi. Avval ro'yxatdan o'tishi kerak!")
        return

    if action == "create":
        set_user_role(chat_id, "admin")
        await message.answer("✅ Foydalanuvchi admin qilindi!")
    elif action == "remove":
        set_user_role(chat_id, "user")
        await message.answer("🗑 Foydalanuvchi admin ro'lidan olib tashlandi.")
    else:
        await message.answer("❌ Noma'lum buyruq. create|list|remove dan birini ishlating.")

@admin_router.callback_query(F.data == "upload_table")
async def upload_table_handler(cb:CallbackQuery, state:FSMContext):
    await state.set_state(SettingsState.mode)
    await cb.message.edit_text("Dars jadval faylini <strong>excel</strong> formatida yuborishingiz mumkin!", reply_markup=back_admin_menu, parse_mode="HTML")

@admin_router.message(SettingsState.mode)
async def table_handler(message: Message, state:FSMContext):
    if message.document:
        # Only accept Excel files.
        filename = (message.document.file_name or "").lower()
        if not filename.endswith((".xlsx", ".xls")):
            await state.set_state(SettingsState.mode)
            await message.answer(
                "Iltimos, faqat <strong>Excel</strong> fayl yuboring! (.xlsx / .xls)",
                reply_markup=back_admin_menu,
                parse_mode="HTML",
            )
            return
        msg = await message.answer("⬇ Fayl yuklab olinmoqda ⬇")
        await save_file_handler(message.document.file_id, chat_id=msg.chat.id,message_id=msg.message_id, state=state)
    else:
        await state.set_state(SettingsState.mode)
        await message.answer("Iltimos, faqat fayl yuboring!", reply_markup=back_admin_menu)


@admin_router.callback_query(F.data == "back_admin_menu")
async def back_admin_menu_handler(cb:CallbackQuery, state:FSMContext):
    await state.clear()
    await cb.message.edit_text("Siz admin menyusidasiz!", reply_markup=admin_menu_markup)


@admin_router.callback_query(F.data.regexp(r"^save_file:(?:yes|no)$"))
async def save_file_permission_handler(cb:CallbackQuery, state:FSMContext):
    permission = cb.data.split(":")[1] == "yes"
    if permission:
        await cb.message.edit_text("Ma'lumotlar saqlanmoqda...")
        file_path = await state.get_value("file_path")
        try:
            upload_table(file_path)
        except Exception:
            await cb.message.edit_text(
                "❌ Faylni o'qishda xato yuz berdi. "
                "Fayl to'g'ri Excel formatda ekanligini tekshirib qayta urinish ko'ring!"
            )
            await cb.message.answer("Siz admin menyusidasiz!", reply_markup=admin_menu_markup)
            return
        # Schedule uploaded to DB — remove the temporary file.
        delete_uploaded_file(file_path)
        await cb.message.edit_text("Jadval muvaffaqiyatli tarzda yakunlandi!")
        # Warn all users and send them their new schedule.
        await notify_users_schedule_updated()
        await cb.message.answer("Siz admin menyusidasiz!", reply_markup=admin_menu_markup)
    else:
        await state.set_state(SettingsState.date)
        await cb.message.edit_text("Iltimos sana va soatni yuboring!\nMasalan: 17.07.2026 17:00")

@admin_router.message(SettingsState.date)
async def date_handler(message:Message, state:FSMContext):
    date = message.text
    try:
        dt = datetime.strptime(date, "%d.%m.%Y %H:%M")
    except ValueError:
        await state.set_state(SettingsState.date)
        await message.answer(
            "Sana va soat noto'g'ri formatda!\nIltimos quyidagi formatda yuboring: 17.07.2026 17:00",
            reply_markup=back_admin_menu,
        )
        return
    await state.update_data(date=dt)
    await message.answer(f"Sana va vaqtni tastiqlang: {dt.strftime('%d.%m.%Y %H:%M')}", reply_markup=admit_task_markup)


@admin_router.callback_query(F.data.regexp(admit_task_regex))    
async def admit_handler(cb:CallbackQuery, state:FSMContext):
    action = cb.data.split(":")[1]
    if action == "edit":
        await state.set_state(SettingsState.date)
        await cb.message.edit_text("Iltimos sana va soatni yuboring!\nMasalan: 17.07.2026 17:00")
    elif action == "accept":
        # Block creating a new task while another task is still active.
        active = get_active_tasks()
        if active:
            await cb.message.edit_text(
                "❌ Yangi vazifa qo'shib bo'lmaydi! "
                "Avval old vazifa to'liq tugashishi lozim."
            )
            await cb.message.answer("Siz admin menyusidasiz!", reply_markup=admin_menu_markup)
            return

        file_path = await state.get_value("file_path")
        file_date = await state.get_value("date")
        # Remove any old tasks before creating the new one.
        delete_all_tasks()
        # IMPORTANT: do NOT delete the file here — the task needs it later when
        # its date arrives and the schedule is uploaded to the DB.
        create_task(file_path=file_path, file_date=file_date)
        await cb.message.edit_text("✅ Sana va vaqt tastiqlandi! ✅")
        await cb.message.answer("Siz admin menyusidasiz!", reply_markup=admin_menu_markup)


# --------------------------
# 📬 Xabar yuborish (broadcast)
# --------------------------
@admin_router.callback_query(F.data == "send_message")
async def send_message_handler(cb: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsState.broadcast_message)
    await cb.message.edit_text(
        "Yubormoqchi bo'lgan xabaringizni yozib yuboring. "
        "Ushbu xabar barcha foydalanuvchilarga yetkaziladi!",
        reply_markup=back_admin_menu,
    )


@admin_router.message(SettingsState.broadcast_message)
async def broadcast_message_handler(message: Message, state: FSMContext):
    text = message.text
    if not text:
        await message.answer("Iltimos, matn yuboring!", reply_markup=back_admin_menu)
        return
    await state.update_data(broadcast_message=text)
    await message.answer(
        f"Xabaringiz quyidagicha:\n\n{text}\n\nYuborishni tasdiqlaysizmi?",
        reply_markup=get_broadcast_confirm_markup(),
    )


@admin_router.callback_query(F.data.regexp(r"^broadcast:(?:send|rewrite)$"))
async def broadcast_confirm_handler(cb: CallbackQuery, state: FSMContext):
    action = cb.data.split(":")[1]
    if action == "rewrite":
        await state.set_state(SettingsState.broadcast_message)
        await cb.message.edit_text(
            "Yubormoqchi bo'lgan xabaringizni qayta yozib yuboring.",
            reply_markup=back_admin_menu,
        )
        return

    text = await state.get_value("broadcast_message")
    users = get_all_users()
    sent = 0
    for user in users:
        try:
            await bot.send_message(chat_id=user.chat_id, text=text)
            sent += 1
        except Exception:
            continue
    await state.clear()
    await cb.message.edit_text(f"✅ Xabar {sent} ta foydalanuvchiga yuborildi.")
    await cb.message.answer("Siz admin menyusidasiz!", reply_markup=admin_menu_markup)


# --------------------------
# �️ Qo'riqchilar (security) — manage guards only
# --------------------------
@admin_router.callback_query(F.data == "security")
async def security_menu_handler(cb: CallbackQuery):
    await cb.message.edit_text(
        "🛡️ Qo'riqchilar bo'limi. Qo'riqchilar ro'yxatini ko'ring yoki yangi qo'riqchi qo'shing:",
        reply_markup=get_security_menu_markup(),
    )


@admin_router.callback_query(F.data == "security:guards")
async def security_list_handler(cb: CallbackQuery):
    markup = get_security_user_list_markup("guards", "security")
    await cb.message.edit_text("🛡️ Qo'riqchilar ro'yxati:", reply_markup=markup)


@admin_router.callback_query(F.data.regexp(r"^security:user:\d+:guards$"))
async def security_user_detail_handler(cb: CallbackQuery):
    _, _, user_id, list_type = cb.data.split(":")
    user = get_user_by_id(int(user_id))
    if user is None:
        await cb.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return
    await cb.message.edit_text(
        f"🛡️ Foydalanuvchi\n🆔 {user.chat_id}\n\nNima qilmoqchisiz?",
        reply_markup=get_security_user_actions_markup(user.id, list_type),
    )


@admin_router.callback_query(
    F.data.regexp(r"^security:(demote|delete):\d+:guards$")
)
async def security_user_action_handler(cb: CallbackQuery):
    _, action, user_id, list_type = cb.data.split(":")
    user = get_user_by_id(int(user_id))
    if user is None:
        await cb.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return

    if action == "demote":
        set_user_role(user.chat_id, "user")
        text = "🛡️ Qo'riqchi ro'lidan olib tashlandi."
    else:
        delete_user(user.id)
        text = "🗑 Foydalanuvchi o'chirildi."

    await cb.answer(text, show_alert=True)
    markup = get_security_user_list_markup("guards", "security")
    await cb.message.edit_text("🛡️ Qo'riqchilar ro'yxati:", reply_markup=markup)


@admin_router.callback_query(F.data == "security:add_guard")
async def security_add_guard_handler(cb: CallbackQuery, state: FSMContext):
    await state.set_data({"security_role": "guard"})
    await state.set_state(SettingsState.security_select_user)
    await cb.message.edit_text(
        "Qo'riqchi qilmoqchi bo'lgan foydalanuvchining chat ID sini yuboring.",
        reply_markup=back_admin_menu,
    )


@admin_router.message(SettingsState.security_select_user)
async def security_select_user_handler(message: Message, state: FSMContext):
    try:
        chat_id = int(message.text.strip())
    except ValueError:
        await state.set_state(SettingsState.security_select_user)
        await message.answer("Iltimos, to'g'ri chat ID yuboring!", reply_markup=back_admin_menu)
        return

    role_name = (await state.get_data()).get("security_role", "guard")
    if set_user_role(chat_id, role_name):
        text = "🛡️ Foydalanuvchi qo'riqchi qilindi."
        await message.answer(text)
    else:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.")

    await state.clear()

    markup = get_security_user_list_markup("guards", "security")
    await message.answer("🛡️ Qo'riqchilar ro'yxati:", reply_markup=markup)


# --------------------------
# 📋 Vazifalar (tasks)
# --------------------------
@admin_router.callback_query(F.data == "tasks")
async def tasks_list_handler(cb: CallbackQuery):
    tasks = get_all_tasks()
    if not tasks:
        await cb.message.edit_text(
            "📋 Hozircha hech qanday vazifa mavjud emas.",
            reply_markup=back_admin_menu,
        )
        return
    await cb.message.edit_text(
        "📋 Vazifalar ro'yxati:\nVazifani tanlang:",
        reply_markup=get_tasks_list_markup(tasks),
    )


@admin_router.callback_query(F.data.regexp(r"^task:show:\d+$"))
async def task_show_handler(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[2])
    tasks = get_all_tasks()
    task = next((t for t in tasks if t.id == task_id), None)
    if task is None:
        await cb.answer("Vazifa topilmadi.", show_alert=True)
        return
    when = task.date.strftime("%d.%m.%Y %H:%M") if task.date else "—"
    status_text = {
        "pending": "⏳ Kutilmoqda",
        "running": "🔄 Bajarilmoqda",
        "completed": "✅ Yakunlangan",
        "failed": "❌ Xato",
    }.get(task.status, task.status)
    await cb.message.edit_text(
        f"📋 Vazifa #{task.id}\n"
        f"📅 Sana: {when}\n"
        f"📄 Fayl: {task.file_path or '—'}\n"
        f"🔄 Holat: {status_text}\n\n"
        f"Vazifani yakunlash va o'chirish yoki faqat o'chirish mumkin:",
        reply_markup=get_task_actions_markup(task.id),
    )


@admin_router.callback_query(F.data.regexp(r"^task:finish:\d+$"))
async def task_finish_handler(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[2])
    tasks = get_all_tasks()
    task = next((t for t in tasks if t.id == task_id), None)
    if task is None:
        await cb.answer("Vazifa topilmadi.", show_alert=True)
        return

    when = task.date.strftime("%d.%m.%Y %H:%M") if task.date else "—"
    # Upload the schedule to the DB, notify users, then delete the task.
    try:
        file_path = task.file_path
        upload_table(file_path)
    except Exception:
        await cb.message.edit_text(
            f"❌ Vazifa #{task.id} yakunlanmadi: faylni o'qishda xato yuz berdi."
        )
        await cb.message.answer("Siz admin menyusidasiz!", reply_markup=admin_menu_markup)
        return

    # Notify all users about the schedule change.
    await notify_users_schedule_updated()

    finish_task(task_id)
    await cb.message.edit_text(f"✅ Vazifa yakunlandi va o'chirildi: {when}")
    await cb.message.answer("Siz admin menyusidasiz!", reply_markup=admin_menu_markup)


@admin_router.callback_query(F.data.regexp(r"^task:delete:\d+$"))
async def task_delete_handler(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[2])
    if delete_task(task_id):
        await cb.message.edit_text(f"🗑 Vazifa #{task_id} o'chirildi.")
    else:
        await cb.message.edit_text("Vazifa topilmadi.")
    await cb.message.answer("Siz admin menyusidasiz!", reply_markup=admin_menu_markup)