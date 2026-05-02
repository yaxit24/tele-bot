import logging

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command

from bot.config import ADMIN_IDS, MAIN_GROUP_ID
from bot.services.member_manager import (
    get_members_not_in_community, get_tracked_groups, get_discovery_stats
)

logger = logging.getLogger(__name__)
router = Router()

# NOTE: Passive member tracking is handled by MemberTrackingMiddleware
# in bot/middlewares/tracking.py — it runs on every message without
# consuming it, so other handlers (moderation, commands) still fire.


# ─── /discover — show members NOT in your community ─────────────────────────

@router.message(Command("discover"))
async def cmd_discover(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    if not MAIN_GROUP_ID:
        await message.reply("❌ MAIN_GROUP_ID not configured in .env")
        return

    members = await get_members_not_in_community(limit=20)

    if not members:
        await message.reply("✅ No new members to discover. All tracked users are already in your community!")
        return

    stats = await get_discovery_stats()

    text = (
        f"🔍 <b>Member Discovery</b>\n\n"
        f"📊 Tracked: {stats['total_tracked']} | "
        f"In community: {stats['in_community']} | "
        f"Potential: {stats['not_in_community']}\n\n"
        f"<b>Top prospects (not in your community):</b>\n\n"
    )

    for i, m in enumerate(members, 1):
        username_display = f"@{m['username']}" if m['username'] else m['first_name'] or 'Unknown'
        text += (
            f"{i}. {username_display} "
            f"(ID: <code>{m['user_id']}</code>)\n"
            f"   💬 {m['message_count']} msgs | "
            f"📂 {m['group_count']} group(s): {m['group_names']}\n\n"
        )

    text += f"\n💡 Use /invite_bulk to send invite links to these users."
    await message.reply(text, parse_mode="HTML")


# ─── /groups — show all tracked groups ───────────────────────────────────────

@router.message(Command("groups"))
async def cmd_groups(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    groups = await get_tracked_groups()

    if not groups:
        await message.reply("No groups tracked yet. Add the bot to groups as admin.")
        return

    text = "📂 <b>Tracked Groups</b>\n\n"
    for g in groups:
        main_tag = " ⭐ MAIN" if g['is_main'] else ""
        text += f"• <b>{g['group_name']}</b>{main_tag}\n  ID: <code>{g['group_id']}</code> | 👥 {g['member_count']} tracked\n\n"

    await message.reply(text, parse_mode="HTML")
