"""FastAPI entry point for deploying the bot on Vercel.

Vercel runs Python as serverless ASGI functions, so there is no long-running
process. This module exposes a FastAPI `app` that receives Telegram webhook
updates and feeds them into the aiogram dispatcher.

NOTE: The background scheduler (services/scheduler.py) cannot run on Vercel
because serverless functions are short-lived. Scheduled sends (daily
timetables, task execution) must be triggered externally (e.g. a cron job
hitting a protected endpoint) or run on a separate always-on host.

IMPORTANT: The bot modules are imported lazily (inside handlers) so that a
failure in the bot/DB import chain does NOT crash the serverless function at
import time (which would surface as FUNCTION_INVOCATION_FAILED). Instead, the
error is logged and a readable response is returned.
"""

from fastapi import FastAPI, Request, Response

from config.utils import (
    WEBHOOK_DOMAIN,
    WEBHOOK_PATH,
    WEBHOOK_SECRET,
)

app = FastAPI(title="Maytab Telegram Bot Webhook")

# Lazy-loaded on first use.
_bot = None
_dp = None


def _load_bot():
    """Import and cache the bot/dispatcher. Raises on failure."""
    global _bot, _dp
    if _bot is None or _dp is None:
        from bot.bot import dp, bot, setup

        setup()
        _bot = bot
        _dp = dp
    return _bot, _dp


@app.on_event("startup")
async def on_startup() -> None:
    """Set the Telegram webhook and notify the owner.

    Errors are caught so a DB/filesystem problem doesn't crash the serverless
    function (which would surface as FUNCTION_INVOCATION_FAILED).
    """
    try:
        bot, _ = _load_bot()
        await bot.set_webhook(
            f"{WEBHOOK_DOMAIN}{WEBHOOK_PATH}",
            secret_token=WEBHOOK_SECRET or None,
        )
    except Exception as exc:
        print(f"[startup] bot init / set_webhook failed: {exc!r}")
    try:
        from bot.bot import notify_owner_started

        await notify_owner_started()
    except Exception as exc:
        print(f"[startup] notify_owner_started failed: {exc!r}")


@app.post(WEBHOOK_PATH)
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = None,
) -> Response:
    """Receive a Telegram update and process it with the dispatcher."""
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        return Response(status_code=403)

    try:
        bot, dp = _load_bot()
    except Exception as exc:
        print(f"[webhook] bot init failed: {exc!r}")
        return Response(status_code=500, content=f"bot init failed: {exc!r}")

    from aiogram.types import Update

    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return Response(status_code=200)


@app.get("/")
async def root() -> dict:
    """Health check that also reports whether the bot loaded."""
    try:
        _load_bot()
        bot_status = "ok"
    except Exception as exc:
        bot_status = f"error: {exc!r}"
    return {"status": "ok", "bot": bot_status, "webhook_path": WEBHOOK_PATH}