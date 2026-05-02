import logging
import io

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import ADMIN_IDS
from bot.services.invite_worker import (
    create_invite_job, get_job_status, cancel_job,
    start_invite_job, is_job_running, get_current_job_id
)

logger = logging.getLogger(__name__)
router = Router()


class InviteStates(StatesGroup):
    waiting_for_file = State()


# ─── /invite_bulk — start a bulk invite job ──────────────────────────────────

@router.message(Command("invite_bulk"))
async def cmd_invite_bulk(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    if is_job_running():
        job_id = get_current_job_id()
        await message.reply(
            f"⚠️ A bulk invite job (#{job_id}) is already running.\n"
            f"Use /invite_status to check progress or /invite_stop to cancel."
        )
        return

    await state.set_state(InviteStates.waiting_for_file)
    await message.reply(
        "📤 <b>Bulk Invite</b>\n\n"
        "Send me a <b>.txt</b> or <b>.csv</b> file with user IDs (one per line).\n\n"
        "Or paste the IDs directly as a message (one per line).\n\n"
        "Send /cancel to abort.",
        parse_mode="HTML"
    )


@router.message(InviteStates.waiting_for_file, F.document)
async def handle_invite_file(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id not in ADMIN_IDS:
        return

    doc = message.document
    if not doc.file_name.endswith(('.txt', '.csv')):
        await message.reply("❌ Please send a .txt or .csv file.")
        return

    # Download file
    file = await bot.download(doc)
    content = file.read().decode('utf-8')
    user_ids = _parse_user_ids(content)

    if not user_ids:
        await message.reply("❌ No valid user IDs found in the file.")
        await state.clear()
        return

    await _start_job(message, state, bot, user_ids)


@router.message(InviteStates.waiting_for_file, F.text)
async def handle_invite_text(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id not in ADMIN_IDS:
        return

    if message.text.strip().lower() == '/cancel':
        await state.clear()
        await message.reply("❌ Bulk invite cancelled.")
        return

    user_ids = _parse_user_ids(message.text)

    if not user_ids:
        await message.reply("❌ No valid user IDs found. Send numeric IDs, one per line.")
        return

    await _start_job(message, state, bot, user_ids)


async def _start_job(message: Message, state: FSMContext, bot: Bot, user_ids: list):
    await state.clear()

    job_id = await create_invite_job(user_ids)
    start_invite_job(bot, job_id)

    await message.reply(
        f"✅ <b>Bulk invite job #{job_id} started!</b>\n\n"
        f"📊 Total IDs: {len(user_ids)}\n"
        f"⏱ Estimated time: ~{len(user_ids) * 3} minutes\n\n"
        f"Use /invite_status to check progress.\n"
        f"Use /invite_stop to cancel.",
        parse_mode="HTML"
    )


# ─── /invite_status ──────────────────────────────────────────────────────────

@router.message(Command("invite_status"))
async def cmd_invite_status(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    job_id = get_current_job_id()
    if not job_id:
        await message.reply("No active invite job. Use /invite_bulk to start one.")
        return

    status = await get_job_status(job_id)
    if not status:
        await message.reply("Job not found.")
        return

    progress = status['sent'] + status['skipped'] + status['unreachable'] + status['failed']
    total = status['total_ids']
    pct = (progress / total * 100) if total > 0 else 0

    text = (
        f"📊 <b>Invite Job #{status['id']}</b>\n\n"
        f"Status: <b>{status['status'].upper()}</b>\n"
        f"Progress: {progress}/{total} ({pct:.0f}%)\n\n"
        f"✅ Sent: {status['sent']}\n"
        f"⏭ Skipped (already member): {status['skipped']}\n"
        f"❌ Unreachable (never started bot): {status['unreachable']}\n"
        f"⚠️ Failed: {status['failed']}\n\n"
        f"Started: {status['created_at']}"
    )
    await message.reply(text, parse_mode="HTML")


# ─── /invite_stop ────────────────────────────────────────────────────────────

@router.message(Command("invite_stop"))
async def cmd_invite_stop(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    job_id = get_current_job_id()
    if not job_id:
        await message.reply("No active invite job to stop.")
        return

    await cancel_job(job_id)
    await message.reply(f"🛑 Invite job #{job_id} cancelled.")


# ─── /invite_history ─────────────────────────────────────────────────────────

@router.message(Command("invite_history"))
async def cmd_invite_history(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    from bot.database.db import get_db
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, status, total_ids, sent, skipped, unreachable, failed, created_at "
        "FROM invite_jobs ORDER BY id DESC LIMIT 10"
    )
    rows = await cursor.fetchall()
    await db.close()

    if not rows:
        await message.reply("No invite jobs found yet.")
        return

    text = "📋 <b>Invite History</b> (last 10)\n\n"
    for row in rows:
        text += (
            f"<b>Job #{row[0]}</b> — {row[1].upper()}\n"
            f"  Total: {row[2]} | ✅ {row[3]} | ⏭ {row[4]} | ❌ {row[5]} | ⚠️ {row[6]}\n"
            f"  Date: {row[7]}\n\n"
        )

    await message.reply(text, parse_mode="HTML")


# ─── Helper ──────────────────────────────────────────────────────────────────

def _parse_user_ids(text: str) -> list:
    """Parse user IDs from text (one per line, supports comma-separated too)."""
    ids = []
    for line in text.strip().splitlines():
        line = line.strip().strip(',')
        if not line:
            continue
        # Handle comma-separated on same line
        parts = line.split(',')
        for part in parts:
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))
    return list(set(ids))  # deduplicate
