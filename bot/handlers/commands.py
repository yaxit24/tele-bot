import logging
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ChatPermissions
from aiogram.filters import Command

from bot.config import (
    ADMIN_IDS, MAIN_GROUP_ID, MUTE_DURATION_MINUTES, BAN_AFTER_WARNINGS
)
from bot.database.queries import (
    add_warning, clear_warnings, get_warnings, get_stats,
    set_muted, set_unmuted, set_banned, get_setting, set_setting
)
from bot.utils.helpers import mention_user, format_duration

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def get_target_user(message: Message):
    """Get target user from reply or mention."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    return None


# ─── /ban ────────────────────────────────────────────────────────────────────

@router.message(Command("ban"))
async def cmd_ban(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    target = get_target_user(message)
    if not target:
        await message.reply("↩️ Reply to a user's message to ban them.")
        return

    try:
        await bot.ban_chat_member(message.chat.id, target.id)
        await set_banned(target.id, True)
        await message.reply(
            f"🚫 {mention_user(target)} has been <b>banned</b>.",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.reply(f"❌ Failed to ban: {e}")


# ─── /unban ──────────────────────────────────────────────────────────────────

@router.message(Command("unban"))
async def cmd_unban(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    target = get_target_user(message)
    if not target:
        await message.reply("↩️ Reply to a user's message to unban them.")
        return

    try:
        await bot.unban_chat_member(message.chat.id, target.id, only_if_banned=True)
        await set_banned(target.id, False)
        await message.reply(
            f"✅ {mention_user(target)} has been <b>unbanned</b>.",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.reply(f"❌ Failed to unban: {e}")


# ─── /mute ───────────────────────────────────────────────────────────────────

@router.message(Command("mute"))
async def cmd_mute(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    target = get_target_user(message)
    if not target:
        await message.reply("↩️ Reply to a user's message to mute them.\nUsage: /mute [minutes]")
        return

    # Parse duration from command args
    args = message.text.split()
    duration = MUTE_DURATION_MINUTES
    if len(args) > 1:
        try:
            duration = int(args[1])
        except ValueError:
            pass

    try:
        until_date = datetime.utcnow() + timedelta(minutes=duration)
        await bot.restrict_chat_member(
            message.chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date,
        )
        await set_muted(target.id, duration)
        await message.reply(
            f"🔇 {mention_user(target)} has been <b>muted</b> for {format_duration(duration)}.",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.reply(f"❌ Failed to mute: {e}")


# ─── /unmute ─────────────────────────────────────────────────────────────────

@router.message(Command("unmute"))
async def cmd_unmute(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    target = get_target_user(message)
    if not target:
        await message.reply("↩️ Reply to a user's message to unmute them.")
        return

    try:
        await bot.restrict_chat_member(
            message.chat.id, target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await set_unmuted(target.id)
        await message.reply(
            f"🔊 {mention_user(target)} has been <b>unmuted</b>.",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.reply(f"❌ Failed to unmute: {e}")


# ─── /warn ───────────────────────────────────────────────────────────────────

@router.message(Command("warn"))
async def cmd_warn(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    target = get_target_user(message)
    if not target:
        await message.reply("↩️ Reply to a user's message to warn them.\nUsage: /warn [reason]")
        return

    args = message.text.split(maxsplit=1)
    reason = args[1] if len(args) > 1 else "No reason specified"

    count = await add_warning(target.id)
    await message.reply(
        f"⚠️ {mention_user(target)} warned ({count}/{BAN_AFTER_WARNINGS}).\n"
        f"Reason: {reason}",
        parse_mode="HTML"
    )


# ─── /warnings ───────────────────────────────────────────────────────────────

@router.message(Command("warnings"))
async def cmd_warnings(message: Message):
    if not is_admin(message.from_user.id):
        return

    target = get_target_user(message)
    if not target:
        await message.reply("↩️ Reply to a user's message to check warnings.")
        return

    count = await get_warnings(target.id)
    await message.reply(
        f"📊 {mention_user(target)} has <b>{count}/{BAN_AFTER_WARNINGS}</b> warnings.",
        parse_mode="HTML"
    )


# ─── /clearwarnings ──────────────────────────────────────────────────────────

@router.message(Command("clearwarnings"))
async def cmd_clearwarnings(message: Message):
    if not is_admin(message.from_user.id):
        return

    target = get_target_user(message)
    if not target:
        await message.reply("↩️ Reply to a user's message to clear warnings.")
        return

    await clear_warnings(target.id)
    await message.reply(
        f"✅ Warnings cleared for {mention_user(target)}.",
        parse_mode="HTML"
    )


# ─── /stats ──────────────────────────────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = await get_stats()
    text = (
        f"📊 <b>Community Stats</b>\n\n"
        f"👥 Total members: <b>{stats['total_members']}</b>\n"
        f"⚠️ Warned members: <b>{stats['warned_members']}</b>\n"
        f"🚫 Banned members: <b>{stats['banned_members']}</b>\n"
        f"🚨 Violations today: <b>{stats['violations_today']}</b>"
    )
    await message.reply(text, parse_mode="HTML")


# ─── /setwelcome ─────────────────────────────────────────────────────────────

@router.message(Command("setwelcome"))
async def cmd_setwelcome(message: Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "Usage: /setwelcome [message]\n"
            "Use {name} as placeholder for user's name."
        )
        return

    await set_setting("welcome_message", args[1])
    await message.reply("✅ Welcome message updated!")


# ─── /setrules ───────────────────────────────────────────────────────────────

@router.message(Command("setrules"))
async def cmd_setrules(message: Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Usage: /setrules [rules text]")
        return

    await set_setting("community_rules", args[1])
    await message.reply("✅ Community rules updated!")


# ─── /rules ──────────────────────────────────────────────────────────────────

@router.message(Command("rules"))
async def cmd_rules(message: Message):
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
    await message.reply(rules, parse_mode="HTML")


# ─── /analytics ──────────────────────────────────────────────────────────────

@router.message(Command("analytics"))
async def cmd_analytics(message: Message):
    if not is_admin(message.from_user.id):
        return

    from bot.services.member_manager import get_discovery_stats, get_tracked_groups
    stats = await get_stats()
    discovery = await get_discovery_stats()
    groups = await get_tracked_groups()

    text = (
        f"📈 <b>Community Analytics</b>\n\n"
        f"<b>Members:</b>\n"
        f"  👥 Total: {stats['total_members']}\n"
        f"  ⚠️ Warned: {stats['warned_members']}\n"
        f"  🚫 Banned: {stats['banned_members']}\n\n"
        f"<b>Discovery:</b>\n"
        f"  🔍 Total tracked across groups: {discovery['total_tracked']}\n"
        f"  ✅ In community: {discovery['in_community']}\n"
        f"  🎯 Potential invites: {discovery['not_in_community']}\n\n"
        f"<b>Groups tracked:</b> {len(groups)}\n"
        f"<b>Violations today:</b> {stats['violations_today']}"
    )
    await message.reply(text, parse_mode="HTML")


# ─── /funnel ─────────────────────────────────────────────────────────────────

@router.message(Command("funnel"))
async def cmd_funnel(message: Message):
    if not is_admin(message.from_user.id):
        return

    from bot.database.db import get_db
    db = await get_db()

    # Get overall invite funnel stats
    total_invited = await (await db.execute(
        "SELECT COUNT(*) FROM invite_targets"
    )).fetchone()
    sent = await (await db.execute(
        "SELECT COUNT(*) FROM invite_targets WHERE status = 'sent'"
    )).fetchone()
    joined = await (await db.execute(
        "SELECT COUNT(*) FROM invite_targets WHERE status = 'joined'"
    )).fetchone()
    unreachable = await (await db.execute(
        "SELECT COUNT(*) FROM invite_targets WHERE status = 'unreachable'"
    )).fetchone()

    await db.close()

    total = total_invited[0]
    if total == 0:
        await message.reply("📊 No invite data yet. Use /invite_bulk to start inviting.")
        return

    sent_count = sent[0]
    joined_count = joined[0]
    conversion = (joined_count / sent_count * 100) if sent_count > 0 else 0

    text = (
        f"📊 <b>Invite Funnel</b>\n\n"
        f"Total targeted: {total}\n"
        f"✅ Invites sent: {sent_count}\n"
        f"🎉 Joined: {joined_count}\n"
        f"❌ Unreachable: {unreachable[0]}\n\n"
        f"📈 <b>Conversion rate:</b> {conversion:.1f}%"
    )
    await message.reply(text, parse_mode="HTML")


# ─── Callback: mod actions from log channel ──────────────────────────────────

@router.callback_query(F.data.startswith("mod_"))
async def handle_mod_callback(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Only admins can do this.", show_alert=True)
        return

    action, value = callback.data.split(":", 1)
    user_id = int(value)

    if action == "mod_warn":
        count = await add_warning(user_id)
        await callback.answer(f"Warning added ({count}/{BAN_AFTER_WARNINGS})")

    elif action == "mod_mute":
        await set_muted(user_id, MUTE_DURATION_MINUTES)
        if MAIN_GROUP_ID:
            try:
                until_date = datetime.utcnow() + timedelta(minutes=MUTE_DURATION_MINUTES)
                await bot.restrict_chat_member(
                    MAIN_GROUP_ID, user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until_date,
                )
            except Exception:
                pass
        await callback.answer(f"User muted for {MUTE_DURATION_MINUTES} min")

    elif action == "mod_ban":
        await set_banned(user_id, True)
        if MAIN_GROUP_ID:
            try:
                await bot.ban_chat_member(MAIN_GROUP_ID, user_id)
            except Exception:
                pass
        await callback.answer("User banned")

    elif action == "mod_dismiss":
        await callback.answer("Report dismissed")

    # Update the message to show action taken
    await callback.message.edit_reply_markup(reply_markup=None)
