from datetime import datetime, timedelta
from bot.database.db import get_db


# ─── Member Operations ───────────────────────────────────────────────────────

async def upsert_member(user_id: int, username: str = None, first_name: str = None, source_group_id: int = None):
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO members (user_id, username, first_name, source_group_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = COALESCE(excluded.username, members.username),
                first_name = COALESCE(excluded.first_name, members.first_name)
        """, (user_id, username, first_name, source_group_id))
        await db.commit()
    finally:
        await db.close()


async def get_member(user_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM members WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()
    finally:
        await db.close()


async def increment_message_count(user_id: int):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE members SET message_count = message_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
    finally:
        await db.close()


async def add_warning(user_id: int) -> int:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE members SET warning_count = warning_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
        cursor = await db.execute("SELECT warning_count FROM members WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0
    finally:
        await db.close()


async def get_warnings(user_id: int) -> int:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT warning_count FROM members WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0
    finally:
        await db.close()


async def clear_warnings(user_id: int):
    db = await get_db()
    try:
        await db.execute("UPDATE members SET warning_count = 0 WHERE user_id = ?", (user_id,))
        await db.commit()
    finally:
        await db.close()


async def set_muted(user_id: int, duration_minutes: int):
    mute_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    db = await get_db()
    try:
        await db.execute(
            "UPDATE members SET is_muted = TRUE, mute_until = ? WHERE user_id = ?",
            (mute_until.isoformat(), user_id)
        )
        await db.commit()
    finally:
        await db.close()


async def set_unmuted(user_id: int):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE members SET is_muted = FALSE, mute_until = NULL WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
    finally:
        await db.close()


async def set_banned(user_id: int, banned: bool = True):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE members SET is_banned = ? WHERE user_id = ?",
            (banned, user_id)
        )
        await db.commit()
    finally:
        await db.close()


async def set_welcomed(user_id: int):
    db = await get_db()
    try:
        await db.execute("UPDATE members SET welcomed = TRUE WHERE user_id = ?", (user_id,))
        await db.commit()
    finally:
        await db.close()


# ─── Violations ──────────────────────────────────────────────────────────────

async def log_violation(user_id: int, violation_type: str, message_text: str, action_taken: str):
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO violations (user_id, violation_type, message_text, action_taken)
            VALUES (?, ?, ?, ?)
        """, (user_id, violation_type, message_text, action_taken))
        await db.commit()
    finally:
        await db.close()


# ─── Settings ────────────────────────────────────────────────────────────────

async def get_setting(key: str, default: str = None) -> str:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else default
    finally:
        await db.close()


async def set_setting(key: str, value: str):
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
        await db.commit()
    finally:
        await db.close()


# ─── Stats ───────────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    db = await get_db()
    try:
        total = await (await db.execute("SELECT COUNT(*) FROM members")).fetchone()
        warned = await (await db.execute("SELECT COUNT(*) FROM members WHERE warning_count > 0")).fetchone()
        banned = await (await db.execute("SELECT COUNT(*) FROM members WHERE is_banned = TRUE")).fetchone()
        violations_today = await (await db.execute(
            "SELECT COUNT(*) FROM violations WHERE date(timestamp) = date('now')"
        )).fetchone()
        return {
            "total_members": total[0],
            "warned_members": warned[0],
            "banned_members": banned[0],
            "violations_today": violations_today[0],
        }
    finally:
        await db.close()
