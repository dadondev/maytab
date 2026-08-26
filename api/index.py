"""FastAPI entry point for deploying the bot on Vercel.

Vercel runs Python as serverless ASGI functions, so there is no long-running
process. This module exposes a FastAPI `app` that receives Telegram webhook
updates and feeds them into the aiogram dispatcher.

NOTE: The background scheduler (services/scheduler.py) cannot run on Vercel
because serverless functions are short-lived. Scheduled sends (daily
timetables, task execution) must be triggered externally (e.g. a cron job
hitting a protected endpoint) or run on a separate always-on host.
"""

from fastapi import FastAPI, Request, Response, Header

from bot.bot import dp, bot, setup
from config.utils import (
    WEBHOOK_DOMAIN,
    WEBHOOK_PATH,
    WEBHOOK_SECRET,
)

app = FastAPI(title="Maytab Telegram Bot Webhook")


@app.on_event("startup")
async def on_startup() -> None:
    """Register routers and set the Telegram webhook on cold start."""
    setup()
    await bot.set_webhook(
        f"{WEBHOOK_DOMAIN}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET or None,
    )


@app.post(WEBHOOK_PATH)
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = None,
) -> Response:
    """Receive a Telegram update and process it with the dispatcher."""
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        return Response(status_code=403)

    from aiogram.types import Update

    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return Response(status_code=200)


@app.get("/")
async def root() -> dict:
    return {"status": "ok", "bot": "maytab"}