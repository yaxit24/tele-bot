import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message

from bot.config import MAIN_GROUP_ID
from bot.services.member_manager import register_group, track_member_in_group

logger = logging.getLogger(__name__)


class MemberTrackingMiddleware(BaseMiddleware):
    """Silently tracks every user who sends a message in any group.
    Runs as middleware so it doesn't consume the message — other handlers still fire."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user and not event.from_user.is_bot:
            if event.chat and event.chat.type in ("group", "supergroup"):
                try:
                    await register_group(
                        group_id=event.chat.id,
                        group_name=event.chat.title or "Unknown",
                        is_main=(event.chat.id == MAIN_GROUP_ID),
                    )
                    await track_member_in_group(
                        user_id=event.from_user.id,
                        group_id=event.chat.id,
                        username=event.from_user.username,
                        first_name=event.from_user.first_name,
                    )
                except Exception as e:
                    logger.error(f"Tracking error: {e}")

        return await handler(event, data)
