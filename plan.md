# GhostAI Community Bot — Master Plan

## Overview
A Telegram bot to **manage, moderate, grow** your community and **sell GhostAI subscriptions** (AI Interview Assistant — ghostai.one).

**Stack**: Python 3.11+ | aiogram 3.x | SQLite (aiosqlite) | Free hosting (Railway/Render)
**AI-Ready**: Modular design with pluggable AI provider (OpenRouter/OpenAI) for future upgrades.

---

## Architecture

```
telebot/
├── bot/
│   ├── __init__.py
│   ├── main.py                 # Entry point, bot startup
│   ├── config.py               # Environment variables, settings
│   ├── middlewares/
│   │   ├── __init__.py
│   │   ├── throttling.py       # Anti-flood / rate limiting
│   │   └── logging.py          # Message logging middleware
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── welcome.py          # New member welcome messages
│   │   ├── moderation.py       # Content moderation (keyword + AI-ready)
│   │   ├── commands.py         # Admin commands (/ban, /warn, /mute, /stats)
│   │   ├── sales.py            # SaaS promotion & funnel handlers
│   │   ├── bulk_invite.py      # Bulk invite from user ID list
│   │   └── member_sync.py      # Cross-group member discovery
│   ├── filters/
│   │   ├── __init__.py
│   │   ├── profanity.py        # Keyword/regex bad-content filter
│   │   └── spam.py             # Spam detection filter
│   ├── services/
│   │   ├── __init__.py
│   │   ├── moderation_engine.py  # Core moderation logic (keyword now, AI later)
│   │   ├── ai_provider.py        # Pluggable AI interface (OpenRouter/OpenAI)
│   │   ├── invite_worker.py      # Background bulk invite job processor
│   │   ├── member_manager.py     # Member tracking, cross-group sync
│   │   └── sales_funnel.py       # Drip messages, CTA scheduling
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py               # DB connection, init
│   │   ├── models.py           # Table schemas
│   │   └── queries.py          # CRUD operations
│   └── utils/
│       ├── __init__.py
│       ├── keyboards.py        # Inline keyboards, buttons
│       └── helpers.py          # Formatting, time utils
├── data/
│   ├── bad_words.txt           # Profanity word list
│   ├── spam_patterns.txt       # Spam regex patterns
│   └── welcome_templates.txt   # Welcome message templates
├── tools/
│   └── member_scraper.py      # Telethon-based member extractor (Phase 4)
├── .env.example                # Environment variable template
├── requirements.txt
├── Dockerfile                  # For Railway/Render deployment
├── Procfile                    # For Railway
└── README.md
```

---

## Features — Phased Rollout

### Phase 1: Core Bot (MVP)
> **Goal**: Get bot live with welcome + moderation + basic sales CTA

#### 1.1 Auto-Welcome System
- Detect `ChatMemberUpdated` event when a new user joins
- Send a personalized welcome message with:
  - User's name (first_name)
  - Community rules summary
  - Quick intro to GhostAI (what it does, value prop)
  - CTA button → link to ghostai.one
- Configurable welcome message templates (admin can change via command)
- Optional: Delete join/leave service messages to keep chat clean

#### 1.2 Content Moderation (Keyword/Regex)
- **Profanity filter**: Match against curated bad-words list (multi-language support)
- **Sexual content filter**: Keyword patterns for explicit/sexual content
- **Spam filter**: Detect repeated messages, excessive links, forwarded spam
- **Actions on violation**:
  - Auto-delete the message
  - Warn the user (1st, 2nd, 3rd warning)
  - Auto-mute after 3 warnings (configurable)
  - Auto-ban after 5 warnings (configurable)
  - Log violation to admin/log channel with evidence (message text, user info, timestamp)
- **Admin override**: Admins/whitelisted users are exempt
- **Report system**: Users can reply to a message with `/report` to flag it to admins

#### 1.3 Admin Commands
| Command | Description |
|---------|-------------|
| `/ban @user` | Ban a user |
| `/unban @user` | Unban a user |
| `/mute @user [duration]` | Mute user for X minutes/hours |
| `/unmute @user` | Unmute a user |
| `/warn @user [reason]` | Issue a warning |
| `/warnings @user` | Check warning count |
| `/clearwarnings @user` | Reset warnings |
| `/stats` | Community stats (members, messages today, warnings) |
| `/setwelcome [text]` | Set custom welcome message |
| `/setrules [text]` | Set community rules |
| `/rules` | Display community rules |
| `/promote` | Send a GhostAI promo message |

#### 1.4 Basic Sales Funnel
- **Welcome CTA**: Every welcome message has a "Try GhostAI Free" button → ghostai.one
- **Scheduled promos**: Bot sends a promo message every X hours (configurable) with:
  - Feature highlights of GhostAI
  - Testimonials / success stories
  - Direct link to purchase → ghostai.one
- **`/pricing` command**: Shows subscription plans with links
- **DM follow-up**: When a user joins, bot sends a DM after 24h with a personalized pitch
  (if user has started a conversation with the bot)

---

### Phase 2: Growth & Intelligence
> **Goal**: Grow community + smarter moderation

#### 2.1 Cross-Group Member Harvesting & Invite Pipeline
> Bot joins your other groups as admin → passively collects every user who
> sends a message → cross-references with your community → invites missing users.

**Step 1 — Passive Member Collection (automatic)**
- Bot is added as admin to target groups (groups you're already in)
- Every message in those groups → bot silently logs user_id, username, first_name, group_id
- No scraping, no API abuse — just listening to normal chat activity
- Over days/weeks, builds a comprehensive member database

**Step 2 — Cross-Reference Engine**
- Compares collected members vs your main community members
- Flags users who are in Group A/B/C but NOT in your community
- Admin command `/discover` shows list with stats:
  - Username, which group(s) they're active in, message count, last seen
  - Sorted by activity level (most active first = highest-value targets)

**Step 3 — Invite Pipeline**
- DM invite (preferred): For users who have started a chat with the bot
- In-group CTA: Bot posts periodic "Join our community" messages in source groups
- Smart timing: Sends invites during peak activity hours
- Rate limiting: Max 20 DMs/hour to avoid Telegram spam flags
- Drip sequence: If user ignores first invite, retry after 3 days with different angle

**Step 4 — Tracking & Analytics**
- Track invite link clicks per source group
- Track conversion rate: invited → joined → active member
- `/funnel` command shows the full pipeline stats

#### 2.2 Bulk Invite from User ID List
> You provide a list of user IDs → bot sends each one a personalized invite via DM

**How it works:**
- Admin sends `/invite_bulk` command
- Bot asks to upload a .txt or .csv file with user IDs (one per line)
- Bot processes the list and categorizes each user:
  - ✅ Reachable — user has started the bot before → invite DM sent
  - ⚠️ Already member — user is already in community → skipped
  - ❌ Unreachable — user never started the bot → flagged (cannot DM)
- Sends invites in background at 20/hour to avoid Telegram spam detection
- Each invite includes:
  - Personalized message with user's name
  - GhostAI value proposition
  - One-click invite link to join community

**Admin commands:**
| Command | Description |
|---------|-------------|
| `/invite_bulk` | Start a new bulk invite job (upload file) |
| `/invite_status` | Check progress of current job |
| `/invite_stop` | Cancel running bulk invite job |
| `/invite_history` | See past bulk invite jobs and results |

**Retry & Follow-up:**
- If user doesn't join within 3 days → send one follow-up DM (different angle)
- Max 2 attempts per user, then mark as "declined"
- All attempts logged in DB for analytics

**⚠️ Telegram Constraints (applies to 2.1 and 2.2)**
- Bot CANNOT add users to groups directly — only invite links
- Bot CANNOT DM users who haven't started a chat with it first
- Bot CANNOT fetch full member list via Bot API — only sees active chatters
- All invites respect Telegram rate limits and ToS

#### 2.3 Member Analytics & CRM
- Track per-user: join date, message count, warnings, activity level, referral source
- `/analytics` command: daily active users, growth rate, top contributors, churn

#### 2.4 Engagement Features
- Auto-reply to FAQs: Keyword-triggered auto-replies
- Polls & quizzes: `/poll [question]`
- Leaderboard: `/top` — most active members this week
- Referral tracking: Unique invite link per user

---

### Phase 3: AI-Powered Upgrade
> **Goal**: Plug in AI for smart moderation + sales

#### 3.1 AI Content Moderation (OpenRouter)
- Replace/augment keyword filter with AI classification
- Pluggable ai_provider.py — just add OpenRouter API key in .env

#### 3.2 AI Sales Assistant
- Bot answers GhostAI product questions using AI
- Handles objections, personalized recommendations

#### 3.3 Smart Engagement
- AI-generated personalized welcome messages
- Auto-summarize daily chat activity for admins
- Community sentiment trends

---

### Phase 4: Member Scraper Tool (Telethon)
> **Goal**: Extract member IDs from large groups you don't own

#### 4.1 Telethon-Based Member Extractor
> A standalone utility script — NOT part of the main bot. Run manually when needed.

**What it does:**
- Uses YOUR personal Telegram account (via Telethon client API)
- You provide a group username or invite link
- Script fetches all visible members (user_id, username, first_name)
- Exports to `data/scraped_members.csv`
- That CSV is then fed to the bot's `/invite_bulk` command

**How to use:**
```bash
python tools/member_scraper.py --group @target_group_username --output data/scraped_members.csv
```

**Features:**
- One-time phone/OTP login (session saved for reuse)
- Smart rate limiting: 200 members per batch, 10-15s random delay between batches
- Progress bar showing extraction progress
- Handles groups up to ~10k visible members
- Saves partial results if interrupted (resume support)
- Deduplication: skips IDs already in your DB

**Safety measures:**
- Random delays (5-15s) between API calls to mimic human behavior
- Max 10k members per session to avoid aggressive flagging
- Use a SECONDARY Telegram account (not your main)
- Run at most once per day per group

**⚠️ Risks & Disclaimers:**
- Violates Telegram ToS — account could get restricted/banned
- Only works if the group's member list is visible (some groups hide it)
- NEVER use your primary account — always use a burner
- This tool is for educational/personal use; use at your own risk

**Flow:**
```
[You join target group] → run scraper → members.csv → /invite_bulk → DM invites → Your Community
```

---

## Database Schema (SQLite)

```sql
CREATE TABLE members (
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

CREATE TABLE violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    violation_type TEXT,
    message_text TEXT,
    action_taken TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES members(user_id)
);

CREATE TABLE groups (
    group_id INTEGER PRIMARY KEY,
    group_name TEXT,
    is_main_community BOOLEAN DEFAULT FALSE,
    member_count INTEGER DEFAULT 0
);

CREATE TABLE group_members (
    group_id INTEGER,
    user_id INTEGER,
    PRIMARY KEY (group_id, user_id)
);

CREATE TABLE invite_jobs (
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

CREATE TABLE invite_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    user_id INTEGER,
    status TEXT DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    joined_at TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES invite_jobs(id)
);

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE sales_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Environment Variables

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
MAIN_GROUP_ID=-1001234567890
LOG_CHANNEL_ID=-1001234567891
GHOSTAI_URL=https://ghostai.one
GHOSTAI_PRICING_URL=https://ghostai.one/pricing

# Phase 3 (AI) — leave empty for now
AI_PROVIDER=openrouter
AI_API_KEY=
AI_MODEL=meta-llama/llama-3-8b-instruct

# Moderation
MAX_WARNINGS=3
MUTE_DURATION_MINUTES=60
BAN_AFTER_WARNINGS=5
PROMO_INTERVAL_HOURS=6

# Invite settings
INVITE_RATE_PER_HOUR=20
INVITE_RETRY_AFTER_DAYS=3
MAX_INVITE_ATTEMPTS=2

# Telethon scraper (Phase 4) — use secondary account!
TELETHON_API_ID=
TELETHON_API_HASH=
TELETHON_PHONE=

# Database
DATABASE_PATH=data/bot.db
```

---

## Hosting (Free Tier)

| Provider | Free Tier | Best For |
|----------|-----------|----------|
| **Railway** | $5 free credit/month | Best DX, easy deploy |
| **Render** | 750 hrs/month free | Reliable, auto-deploy |
| **Oracle Cloud** | Always-free ARM VM | Best for 24/7 uptime |

---

## Implementation Order

```
Week 1: Project setup + Welcome + Moderation        ← BUILD FIRST
Week 2: Admin commands + Sales + Logging
Week 3: Cross-group harvesting + Bulk invite + Analytics
Week 4: AI prep + Docker + Deploy + Testing
Week 5: Telethon member scraper tool                  ← BUILD LAST
```

---

## Key Telegram API Considerations

1. Bot must be admin in the community group
2. Disable privacy mode via @BotFather so bot sees all messages
3. Bot can only DM users who started a chat first
4. Rate limits: ~30 messages/second max
5. Bots CANNOT add users to groups — only invite links

---

## Next Steps

Approve this plan → I start building Phase 1 (MVP) immediately.
**Say "go" to start coding.**
