"""
Comprehensive production-readiness test suite for GhostAI Telegram Bot.
Tests all modules offline (no Telegram API calls).
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0

def test(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


# ═══════════════════════════════════════════════════════════════════════════════
print("\n🔧 1. CONFIG")
# ═══════════════════════════════════════════════════════════════════════════════
from bot.config import (
    BOT_TOKEN, ADMIN_IDS, MAIN_GROUP_ID, LOG_CHANNEL_ID,
    GHOSTAI_URL, GHOSTAI_PRICING_URL, MAX_WARNINGS, MUTE_DURATION_MINUTES,
    BAN_AFTER_WARNINGS, PROMO_INTERVAL_HOURS, INVITE_RATE_PER_HOUR,
    DATABASE_PATH
)

test("BOT_TOKEN is set", bool(BOT_TOKEN))
test("ADMIN_IDS is a list", isinstance(ADMIN_IDS, list))
test("MAIN_GROUP_ID is int", isinstance(MAIN_GROUP_ID, int))
test("LOG_CHANNEL_ID is int", isinstance(LOG_CHANNEL_ID, int))
test("GHOSTAI_URL is valid", GHOSTAI_URL.startswith("http"))
test("GHOSTAI_PRICING_URL is valid", GHOSTAI_PRICING_URL.startswith("http"))
test("MAX_WARNINGS > 0", MAX_WARNINGS > 0)
test("BAN_AFTER_WARNINGS > MAX_WARNINGS", BAN_AFTER_WARNINGS > MAX_WARNINGS)
test("MUTE_DURATION_MINUTES > 0", MUTE_DURATION_MINUTES > 0)
test("PROMO_INTERVAL_HOURS > 0", PROMO_INTERVAL_HOURS > 0)
test("INVITE_RATE_PER_HOUR > 0", INVITE_RATE_PER_HOUR > 0)
test("DATABASE_PATH ends with bot.db", str(DATABASE_PATH).endswith("bot.db"))


# ═══════════════════════════════════════════════════════════════════════════════
print("\n🔧 2. DATABASE")
# ═══════════════════════════════════════════════════════════════════════════════
from bot.database.db import init_db, get_db

async def test_database():
    # Clean slate
    import pathlib
    db_path = DATABASE_PATH
    if db_path.exists():
        db_path.unlink()
    for suffix in ["-wal", "-shm"]:
        p = pathlib.Path(str(db_path) + suffix)
        if p.exists():
            p.unlink()

    await init_db()
    test("init_db creates database file", db_path.exists())

    db = await get_db()
    test("get_db returns connection", db is not None)

    # Verify all tables exist
    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in await cursor.fetchall()]
    await db.close()

    expected = ["group_members", "groups", "invite_jobs", "invite_targets", "members", "sales_log", "settings", "violations"]
    for t in expected:
        test(f"Table '{t}' exists", t in tables)

asyncio.run(test_database())


# ═══════════════════════════════════════════════════════════════════════════════
print("\n🔧 3. QUERIES (CRUD)")
# ═══════════════════════════════════════════════════════════════════════════════
from bot.database.queries import (
    upsert_member, get_member, increment_message_count,
    add_warning, get_warnings, clear_warnings,
    set_muted, set_unmuted, set_banned, set_welcomed,
    log_violation, get_setting, set_setting, get_stats
)

async def test_queries():
    # Upsert member
    await upsert_member(111, "testuser", "TestFirst")
    member = await get_member(111)
    test("upsert_member creates record", member is not None)
    test("member user_id correct", member[0] == 111 if member else False)

    # Increment message count
    await increment_message_count(111)
    await increment_message_count(111)
    member = await get_member(111)
    test("increment_message_count works", member[4] == 2 if member else False)

    # Warnings
    count = await add_warning(111)
    test("add_warning returns count 1", count == 1)
    count = await add_warning(111)
    test("add_warning returns count 2", count == 2)
    count = await get_warnings(111)
    test("get_warnings returns 2", count == 2)
    await clear_warnings(111)
    count = await get_warnings(111)
    test("clear_warnings resets to 0", count == 0)

    # Mute/unmute
    await set_muted(111, 60)
    member = await get_member(111)
    test("set_muted sets is_muted", member[7] == 1 if member else False)
    await set_unmuted(111)
    member = await get_member(111)
    test("set_unmuted clears is_muted", member[7] == 0 if member else False)

    # Ban
    await set_banned(111, True)
    member = await get_member(111)
    test("set_banned sets is_banned", member[6] == 1 if member else False)
    await set_banned(111, False)
    member = await get_member(111)
    test("set_banned(False) clears ban", member[6] == 0 if member else False)

    # Welcomed
    await set_welcomed(111)
    member = await get_member(111)
    test("set_welcomed sets flag", member[10] == 1 if member else False)

    # Violations
    await log_violation(111, "profanity", "bad word here", "warned")
    # No crash = pass
    test("log_violation succeeds", True)

    # Settings
    await set_setting("test_key", "test_value")
    val = await get_setting("test_key")
    test("set/get_setting works", val == "test_value")
    val = await get_setting("nonexistent", "default")
    test("get_setting returns default for missing", val == "default")

    # Stats
    stats = await get_stats()
    test("get_stats returns dict", isinstance(stats, dict))
    test("get_stats has total_members", "total_members" in stats)
    test("get_stats total_members >= 1", stats["total_members"] >= 1)
    test("get_stats violations_today >= 1", stats["violations_today"] >= 1)

asyncio.run(test_queries())


# ═══════════════════════════════════════════════════════════════════════════════
print("\n🔧 4. PROFANITY FILTER")
# ═══════════════════════════════════════════════════════════════════════════════
from bot.filters.profanity import load_filters, detect_violation, check_profanity, check_spam, check_sexual_content

load_filters()

# Clean messages (should NOT trigger)
clean_messages = [
    "Hello everyone!",
    "How is the interview prep going?",
    "I passed my exam today!",
    "GhostAI is really helpful",
    "Can someone help me with Python?",
    "a",          # Single letter - should NOT match
    "as",         # Short word - should NOT match
    "I see",      # Common phrase
    "this is great stuff",
    "assignment due tomorrow",
]
for msg in clean_messages:
    test(f"Clean: '{msg[:40]}'", detect_violation(msg) is None)

# Bad messages (SHOULD trigger)
bad_messages = [
    ("you are a fucking idiot", "profanity"),
    ("shit happens", "profanity"),
    ("check my onlyfans", "sexual_content"),
    ("send nudes please", "sexual_content"),
    ("porn link here xxx", "sexual_content"),
    ("earn $500 daily join t.me/scam", "spam"),
    ("free crypto giveaway!", "spam"),
]
for msg, expected_type in bad_messages:
    result = detect_violation(msg)
    test(f"Bad ({expected_type}): '{msg[:40]}'", result == expected_type)


# ═══════════════════════════════════════════════════════════════════════════════
print("\n🔧 5. MEMBER MANAGER")
# ═══════════════════════════════════════════════════════════════════════════════
from bot.services.member_manager import (
    register_group, track_member_in_group,
    get_tracked_groups, get_discovery_stats
)

async def test_member_manager():
    await register_group(-100111, "Test Group A", is_main=False)
    await register_group(-100222, "Test Group B", is_main=False)

    groups = await get_tracked_groups()
    test("register_group creates groups", len(groups) >= 2)

    await track_member_in_group(222, -100111, "user2", "User Two")
    await track_member_in_group(333, -100222, "user3", "User Three")

    stats = await get_discovery_stats()
    test("get_discovery_stats returns dict", isinstance(stats, dict))
    test("total_tracked >= 2", stats["total_tracked"] >= 2)

asyncio.run(test_member_manager())


# ═══════════════════════════════════════════════════════════════════════════════
print("\n🔧 6. INVITE WORKER")
# ═══════════════════════════════════════════════════════════════════════════════
from bot.services.invite_worker import (
    create_invite_job, get_job_status, is_job_running, get_current_job_id
)

async def test_invite_worker():
    job_id = await create_invite_job([1001, 1002, 1003])
    test("create_invite_job returns id", job_id is not None and job_id > 0)

    status = await get_job_status(job_id)
    test("get_job_status returns dict", status is not None)
    test("job status is 'running'", status["status"] == "running")
    test("job total_ids is 3", status["total_ids"] == 3)

    test("is_job_running is False (not started)", not is_job_running())
    test("get_current_job_id is None", get_current_job_id() is None)

asyncio.run(test_invite_worker())


# ═══════════════════════════════════════════════════════════════════════════════
print("\n🔧 7. KEYBOARDS")
# ═══════════════════════════════════════════════════════════════════════════════
from bot.utils.keyboards import welcome_keyboard, pricing_keyboard, promo_keyboard, report_confirm_keyboard

kb = welcome_keyboard()
test("welcome_keyboard has buttons", len(kb.inline_keyboard) > 0)
test("welcome_keyboard has GhostAI button", "GhostAI" in kb.inline_keyboard[0][0].text)

kb = pricing_keyboard()
test("pricing_keyboard has buttons", len(kb.inline_keyboard) > 0)

kb = promo_keyboard()
test("promo_keyboard has buttons", len(kb.inline_keyboard) > 0)

kb = report_confirm_keyboard(123, 456)
test("report_confirm_keyboard has action buttons", len(kb.inline_keyboard) >= 2)


# ═══════════════════════════════════════════════════════════════════════════════
print("\n🔧 8. HELPERS")
# ═══════════════════════════════════════════════════════════════════════════════
from bot.utils.helpers import format_duration

test("format_duration 30 min", format_duration(30) == "30 minutes")
test("format_duration 1 min", format_duration(1) == "1 minute")
test("format_duration 60 min", format_duration(60) == "1 hour")
test("format_duration 90 min", format_duration(90) == "1 hour 30 min")


# ═══════════════════════════════════════════════════════════════════════════════
print("\n🔧 9. IMPORTS (all handlers)")
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from bot.handlers import welcome, moderation, commands, sales, member_sync, bulk_invite
    test("All handler modules import", True)
except Exception as e:
    test(f"All handler modules import ({e})", False)

try:
    from bot.middlewares.throttling import ThrottlingMiddleware
    from bot.middlewares.tracking import MemberTrackingMiddleware
    test("All middleware modules import", True)
except Exception as e:
    test(f"All middleware modules import ({e})", False)

try:
    from bot.main import main
    test("bot.main imports", True)
except Exception as e:
    test(f"bot.main imports ({e})", False)


# ═══════════════════════════════════════════════════════════════════════════════
print("\n🔧 10. HANDLER ROUTERS")
# ═══════════════════════════════════════════════════════════════════════════════
from bot.handlers import welcome, moderation, commands, sales, member_sync, bulk_invite

test("welcome.router has handlers", len(welcome.router.chat_member.handlers) > 0)
test("moderation.router has handlers", len(moderation.router.message.handlers) > 0)
test("commands.router has handlers", len(commands.router.message.handlers) > 0)
test("sales.router has handlers", len(sales.router.message.handlers) > 0)
test("member_sync.router has handlers", len(member_sync.router.message.handlers) > 0)
test("bulk_invite.router has handlers", len(bulk_invite.router.message.handlers) > 0)


# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"  RESULTS: {PASS} passed, {FAIL} failed, {PASS+FAIL} total")
if FAIL == 0:
    print("  🎉 ALL TESTS PASSED — PRODUCTION READY!")
else:
    print(f"  ⚠️  {FAIL} TESTS FAILED — FIX BEFORE DEPLOYING")
print(f"{'='*60}\n")
