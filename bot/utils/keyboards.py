from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import GHOSTAI_URL, GHOSTAI_PRICING_URL


def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Try GhostAI Free", url=GHOSTAI_URL)],
        [InlineKeyboardButton(text="📋 Community Rules", callback_data="show_rules")],
    ])


def pricing_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 View Pricing & Subscribe", url=GHOSTAI_PRICING_URL)],
        [InlineKeyboardButton(text="🌐 Visit GhostAI", url=GHOSTAI_URL)],
    ])


def promo_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Get GhostAI Now", url=GHOSTAI_URL)],
        [InlineKeyboardButton(text="💰 See Plans", url=GHOSTAI_PRICING_URL)],
    ])


def report_confirm_keyboard(message_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚠️ Warn", callback_data=f"mod_warn:{user_id}"),
            InlineKeyboardButton(text="🔇 Mute", callback_data=f"mod_mute:{user_id}"),
            InlineKeyboardButton(text="🚫 Ban", callback_data=f"mod_ban:{user_id}"),
        ],
        [InlineKeyboardButton(text="✅ Dismiss", callback_data=f"mod_dismiss:{message_id}")],
    ])
