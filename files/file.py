import uuid, asyncio, os
from aiogram.fsm.context import FSMContext

from bot.bootstrap import bot
from excel.get_data_from_file import get_data
from keyboards.admit_save_file import survey_save_file_markup
from config.utils import DOWNLOAD_DIR


async def save_file_handler(file_id: str, chat_id: int, message_id: int, state: FSMContext):
    try:
        path = await bot.get_file(file_id)
    except Exception:
        await bot.edit_message_text(
            "❌ Faylni yuklab olib bo'lmadi. Qayta urinish ko'ring!",
            chat_id=chat_id,
            message_id=message_id,
        )
        return

    # Ensure the download directory exists (works with Railway volumes too).
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_name = uuid.uuid4()
    file_path = os.path.join(DOWNLOAD_DIR, f"{file_name}.xlsx")
    try:
        await bot.download_file(path.file_path, file_path)
    except Exception:
        await bot.edit_message_text(
            "❌ Faylni saqlab bo'lmadi. Qayta urinish ko'ring!",
            chat_id=chat_id,
            message_id=message_id,
        )
        return

    await bot.edit_message_text(
        "✅ Fayl muvaffaqiyatli yuklab olindi! ✅",
        chat_id=chat_id,
        message_id=message_id,
    )
    await asyncio.sleep(1)
    await state.update_data(file_path=file_path)
    await bot.edit_message_text(
        "Ma'lumotlar bazasiga hoziroq joylansinmi?\n\n"
        "E'slatma agar hoziroq joylansa shu ondan boshlab yangi jadval asosida ishlanadi!",
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=survey_save_file_markup,
    )


def save_file(file: bytes, filename: str) -> None:
    with open(filename, "wb") as f:
        f.write(file)