from datetime import datetime

from aiogram import Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from middlewares.existUserMiddleware import existUserMiddleware
from keyboards.register import (
    register_markup,
    school_selection_markup,
    register_auto_send_markup,
)
from keyboards.menu import menu_markup
from keyboards.my_tables import get_my_tables_markup
from keyboards.group_chat import (
    get_group_grades_markup,
    get_group_start_markup,
)
from keyboards.user_tables import (
    get_grades_markup,
    get_groups_markup,
    get_table_markup,
    get_table_days_markup,
)
from keyboards.settings import get_settings_markup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from states.register_state import RegisterState
from db.queries import (
    create_user,
    get_user,
    create_role,
    get_grades,
    get_groups,
    get_group,
    get_group_chat,
    get_school_regions,
    get_school_provinces,
    get_schools,
    find_nearby_schools,
    update_user_school,
    update_user_tables,
    update_user_setting,
    seed_default_schools,
)
from db.schemas import User
from bot.admin import admin_router
from bot.guard import guard_router
from bot.group_chat import group_router
from bot.bootstrap import bot
from config.utils import OWNER_CHAT_ID


dp = Dispatcher()

public_router = Router()
public_router.message.middleware(existUserMiddleware())


@public_router.message(CommandStart())
async def start_cmd_bot(message: Message, user_exist: bool, user: User | None):
    if message.chat.type == "private":
        if user_exist and bool(user):
            display_name = (
                message.from_user.first_name
                or message.from_user.username
                or "Foydalanuvchi"
            )
            await message.answer(
                text=f"👋 Assalomu alaykum, {display_name}! Nima qilmoqchisiz?",
                reply_markup=menu_markup,
            )
            return

        await message.answer(
            text="👋 Assalomu alaykum! Botdan foydalanishdan avval ro'yhatdan o'tishingiz lozim. \n\n✅ Ro'yhatdan o'tish uchun pastdagi tugmani bosing!",
            reply_markup=register_markup,
        )
        return

    group_binding = get_group_chat(message.chat.id)
    if group_binding is not None:
        group = get_group(group_binding.group_id)
        if group is not None:
            today_key = datetime.now().strftime("%A").lower()
            if not group.table:
                await message.answer(
                    text=f"😕 Bu guruhga biriktirilgan <b>{group.name}</b> jadvali hozircha mavjud emas.",
                    reply_markup=get_group_start_markup(group.id),
                    parse_mode="HTML",
                )
                return

            await message.answer(
                text=format_day(group, today_key),
                reply_markup=get_group_start_markup(group.id),
            )
            return

    await message.answer(
        text="👋 Assalomu alaykum! Bu guruhda hali biriktirilgan sinf jadvali yo'q. Iltimos, sinfni tanlang va guruh jadvalini o'rnating.",
        reply_markup=get_group_grades_markup(),
    )


@public_router.callback_query(F.data == "register")
async def register(callback_query: CallbackQuery, state: FSMContext):
    seed_default_schools()
    await state.set_state(RegisterState.school_type)
    await callback_query.message.edit_text(
        "🏫 Maktabni tanlash usulini tanlang:\n\n📍 Yaqin maktabni tanlash\n✍️ Qo'lda tanlash\n📍 Mening joylashuvim",
        reply_markup=school_selection_markup,
    )


@public_router.message(RegisterState.school_type)
async def register_school_type(message: Message, state: FSMContext):
    text = (message.text or "").strip()

    if message.location is not None:
        schools = find_nearby_schools(message.location.latitude, message.location.longitude)
        if schools:
            selected = schools[0]
            await state.update_data(school_id=selected.id)
            await state.update_data(school_name=selected.name)
            await state.set_state(RegisterState.auto_send)
            await message.answer(
                text=f"✅ Sizga yaqin maktab topildi: {selected.name} ({selected.region}, {selected.province})\n\n🔄 Avtomatik yuborish xizmatidan foydalanasizmi?\n\n📌 Sizga har kuni siz tanlagan dars jadvallar yuboriladi. Bot bir kun oldin va kunning boshida jadvalingizni yuboradi.",
                reply_markup=register_auto_send_markup,
            )
            return
        await message.answer("😕 Yaqin maktab topilmadi. Iltimos, qo'lda tanlang yoki boshqa joydan yuboring.")
        return

    if "yaqin" in text.lower() or "Mening joylashuvim" in text:
        await message.answer(
            "📍 Iltimos, joylashuvingizni yuboring. Bot yaqinidagi maktabni topadi.",
            reply_markup=school_selection_markup,
        )
        return

    if "qo'lda" in text.lower() or "Qo'lda" in text or "qo'lda" in text:
        regions = get_school_regions()
        if not regions:
            await message.answer("😕 Maktab ma'lumotlari hozircha mavjud emas.")
            return
        await state.update_data(school_mode="manual")
        await state.set_state(RegisterState.region)
        await message.answer(
            "🌍 Hududni tanlang:\n" + "\n".join(f"• {r}" for r in regions),
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await message.answer(
        "❌ Iltimos, quyidagi variantlardan birini tanlang: 📍 Yaqin maktabni tanlash / ✍️ Qo'lda tanlash / 📍 Mening joylashuvim",
        reply_markup=school_selection_markup,
    )


@public_router.message(RegisterState.region)
async def register_region(message: Message, state: FSMContext):
    region = (message.text or "").strip()
    regions = get_school_regions()
    if region not in regions:
        await message.answer("❌ Noto'g'ri hudud. Quyidagi variantlardan birini tanlang:\n" + "\n".join(f"• {r}" for r in regions))
        return

    await state.update_data(region=region)
    provinces = get_school_provinces(region)
    await state.set_state(RegisterState.province)
    await message.answer(
        f"🏙 {region} hududi uchun viloyatni tanlang:\n" + "\n".join(f"• {p}" for p in provinces),
    )


@public_router.message(RegisterState.province)
async def register_province(message: Message, state: FSMContext):
    data = await state.get_data()
    region = data.get("region")
    province = (message.text or "").strip()
    provinces = get_school_provinces(region) if region else []
    if province not in provinces:
        await message.answer("❌ Noto'g'ri viloyat. Quyidagi variantlardan birini tanlang:\n" + "\n".join(f"• {p}" for p in provinces))
        return

    await state.update_data(province=province)
    schools = get_schools(region=region, province=province)
    await state.set_state(RegisterState.school)
    await message.answer(
        f"🏫 {region} / {province} uchun maktabni tanlang:\n" + "\n".join(f"• {s.name}" for s in schools),
    )


@public_router.message(RegisterState.school)
async def register_school(message: Message, state: FSMContext):
    data = await state.get_data()
    region = data.get("region")
    province = data.get("province")
    name = (message.text or "").strip()
    schools = get_schools(region=region, province=province)
    selected = next((s for s in schools if s.name.lower() == name.lower()), None)
    if selected is None:
        await message.answer("❌ Noto'g'ri maktab nomi. Quyidagi variantlardan birini tanlang:\n" + "\n".join(f"• {s.name}" for s in schools))
        return

    await state.update_data(school_id=selected.id, school_name=selected.name)
    await state.set_state(RegisterState.auto_send)
    await message.answer(
        f"✅ Siz tanlagan maktab: {selected.name} ({selected.region}, {selected.province})\n\n🔄 Avtomatik yuborish xizmatidan foydalanasizmi?\n\n📌 Sizga har kuni siz tanlagan dars jadvallar yuboriladi. Bot bir kun oldin va kunning boshida jadvalingizni yuboradi.",
        reply_markup=register_auto_send_markup,
    )


@public_router.message(RegisterState.auto_send)
async def register_auto_send(message: Message, state: FSMContext):

    auto_send = message.text.lower()

    await state.update_data(auto_send=True if "ha" in auto_send else False)
    await state.update_data(sms_service=False)

    chat_id = message.from_user.id

    data = await state.get_data()

    data = {
        **data,
        "auto_send": True if "ha" in (message.text or "").lower() else False,
    }

    user = create_user(chat_id=chat_id, data=data)
    role = create_role(user_id=user.id)
    school_id = data.get("school_id")
    if school_id is not None:
        update_user_school(chat_id, school_id)
        user = get_user(chat_id)

    await message.answer(
        "🎉 Muvaffaqiyatli tarzda ro'yhatdan o'tdingiz!",
        reply_markup=ReplyKeyboardRemove(),
    )

    await notify_admins_new_user(user)

    await start_cmd_bot(message, True, user)


async def notify_admins_new_user(user: User) -> None:
    """Notify the owner when a new user has joined/registered the bot."""
    text = (
        f"🆕 Yangi foydalanuvchi botga qo'shildi!\n\n"
        f"🆔 ID: {user.chat_id}"
    )
    try:
        await bot.send_message(chat_id=OWNER_CHAT_ID, text=text)
    except Exception:
        # Skip if the owner can't be reached (blocked bot, etc.)
        pass


# TODO: at the end of register


# TODO: at the start of my tables


@public_router.callback_query(F.data == "my_tables")
async def my_tables_handler(callback_data: CallbackQuery):

    user = get_user(callback_data.from_user.id)

    tables_markup = get_my_tables_markup(user.tables)

    message = (
        "😕 Sizda hech qanday jadval mavjud emas!"
        if len(user.tables) == 0
        else "📚 Sizga tegishli bo'lgan dars jadvallari:"
    )

    await callback_data.message.edit_text(message, reply_markup=tables_markup)
    await callback_data.answer()


@public_router.callback_query(F.data == "back_menu")
async def back_menu(callback_query: CallbackQuery):

    user = get_user(callback_query.from_user.id)

    display_name = (
        callback_query.from_user.first_name
        or callback_query.from_user.username
        or "Foydalanuvchi"
    )
    await callback_query.message.edit_text(
        f"Assalomu alaykum, {display_name}", reply_markup=menu_markup
    )
    await callback_query.answer()


@public_router.callback_query(F.data == "refresh_selected_tables")
async def refresh_selected_tables_handler(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    tables = user.tables or [] if user else []

    if not tables:
        await callback_query.message.edit_text(
            "😕 Sizda hozircha tanlangan jadval mavjud emas.",
            reply_markup=get_my_tables_markup([]),
        )
        await callback_query.answer()
        return

    refreshed = []
    for group_id in tables:
        group = get_group(group_id)
        if group is not None and group.table:
            refreshed.append(group)

    if not refreshed:
        await callback_query.message.edit_text(
            "😕 Tanlangan jadvallar hozircha mavjud emas yoki yangilanmagan.",
            reply_markup=get_my_tables_markup(tables),
        )
        await callback_query.answer()
        return

    for group in refreshed:
        await callback_query.message.answer(
            format_table(group),
            reply_markup=get_table_days_markup(group.id, back_callback="my_tables"),
        )

    await callback_query.answer("✅ Tanlangan jadval(lar) yangilandi.")


@public_router.callback_query(F.data == "add_user_table")
async def add_user_table(callback_query: CallbackQuery):
    grades = get_grades()
    text = "➕ Jadval qo'shish uchun sinfni tanlang:"
    if not grades:
        text = "😕 Hozircha qo'shiladigan jadvallar mavjud emas."
    await callback_query.message.edit_text(
        text, reply_markup=get_grades_markup(grades, source="add", back_callback="my_tables")
    )
    await callback_query.answer()


@public_router.callback_query(F.data == "general_tables")
async def general_tables_handler(callback_query: CallbackQuery):
    grades = get_grades()
    text = "📋 Umumiy jadval uchun sinfni tanlang:"
    if not grades:
        text = "😕 Hozircha umumiy jadvallar mavjud emas."
    await callback_query.message.edit_text(
        text, reply_markup=get_grades_markup(grades, source="general")
    )
    await callback_query.answer()


@public_router.callback_query(F.data.regexp(r"^select_grade:(?:add|general):\d+$"))
async def select_grade_handler(callback_query: CallbackQuery):
    _, source, grade_id = callback_query.data.split(":")
    groups = get_groups(int(grade_id))
    back_callback = "add_user_table" if source == "add" else "general_tables"
    text = "🏫 Guruhni tanlang:"
    if not groups:
        text = "😕 Bu sinf uchun jadvallar mavjud emas."
    await callback_query.message.edit_text(
        text, reply_markup=get_groups_markup(groups, back_callback=back_callback)
    )
    await callback_query.answer()


def format_table(group) -> str:
    day_names = {
        "monday": "🟡 Dushanba", "tuesday": "🔴 Seshanba", "wednesday": "🟢 Chorshanba",
        "thursday": "🟣 Payshanba", "friday": "🔵 Juma", "saturday": "🟠 Shanba",
    }
    lines = [f"📋 {group.name} guruhi jadvali"]
    for day, name in day_names.items():
        subjects = group.table.get(day, []) if group.table else []
        if subjects:
            lines.append(f"\n{name}:\n" + "\n".join(f"  {index}. {subject}" for index, subject in enumerate(subjects, 1)))
    return "\n".join(lines)


def format_day(group, day_key: str) -> str:
    """Format a single day's schedule for a class."""
    day_names = {
        "monday": "🟡 Dushanba", "tuesday": "🔴 Seshanba", "wednesday": "🟢 Chorshanba",
        "thursday": "🟣 Payshanba", "friday": "🔵 Juma", "saturday": "🟠 Shanba",
    }
    subjects = group.table.get(day_key, []) if group.table else []
    name = day_names.get(day_key, day_key)
    if not subjects:
        return f"📅 {group.name} — {name}: 😕 bo'sh (dars yo'q)"
    lines = [f"📅 {group.name} — {name}:"]
    lines.append("\n".join(f"{index}. {subject}" for index, subject in enumerate(subjects, 1)))
    return "\n".join(lines)


@public_router.callback_query(F.data.regexp(r"^show_table:\d+$"))
async def show_table_handler(callback_query: CallbackQuery):
    group = get_group(int(callback_query.data.split(":")[1]))
    if group is None:
        await callback_query.answer("Jadval topilmadi.", show_alert=True)
        return
    # No schedule data for this group.
    if not group.table:
        await callback_query.message.edit_text(
            f"😕 {group.name} guruhi uchun hozircha jadval mavjud emas. "
            "Admin jadvalni yuklaganida sizga xabar beriladi!",
            reply_markup=get_table_days_markup(group.id, back_callback="general_tables"),
        )
        return
    user = get_user(callback_query.from_user.id)
    selected = group.id in (user.tables or [])
    await callback_query.message.edit_text(
        f"📅 {group.name} guruhi jadvali. Qaysi kunni ko'rmoqchisiz?",
        reply_markup=get_table_days_markup(group.id, back_callback="general_tables"),
    )
    await callback_query.answer()


@public_router.callback_query(F.data.regexp(r"^show_day:\d+:(monday|tuesday|wednesday|thursday|friday|saturday)$"))
async def show_day_handler(callback_query: CallbackQuery):
    _, group_id, day_key = callback_query.data.split(":")
    group = get_group(int(group_id))
    if group is None:
        await callback_query.answer("Jadval topilmadi.", show_alert=True)
        return
    # No schedule data for this group at all.
    if not group.table:
        await callback_query.message.edit_text(
            f"😕 {group.name} guruhi uchun hozircha jadval mavjud emas!",
            reply_markup=get_table_days_markup(group.id, back_callback="general_tables"),
        )
        return
    await callback_query.message.edit_text(
        format_day(group, day_key),
        reply_markup=get_table_days_markup(group.id, back_callback="general_tables"),
    )
    await callback_query.answer()


@public_router.callback_query(F.data.regexp(r"^(?:add_table|remove_table):\d+$"))
async def update_table_selection_handler(callback_query: CallbackQuery):
    action, group_id = callback_query.data.split(":")
    group_id = int(group_id)
    if get_group(group_id) is None:
        await callback_query.answer("Jadval topilmadi.", show_alert=True)
        return
    user = get_user(callback_query.from_user.id)
    tables = list(user.tables or [])
    if action == "add_table" and group_id not in tables:
        tables.append(group_id)
    elif action == "remove_table" and group_id in tables:
        tables.remove(group_id)
    update_user_tables(user.chat_id, tables)
    await callback_query.answer("✅ Jadval qo'shildi." if action == "add_table" else "🗑 Jadval o'chirildi.")
    if action == "add_table":
        await callback_query.message.edit_text(
            "✅ Jadval Mening jadvallarim bo'limiga qo'shildi!",
            reply_markup=get_table_markup(group_id, selected=True),
        )
    else:
        await my_tables_handler(callback_query)


@public_router.callback_query(F.data == "settings")
async def settings_handler(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    await callback_query.message.edit_text(
        "⚙️ Sozlamalar:", reply_markup=get_settings_markup(user)
    )
    await callback_query.answer()


@public_router.callback_query(F.data == "change_school")
async def change_school_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(RegisterState.school_type)
    await callback_query.message.edit_text(
        "🏫 Maktabni tanlash usulini tanlang:\n\n📍 Yaqin maktabni tanlash\n✍️ Qo'lda tanlash\n📍 Mening joylashuvim",
        reply_markup=school_selection_markup,
    )
    await callback_query.answer()


@public_router.callback_query(F.data.regexp(r"^toggle_setting:auto_send$"))
async def toggle_setting_handler(callback_query: CallbackQuery):
    setting = callback_query.data.split(":")[1]
    user = get_user(callback_query.from_user.id)
    value = not bool(getattr(user, setting))
    update_user_setting(user.chat_id, setting, value)
    user = get_user(callback_query.from_user.id)
    await callback_query.message.edit_reply_markup(reply_markup=get_settings_markup(user))
    await callback_query.answer("⚙️ Sozlama yangilandi.")


# INFO: at the end of my tables


# INFO: start of general tables


# INFO: end of general tables


# INFO: start of settings


# INFO: end of settings


async def start_bot():
    """Start the bot via polling (default mode)."""
    setup()
    await notify_owner_started()
    await dp.start_polling(bot)


def setup_bot():
    """Register all routers on the dispatcher. Used by both polling and webhook."""
    setup()


async def notify_owner_started():
    """Send a startup notification to the owner (from .env).

    Lets the owner know the bot is running. Safe to call even if the owner
    hasn't started a chat with the bot yet (the send is wrapped in try/except).
    """
    if not OWNER_CHAT_ID:
        return
    try:
        await bot.send_message(
            chat_id=int(OWNER_CHAT_ID),
            text="✅ Bot ishga tushdi va ishlamoqda!",
        )
    except Exception:
        # Owner may not have started the bot yet — ignore silently.
        pass


def setup():
    """Initialize the DB, register routers, and promote the owner to admin.

    Safe to call multiple times (idempotent). Used by polling, the aiohttp
    webhook server, and the FastAPI/Vercel entry point.
    """
    from db.schemas import init_db
    from db.queries import seed_default_schools

    init_db()
    seed_default_schools()
    dp.include_routers(public_router, admin_router, guard_router, group_router)
