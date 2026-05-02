import logging
from typing import List, Dict, Optional

from bot.database.db import get_db
from bot.config import MAIN_GROUP_ID

logger = logging.getLogger(__name__)


async def register_group(group_id: int, group_name: str, is_main: bool = False):
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO groups (group_id, group_name, is_main_community)
            VALUES (?, ?, ?)
            ON CONFLICT(group_id) DO UPDATE SET group_name = excluded.group_name
        """, (group_id, group_name, is_main))
        await db.commit()
    finally:
        await db.close()


async def track_member_in_group(user_id: int, group_id: int, username: str = None, first_name: str = None):
    db = await get_db()
    try:
        # Upsert into group_members
        await db.execute("""
            INSERT OR IGNORE INTO group_members (group_id, user_id)
            VALUES (?, ?)
        """, (group_id, user_id))
        # Also upsert into members table
        await db.execute("""
            INSERT INTO members (user_id, username, first_name, source_group_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = COALESCE(excluded.username, members.username),
                first_name = COALESCE(excluded.first_name, members.first_name)
        """, (user_id, username, first_name, group_id))
        await db.commit()
    finally:
        await db.close()


async def get_members_not_in_community(limit: int = 50) -> List[Dict]:
    """Find users who are in tracked groups but NOT in the main community."""
    if not MAIN_GROUP_ID:
        return []

    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT
                gm.user_id,
                m.username,
                m.first_name,
                m.message_count,
                COUNT(DISTINCT gm.group_id) as group_count,
                GROUP_CONCAT(DISTINCT g.group_name) as group_names
            FROM group_members gm
            JOIN members m ON m.user_id = gm.user_id
            JOIN groups g ON g.group_id = gm.group_id
            WHERE gm.user_id NOT IN (
                SELECT user_id FROM group_members WHERE group_id = ?
            )
            AND g.is_main_community = FALSE
            GROUP BY gm.user_id
            ORDER BY m.message_count DESC
            LIMIT ?
        """, (MAIN_GROUP_ID, limit))
        rows = await cursor.fetchall()
    finally:
        await db.close()

    return [
        {
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "message_count": row[3],
            "group_count": row[4],
            "group_names": row[5],
        }
        for row in rows
    ]


async def get_tracked_groups() -> List[Dict]:
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT g.group_id, g.group_name, g.is_main_community,
                   COUNT(gm.user_id) as member_count
            FROM groups g
            LEFT JOIN group_members gm ON g.group_id = gm.group_id
            GROUP BY g.group_id
        """)
        rows = await cursor.fetchall()
    finally:
        await db.close()

    return [
        {
            "group_id": row[0],
            "group_name": row[1],
            "is_main": row[2],
            "member_count": row[3],
        }
        for row in rows
    ]


async def get_discovery_stats() -> Dict:
    db = await get_db()
    try:
        total_tracked = await (await db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM group_members"
        )).fetchone()

        in_community = await (await db.execute(
            "SELECT COUNT(user_id) FROM group_members WHERE group_id = ?",
            (MAIN_GROUP_ID,)
        )).fetchone()

        not_in_community = await (await db.execute("""
            SELECT COUNT(DISTINCT gm.user_id)
            FROM group_members gm
            WHERE gm.user_id NOT IN (
                SELECT user_id FROM group_members WHERE group_id = ?
            )
            AND gm.group_id != ?
        """, (MAIN_GROUP_ID, MAIN_GROUP_ID))).fetchone()

        return {
            "total_tracked": total_tracked[0],
            "in_community": in_community[0],
            "not_in_community": not_in_community[0],
        }
    finally:
        await db.close()
