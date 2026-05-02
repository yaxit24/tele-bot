import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
MAIN_GROUP_ID = int(os.getenv("MAIN_GROUP_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

GHOSTAI_URL = os.getenv("GHOSTAI_URL", "https://ghostai.one")
GHOSTAI_PRICING_URL = os.getenv("GHOSTAI_PRICING_URL", "https://ghostai.one/pricing")

# Moderation
MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", "3"))
MUTE_DURATION_MINUTES = int(os.getenv("MUTE_DURATION_MINUTES", "60"))
BAN_AFTER_WARNINGS = int(os.getenv("BAN_AFTER_WARNINGS", "5"))

# Sales
PROMO_INTERVAL_HOURS = int(os.getenv("PROMO_INTERVAL_HOURS", "6"))

# Invite
INVITE_RATE_PER_HOUR = int(os.getenv("INVITE_RATE_PER_HOUR", "60"))
INVITE_RETRY_AFTER_DAYS = int(os.getenv("INVITE_RETRY_AFTER_DAYS", "3"))
MAX_INVITE_ATTEMPTS = int(os.getenv("MAX_INVITE_ATTEMPTS", "2"))

# AI (Phase 3)
AI_PROVIDER = os.getenv("AI_PROVIDER", "openrouter")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "meta-llama/llama-3-8b-instruct")

# Database
DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "data/bot.db")
