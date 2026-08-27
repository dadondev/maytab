import asyncio
import os

from fastapi import FastAPI, Request, Response

from bot.bot import dp, bot, setup, notify_owner_started
from config.utils import (
    WEBHOOK_DOMAIN,
    WEBHOOK_PATH,
)

# FastAPI application — this is the ASGI app that uvicorn loads (uvicorn main:app).
app = FastAPI(title="Maytab Telegram Bot")


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize the DB, register routers, set the webhook, and start the scheduler."""
    setup()

    # Set the Telegram webhook so updates are delivered to this server.
    try:
        await bot.set_webhook(f"{WEBHOOK_DOMAIN}{WEBHOOK_PATH}")
    except Exception as exc:
        print(f"[startup] set_webhook failed: {exc!r}")

    # Notify the owner that the bot is running.
    try:
        await notify_owner_started()
    except Exception as exc:
        print(f"[startup] notify_owner_started failed: {exc!r}")

    # Start the background scheduler (daily sends + task execution).
    from services.scheduler import scheduler_loop

    asyncio.create_task(scheduler_loop())


@app.post(WEBHOOK_PATH)
async def webhook(request: Request) -> Response:
    """Receive a Telegram update and process it with the dispatcher."""
    from aiogram.types import Update

    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return Response(status_code=200)


@app.get("/")
async def root() -> dict:
    """Health check."""
    return {"status": "ok", "bot": "maytab"}


def main():
    """Run the app with uvicorn (used by `python main.py`)."""
    import uvicorn

    port = int(os.getenv("PORT") or os.getenv("WEBHOOK_PORT") or "8080")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
