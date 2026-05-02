import asyncio
import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot

from bot.config import MAIN_GROUP_ID, INVITE_RATE_PER_HOUR, GHOSTAI_URL
from bot.database.db import get_db

logger = logging.getLogger(__name__)

# Global reference to the running job
_current_job: Optional[asyncio.Task] = None
_current_job_id: Optional[int] = None


def get_invite_message(first_name: str, invite_link: str) -> str:
    name = first_name or "there"
    return (
        f"Hey {name}! 👋\n\n"
        f"I noticed you're active in some Telegram groups related to interviews & exams.\n\n"
        f"We have an exclusive community where people share tips, resources, and get access "
        f"to <b>GhostAI</b> — an AI Interview Assistant that works on every platform.\n\n"
        f"🎯 Real-time AI help during interviews\n"
        f"🎯 Works on any online exam platform\n"
        f"🎯 Join 1000+ users already crushing interviews\n\n"
        f"👉 <b>Join our community:</b> {invite_link}\n\n"
        f"🌐 Learn more: {GHOSTAI_URL}"
    )


def get_followup_message(first_name: str, invite_link: str) -> str:
    name = first_name or "there"
    return (
        f"Hey {name}, just a quick follow-up! 🙌\n\n"
        f"Our community is growing fast — people are sharing interview experiences, "
        f"mock practice sessions, and exclusive GhostAI tips.\n\n"
        f"Don't miss out! Join us here 👉 {invite_link}\n\n"
        f"No spam, just value. See you inside! ✌️"
    )


async def create_invite_job(user_ids: list) -> int:
    db = await get_db()
    try:
        cursor = await db.execute("""
            INSERT INTO invite_jobs (status, total_ids) VALUES ('running', ?)
        """, (len(user_ids),))
        job_id = cursor.lastrowid

        for uid in user_ids:
            await db.execute("""
                INSERT INTO invite_targets (job_id, user_id, status) VALUES (?, ?, 'pending')
            """, (job_id, uid))
        await db.commit()
        return job_id
    finally:
        await db.close()


async def get_job_status(job_id: int) -> dict:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM invite_jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
    finally:
        await db.close()
    if not row:
        return None
    return {
        "id": row[0],
        "status": row[1],
        "total_ids": row[2],
        "sent": row[3],
        "skipped": row[4],
        "unreachable": row[5],
        "failed": row[6],
        "created_at": row[7],
        "completed_at": row[8],
    }


async def cancel_job(job_id: int):
    global _current_job, _current_job_id
    if _current_job and not _current_job.done():
        _current_job.cancel()
    db = await get_db()
    try:
        await db.execute(
            "UPDATE invite_jobs SET status = 'cancelled', completed_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), job_id)
        )
        await db.commit()
    finally:
        await db.close()
    _current_job = None
    _current_job_id = None


async def run_invite_job(bot: Bot, job_id: int):
    global _current_job_id
    _current_job_id = job_id

    # Generate invite link for main group
    try:
        invite_link_obj = await bot.create_chat_invite_link(
            MAIN_GROUP_ID,
            name=f"bulk_invite_job_{job_id}",
        )
        invite_link = invite_link_obj.invite_link
    except Exception as e:
        logger.error(f"Failed to create invite link: {e}")
        invite_link = f"https://t.me/+placeholder"  # fallback

    delay_seconds = 3600 / INVITE_RATE_PER_HOUR  # e.g., 20/hr = 180s between each

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, user_id FROM invite_targets WHERE job_id = ? AND status = 'pending'",
            (job_id,)
        )
        targets = await cursor.fetchall()
    finally:
        await db.close()

    sent = 0
    skipped = 0
    unreachable = 0
    failed = 0

    for target_id, user_id in targets:
        # Check if job was cancelled
        db = await get_db()
        try:
            job_row = await (await db.execute(
                "SELECT status FROM invite_jobs WHERE id = ?", (job_id,)
            )).fetchone()
        finally:
            await db.close()

        if not job_row or job_row[0] == 'cancelled':
            logger.info(f"Job {job_id} cancelled, stopping.")
            return

        # Check if user is already in community
        db = await get_db()
        try:
            in_community = await (await db.execute(
                "SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?",
                (MAIN_GROUP_ID, user_id)
            )).fetchone()
        finally:
            await db.close()

        if in_community:
            await _update_target(target_id, 'skipped')
            skipped += 1
            await _update_job_counts(job_id, sent, skipped, unreachable, failed)
            continue

        # Try to get user info for personalized message
        db = await get_db()
        try:
            member_row = await (await db.execute(
                "SELECT first_name FROM members WHERE user_id = ?", (user_id,)
            )).fetchone()
        finally:
            await db.close()
        first_name = member_row[0] if member_row else None

        # Try to send DM
        try:
            msg_text = get_invite_message(first_name, invite_link)
            await bot.send_message(user_id, msg_text, parse_mode="HTML")
            await _update_target(target_id, 'sent')
            sent += 1
            logger.info(f"Invite sent to {user_id}")
        except Exception as e:
            error_str = str(e).lower()
            if "bot was blocked" in error_str or "user is deactivated" in error_str or "chat not found" in error_str:
                await _update_target(target_id, 'unreachable')
                unreachable += 1
            else:
                await _update_target(target_id, 'failed')
                failed += 1
                logger.error(f"Failed to invite {user_id}: {e}")

        await _update_job_counts(job_id, sent, skipped, unreachable, failed)

        # Rate limit delay
        await asyncio.sleep(delay_seconds)

    # Mark job as completed
    db = await get_db()
    try:
        await db.execute(
            "UPDATE invite_jobs SET status = 'completed', completed_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), job_id)
        )
        await db.commit()
    finally:
        await db.close()

    _current_job_id = None
    logger.info(f"Job {job_id} completed: sent={sent}, skipped={skipped}, unreachable={unreachable}, failed={failed}")


async def _update_target(target_id: int, status: str):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE invite_targets SET status = ?, last_attempt = ?, attempts = attempts + 1 WHERE id = ?",
            (status, datetime.utcnow().isoformat(), target_id)
        )
        await db.commit()
    finally:
        await db.close()


async def _update_job_counts(job_id: int, sent: int, skipped: int, unreachable: int, failed: int):
    db = await get_db()
    try:
        await db.execute("""
            UPDATE invite_jobs SET sent = ?, skipped = ?, unreachable = ?, failed = ?
            WHERE id = ?
        """, (sent, skipped, unreachable, failed, job_id))
        await db.commit()
    finally:
        await db.close()


def start_invite_job(bot: Bot, job_id: int):
    global _current_job
    _current_job = asyncio.create_task(run_invite_job(bot, job_id))
    return _current_job


def is_job_running() -> bool:
    return _current_job is not None and not _current_job.done()


def get_current_job_id() -> Optional[int]:
    return _current_job_id
