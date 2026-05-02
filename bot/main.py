import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import BOT_TOKEN, PROMO_INTERVAL_HOURS
from bot.database.db import init_db
from bot.filters.profanity import load_filters
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.middlewares.tracking import MemberTrackingMiddleware
from bot.handlers import welcome, moderation, commands, sales, member_sync, bulk_invite

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set in .env file!")
        return

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Load moderation filters
    load_filters()
    logger.info("Moderation filters loaded")

    # Create bot and dispatcher
    bot = Bot(token=BOT_TOKEN, default={"parse_mode": ParseMode.HTML})
    dp = Dispatcher(storage=MemoryStorage())

    # Register middleware
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.5))
    dp.message.middleware(MemberTrackingMiddleware())

    # Register routers (order matters — welcome first, moderation last)
    dp.include_router(welcome.router)
    dp.include_router(bulk_invite.router)  # Before moderation (has FSM states)
    dp.include_router(commands.router)
    dp.include_router(sales.router)
    dp.include_router(member_sync.router)  # Passive tracking on all messages
    dp.include_router(moderation.router)   # Must be last (catches all text messages)

    # Setup scheduled promo messages
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        sales.send_scheduled_promo,
        "interval",
        hours=PROMO_INTERVAL_HOURS,
        args=[bot],
    )
    scheduler.start()
    logger.info(f"Scheduled promo every {PROMO_INTERVAL_HOURS} hours")

    # Start polling
    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "chat_member", "callback_query"])
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
