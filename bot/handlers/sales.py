import logging
from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.config import ADMIN_IDS, MAIN_GROUP_ID, GHOSTAI_URL, GHOSTAI_PRICING_URL
from bot.utils.keyboards import pricing_keyboard, promo_keyboard

logger = logging.getLogger(__name__)
router = Router()

PROMO_MESSAGES = [
    (
        "🚀 <b>Ace Your Next Interview with GhostAI</b>\n\n"
        "Works on <b>every platform</b> — Google Meet, Zoom, Teams, HackerRank, "
        "Codility, and more.\n\n"
        "✅ Real-time AI assistance during interviews\n"
        "✅ Works on any online exam\n"
        "✅ Undetectable & seamless\n\n"
        "Join 1000+ users who already cracked their dream job 👇"
    ),
    (
        "💼 <b>Tired of failing interviews?</b>\n\n"
        "GhostAI is your secret weapon. It listens to your interview in real-time "
        "and gives you the perfect answers.\n\n"
        "🎯 Works on ANY platform\n"
        "🎯 Online exams, coding tests, HR rounds — all covered\n"
        "🎯 Setup in 2 minutes\n\n"
        "Don't miss your next opportunity 👇"
    ),
    (
        "🎯 <b>Your AI Interview Cheat Code</b>\n\n"
        "GhostAI helps you:\n"
        "• Answer technical questions instantly\n"
        "• Solve coding problems in real-time\n"
        "• Pass HR screening rounds effortlessly\n"
        "• Ace online assessments on any platform\n\n"
        "Start your free trial today 👇"
    ),
]

_promo_index = 0


# ─── /pricing ────────────────────────────────────────────────────────────────

@router.message(Command("pricing"))
async def cmd_pricing(message: Message):
    text = (
        "💰 <b>GhostAI Pricing</b>\n\n"
        "🤖 AI Interview Assistant that works on every platform.\n\n"
        f"🌐 Visit {GHOSTAI_PRICING_URL} to see all plans and subscribe.\n\n"
        "Questions? Ask in this group and we'll help you out!"
    )
    await message.reply(text, reply_markup=pricing_keyboard(), parse_mode="HTML")


# ─── /promote (admin only) ───────────────────────────────────────────────────

@router.message(Command("promote"))
async def cmd_promote(message: Message, bot: Bot):
    if message.from_user.id not in ADMIN_IDS:
        return

    global _promo_index
    promo_text = PROMO_MESSAGES[_promo_index % len(PROMO_MESSAGES)]
    _promo_index += 1

    chat_id = message.chat.id
    await bot.send_message(
        chat_id, promo_text,
        reply_markup=promo_keyboard(),
        parse_mode="HTML"
    )


# ─── Scheduled promo (called by APScheduler) ────────────────────────────────

async def send_scheduled_promo(bot: Bot):
    if not MAIN_GROUP_ID:
        return

    global _promo_index
    promo_text = PROMO_MESSAGES[_promo_index % len(PROMO_MESSAGES)]
    _promo_index += 1

    try:
        await bot.send_message(
            MAIN_GROUP_ID, promo_text,
            reply_markup=promo_keyboard(),
            parse_mode="HTML"
        )
        logger.info("Scheduled promo sent")
    except Exception as e:
        logger.error(f"Failed to send scheduled promo: {e}")


# ─── Callback: show_rules ───────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "show_rules")
async def callback_show_rules(callback: CallbackQuery):
    from bot.database.queries import get_setting
    rules = await get_setting("community_rules")
    if not rules:
        rules = (
            "📋 <b>Community Rules</b>\n\n"
            "1. Be respectful to everyone\n"
            "2. No spam, self-promotion, or ads\n"
            "3. No abusive, sexual, or inappropriate content\n"
            "4. No sharing pirated content\n"
            "5. Help each other grow!"
        )
    await callback.answer()
    await callback.message.answer(rules, parse_mode="HTML")
