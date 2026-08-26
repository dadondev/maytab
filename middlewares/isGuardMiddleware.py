from aiogram import BaseMiddleware
from typing import Any, Awaitable, Callable, Dict
from bot.bootstrap import bot
from db.queries import get_user_role


class isGuardMiddleware(BaseMiddleware):
    """Allow only users with the 'guard' role (admins are also allowed)."""

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ):
        from_user = getattr(event, "from_user", None)
        if from_user is None:
            return

        role = get_user_role(from_user.id)
        if role and role.role in ("guard", "admin"):
            return await handler(event, data)

        await bot.send_message(
            chat_id=from_user.id,
            text="Ushbu buyruq faqat qo'riqchilar uchun mo'jallangan!",
        )