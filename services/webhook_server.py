import asyncio

from aiohttp import web

from bot.bot import dp, setup_bot
from bot.bootstrap import bot
from config.utils import (
    WEBHOOK_DOMAIN,
    WEBHOOK_PATH,
    WEBHOOK_SECRET,
    WEBHOOK_PORT,
)

# Build the aiohttp application once (import-safe).
app = web.Application()


async def _healthcheck(request):
    """Simple health check so Railway knows the app is alive."""
    return web.json_response({"status": "ok", "bot": "maytab"})


app.router.add_get("/", _healthcheck)


async def runner():
    """Start the aiohttp webhook server inside the current event loop.

    Must be awaited so it can run concurrently with the scheduler.
    It runs until the server is stopped / connection is closed.
    """
    setup_bot()

    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    # SimpleRequestHandler handles incoming webhook updates.
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)

    if WEBHOOK_SECRET:
        app.middlewares.append(_secret_token_middleware)

    # Set the webhook on startup.
    await bot.set_webhook(
        f"{WEBHOOK_DOMAIN}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET or None,
    )

    setup_application(app, dp, bot=bot)

    runner_app = web.AppRunner(app)
    await runner_app.setup()
    site = web.TCPSite(runner_app, host="0.0.0.0", port=WEBHOOK_PORT)
    await site.start()

    try:
        # Keep the server running indefinitely.
        await asyncio.Event().wait()
    finally:
        await runner_app.cleanup()
        await bot.delete_webhook()


async def _secret_token_middleware(app, handler):
    async def middleware(request):
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if WEBHOOK_SECRET and token != WEBHOOK_SECRET:
            return web.Response(status=403)
        return await handler(request)

    return middleware