from bot.bot import start_bot
from services.scheduler import scheduler_loop
from services.webhook_server import runner
from db.schemas import init_db
from config.utils import WEBHOOK_USE
import asyncio


async def main():
    init_db()

    if WEBHOOK_USE:
        # Run the webhook server and the scheduler concurrently in the same loop.
        await asyncio.gather(runner(), scheduler_loop())
    else:
        # Run the polling loop and the scheduler concurrently.
        await asyncio.gather(start_bot(), scheduler_loop())


if __name__ == "__main__":
    asyncio.run(main())
