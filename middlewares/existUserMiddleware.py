from aiogram import BaseMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.engine import engine
from db.schemas import Role, User
from typing import Any, Awaitable, Callable, Dict


class existUserMiddleware(BaseMiddleware):
    """Auto-register users on first interaction and inject them into handlers."""

    def __init__(self):
        super().__init__()
        self._imported = False
        self._bot = None
        self._owner_chat_id = None

    def _lazy_import(self):
        # Lazy import to avoid a circular import at module load time.
        if not self._imported:
            from bot.bootstrap import bot
            from config.utils import OWNER_CHAT_ID

            self._bot = bot
            self._owner_chat_id = OWNER_CHAT_ID
            self._imported = True

    async def _notify_owner(self, chat_id: int):
        self._lazy_import()
        if not self._owner_chat_id or self._bot is None:
            return
        try:
            await self._bot.send_message(
                chat_id=self._owner_chat_id,
                text=f"🆕 Yangi foydalanuvchi botga qo'shildi!\n\n🆔 ID: {chat_id}",
            )
        except Exception:
            # Skip if the owner can't be reached (blocked bot, etc.)
            pass

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ):

        event_user = getattr(event, "from_user", None)

        if not event_user:

            data["user_exist"] = False

            return await handler(event, data)

        is_new = False
        with Session(engine) as session:
            statement = select(User).where(User.chat_id == event_user.id)
            result = session.execute(statement)
            user = result.scalar_one_or_none()

            # Auto-register the user if they don't exist yet.
            if user is None:
                user = User(
                    chat_id=event_user.id,
                    auto_send=False,
                    sms_service=False,
                    tables=[],
                )
                session.add(user)
                session.flush()
                session.add(Role(role="user", user_id=user.id))
                session.commit()
                session.refresh(user)
                is_new = True

            data["user_exist"] = True
            data["user"] = user

        if is_new:
            await self._notify_owner(event_user.id)

        return await handler(event, data)
