from aiogram import BaseMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.engine import engine
from db.schemas import User
from typing import Any, Awaitable, Callable, Dict


class existUserMiddleware(BaseMiddleware):

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

        with Session(engine) as session:

            statement = select(User).where(User.chat_id == event_user.id)

            result = session.execute(statement)

            user = result.scalar_one_or_none()

            data["user_exist"] = bool(user)

            data["user"] = user

        return await handler(event, data)
