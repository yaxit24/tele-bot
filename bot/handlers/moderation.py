import logging
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ChatPermissions
from aiogram.enums import ChatMemberStatus

from bot.config import ADMIN_IDS, LOG_CHANNEL_ID, MAX_WARNINGS, MUTE_DURATION_MINUTES, BAN_AFTER_WARNINGS
from bot.database.queries import (
    upsert_member, increment_message_count, add_warning,
    log_violation, set_muted, set_banned
)
from bot.filters.profanity import detect_violation
from bot.utils.helpers import mention_user
from bot.utils.keyboards import report_confirm_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text)
async def moderate_message(message: Message, bot: Bot):
    if not message.from_user or message.from_user.is_bot:
        return

    user = message.from_user

    # Skip admins
    if user.id in ADMIN_IDS:
        await increment_message_count(user.id)
        return

    # Ensure member exists in DB
    await upsert_member(user.id, user.username, user.first_name)
    await increment_message_count(user.id)

    # Check for violations
    violation = detect_violation(message.text)
    if not violation:
        return

    # Delete the offending message
    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")

    # Add warning
    warning_count = await add_warning(user.id)

    # Log violation to DB
    action = "warned"
    if warning_count >= BAN_AFTER_WARNINGS:
        action = "banned"
    elif warning_count >= MAX_WARNINGS:
        action = "muted"

    await log_violation(user.id, violation, message.text[:500], action)

    # Take action based on warning count
    chat_id = message.chat.id
    if warning_count >= BAN_AFTER_WARNINGS:
        # Ban
        try:
            await bot.ban_chat_member(chat_id, user.id)
            await set_banned(user.id, True)
            await bot.send_message(
                chat_id,
                f"🚫 {mention_user(user)} has been <b>banned</b> "
                f"({warning_count} warnings — {violation}).",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to ban user {user.id}: {e}")

    elif warning_count >= MAX_WARNINGS:
        # Mute
        try:
            until_date = datetime.utcnow() + timedelta(minutes=MUTE_DURATION_MINUTES)
            await bot.restrict_chat_member(
                chat_id, user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date,
            )
            await set_muted(user.id, MUTE_DURATION_MINUTES)
            await bot.send_message(
                chat_id,
                f"🔇 {mention_user(user)} has been <b>muted</b> for {MUTE_DURATION_MINUTES} min "
                f"({warning_count}/{BAN_AFTER_WARNINGS} warnings — {violation}).",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to mute user {user.id}: {e}")

    else:
        # Warn
        await bot.send_message(
            chat_id,
            f"⚠️ {mention_user(user)} — warning {warning_count}/{MAX_WARNINGS} "
            f"for <b>{violation}</b>. Please follow the rules.",
            parse_mode="HTML"
        )

    # Log to admin channel
    if LOG_CHANNEL_ID:
        try:
            log_text = (
                f"🚨 <b>Violation Detected</b>\n\n"
                f"<b>User:</b> {mention_user(user)} (ID: <code>{user.id}</code>)\n"
                f"<b>Type:</b> {violation}\n"
                f"<b>Action:</b> {action}\n"
                f"<b>Warnings:</b> {warning_count}/{BAN_AFTER_WARNINGS}\n"
                f"<b>Message:</b> <code>{message.text[:200]}</code>\n"
                f"<b>Chat:</b> {message.chat.title}"
            )
            await bot.send_message(
                LOG_CHANNEL_ID, log_text,
                parse_mode="HTML",
                reply_markup=report_confirm_keyboard(message.message_id, user.id),
            )
        except Exception as e:
            logger.error(f"Failed to send log: {e}")


@router.message(F.text.startswith("/report"))
async def handle_report(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("↩️ Reply to a message with /report to report it.")
        return

    reported_msg = message.reply_to_message
    reported_user = reported_msg.from_user
    reporter = message.from_user

    if not reported_user:
        return

    # Delete the /report command to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    # Send to admin log channel
    if LOG_CHANNEL_ID:
        log_text = (
            f"📢 <b>User Report</b>\n\n"
            f"<b>Reported by:</b> {mention_user(reporter)}\n"
            f"<b>Reported user:</b> {mention_user(reported_user)} "
            f"(ID: <code>{reported_user.id}</code>)\n"
            f"<b>Message:</b> <code>{reported_msg.text[:300] if reported_msg.text else '[media]'}</code>\n"
            f"<b>Chat:</b> {message.chat.title}"
        )
        try:
            await bot.send_message(
                LOG_CHANNEL_ID, log_text,
                parse_mode="HTML",
                reply_markup=report_confirm_keyboard(reported_msg.message_id, reported_user.id),
            )
            # Notify reporter via reply
            notification = await message.answer("✅ Report submitted. Admins will review it.")
            # Auto-delete notification after 5 seconds
            import asyncio
            await asyncio.sleep(5)
            await notification.delete()
        except Exception as e:
            logger.error(f"Failed to send report: {e}")
