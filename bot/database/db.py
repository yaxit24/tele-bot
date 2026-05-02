import aiosqlite
from bot.config import DATABASE_PATH

DB_PATH = DATABASE_PATH


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db


async def init_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS members (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                is_banned BOOLEAN DEFAULT FALSE,
                is_muted BOOLEAN DEFAULT FALSE,
                mute_until TIMESTAMP,
                source_group_id INTEGER,
                welcomed BOOLEAN DEFAULT FALSE,
                dm_followup_sent BOOLEAN DEFAULT FALSE
            );

            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                violation_type TEXT,
                message_text TEXT,
                action_taken TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES members(user_id)
            );

            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                group_name TEXT,
                is_main_community BOOLEAN DEFAULT FALSE,
                member_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER,
                user_id INTEGER,
                PRIMARY KEY (group_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS invite_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT DEFAULT 'running',
                total_ids INTEGER DEFAULT 0,
                sent INTEGER DEFAULT 0,
                skipped INTEGER DEFAULT 0,
                unreachable INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS invite_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                user_id INTEGER,
                status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                last_attempt TIMESTAMP,
                joined_at TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES invite_jobs(id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS sales_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()
