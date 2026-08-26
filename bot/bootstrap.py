from aiogram import Bot
from config.utils import TOKEN

# Central Bot instance, isolated from routers/handlers to avoid circular imports.
bot = Bot(token=TOKEN)