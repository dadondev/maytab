from bot.bot import start_bot
from services.scheduler import scheduler_loop
from db.schemas import init_db
import asyncio


async def main():
    init_db()
    # Run the polling loop and the scheduler concurrently.
    await asyncio.gather(start_bot(), scheduler_loop())


if __name__ == "__main__":
    asyncio.run(main())
