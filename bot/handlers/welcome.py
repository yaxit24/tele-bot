import logging
from aiogram import Router, F, Bot
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER

from bot.config import MAIN_GROUP_ID
from bot.database.queries import upsert_member, set_welcomed, get_setting
from bot.utils.keyboards import welcome_keyboard

logger = logging.getLogger(__name__)
router = Router()

DEFAULT_WELCOME = (
    "Welcome to the GhostAI Community, {name}! 🎉\n\n"
    "We're glad to have you here. This community is all about helping each other "
    "ace interviews and online exams using AI.\n\n"
    "🤖 <b>What is GhostAI?</b>\n"
    "An AI Interview Assistant that works on every platform — any online exam or "
    "interview, GhostAI has your back.\n\n"
    "📋 <b>Quick Rules:</b>\n"
    "• Be respectful — no abuse, spam, or inappropriate content\n"
    "• Help each other out\n"
    "• No self-promotion without permission\n\n"
    "Hit the button below to try GhostAI and crush your next interview! 👇"
)


@router.my_chat_member()
async def on_bot_status_change(event: ChatMemberUpdated):
    """Handle bot's own membership changes (added/removed/promoted)."""
    logger.info(
        f"Bot status changed in {event.chat.title}: "
        f"{event.old_chat_member.status} -> {event.new_chat_member.status}"
    )


@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_new_member(event: ChatMemberUpdated, bot: Bot):
    user = event.new_chat_member.user
    logger.info(f"New member detected: {user.id} ({user.first_name}) in chat {event.chat.id}")
    if user.is_bot:
        return

    # Save member to DB
    await upsert_member(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        source_group_id=event.chat.id,
    )

    # Only send welcome in main community
    if MAIN_GROUP_ID and event.chat.id != MAIN_GROUP_ID:
        return

    # Get custom welcome message or use default
    custom_welcome = await get_setting("welcome_message")
    template = custom_welcome or DEFAULT_WELCOME

    name = user.first_name or "there"
    welcome_text = template.format(name=name)

    try:
        await bot.send_message(
            chat_id=event.chat.id,
            text=welcome_text,
            reply_markup=welcome_keyboard(),
            parse_mode="HTML",
        )
        await set_welcomed(user.id)
        logger.info(f"Welcomed new member: {user.id} ({user.username})")
    except Exception as e:
        logger.error(f"Failed to send welcome message: {e}")
