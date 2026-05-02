# GhostAI Community Bot

Telegram bot for managing, moderating, and growing the GhostAI community.

---

## Quick Start (Local)

```bash
# 1. Clone and install
git clone <your-repo-url>
cd telebot
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your values (see Configuration below)

# 3. Run tests
python tests/test_all.py

# 4. Start bot
python -m bot.main
```

---

## Configuration (.env)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ | `123456:ABC...` | From @BotFather |
| `ADMIN_IDS` | ✅ | `123456789` | Your Telegram user ID (comma-separated for multiple) |
| `MAIN_GROUP_ID` | ✅ | `-1001234567890` | Your community group chat ID |
| `LOG_CHANNEL_ID` | ✅ | `-1001234567891` | Private channel for mod logs |
| `GHOSTAI_URL` | ❌ | `https://ghostai.one` | SaaS product URL |
| `GHOSTAI_PRICING_URL` | ❌ | `https://ghostai.one/pricing` | Pricing page URL |
| `MAX_WARNINGS` | ❌ | `3` | Warnings before mute |
| `BAN_AFTER_WARNINGS` | ❌ | `5` | Warnings before ban |
| `MUTE_DURATION_MINUTES` | ❌ | `60` | Mute duration |
| `PROMO_INTERVAL_HOURS` | ❌ | `6` | Scheduled promo frequency |
| `INVITE_RATE_PER_HOUR` | ❌ | `60` | Bulk invite DM rate |

**How to get IDs:**
- Your user ID → message `@userinfobot` on Telegram
- Group/channel ID → forward any message from the group to `@userinfobot`

---

## Telegram Setup (Before Running)

1. **Create bot**: Message `@BotFather` → `/newbot`
2. **Disable privacy mode**: `/setprivacy` → select bot → `Disable`
3. **Add bot to community group** as **Admin** (permissions: delete messages, ban users, invite links)
4. **Create a private log channel**, add bot as **Admin**

---

## Features

### Phase 1 — Core
- **Auto-Welcome**: Greets new members with GhostAI CTA + rules button
- **Content Moderation**: Auto-detects profanity, spam, sexual content → delete + warn/mute/ban
- **Admin Commands**: Full suite (see table below)
- **Sales Funnel**: Scheduled promos, /pricing, welcome CTA
- **Report System**: Users reply `/report` to flag messages

### Phase 2 — Growth
- **Cross-Group Tracking**: Bot passively tracks members across all groups it's in
- **Member Discovery**: `/discover` shows users in other groups but NOT in your community
- **Bulk Invite**: Upload user IDs → bot sends personalized invite DMs
- **Analytics**: `/analytics` + `/funnel` for community health + invite conversion

---

## All Commands

### Admin Only
| Command | Description |
|---------|-------------|
| `/ban` | Ban user (reply to their message) |
| `/unban` | Unban user |
| `/mute [min]` | Mute user for X minutes (default: 60) |
| `/unmute` | Unmute user |
| `/warn [reason]` | Warn user |
| `/warnings` | Check user's warning count |
| `/clearwarnings` | Reset user's warnings to 0 |
| `/stats` | Community statistics |
| `/analytics` | Full analytics (members + discovery + violations) |
| `/funnel` | Invite conversion funnel |
| `/discover` | Find users not yet in your community |
| `/groups` | List all tracked groups |
| `/invite_bulk` | Start bulk invite job (upload file or paste IDs) |
| `/invite_status` | Check running invite job progress |
| `/invite_stop` | Cancel running invite job |
| `/invite_history` | Past invite job results |
| `/setwelcome [text]` | Set welcome message (use `{name}` for user name) |
| `/setrules [text]` | Set community rules |
| `/promote` | Send a promo message now |

### Everyone
| Command | Description |
|---------|-------------|
| `/rules` | Show community rules |
| `/pricing` | Show GhostAI pricing info |
| `/report` | Report a message (reply to it) |

---

## Deployment

### Option A: Railway (Recommended — Free Tier)

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USER/ghostai-bot.git
   git push -u origin main
   ```

2. **Deploy on Railway**:
   - Go to [railway.app](https://railway.app) → Sign in with GitHub
   - Click **New Project** → **Deploy from GitHub repo** → select your repo
   - Railway auto-detects `Procfile` and runs `worker: python -m bot.main`

3. **Add environment variables**:
   - In Railway dashboard → your project → **Variables** tab
   - Add each variable from your `.env` file:
     ```
     BOT_TOKEN=your_token_here
     ADMIN_IDS=your_id_here
     MAIN_GROUP_ID=-100xxxxxxxxxx
     LOG_CHANNEL_ID=-100xxxxxxxxxx
     ```

4. **Deploy** → Railway builds and starts your bot automatically

5. **Verify**: Send `/stats` in your Telegram group — bot should respond

### Option B: Render (Free Tier)

1. Push to GitHub (same as above)
2. Go to [render.com](https://render.com) → **New** → **Background Worker**
3. Connect your GitHub repo
4. Settings:
   - **Runtime**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `python -m bot.main`
5. Add environment variables in the **Environment** tab
6. Deploy

### Option C: Docker (VPS / Oracle Cloud Free)

```bash
# Build
docker build -t ghostai-bot .

# Run
docker run -d --restart unless-stopped --name ghostai-bot --env-file .env ghostai-bot

# View logs
docker logs -f ghostai-bot

# Stop
docker stop ghostai-bot
```

### Option D: Oracle Cloud (Always Free VPS)

1. Create a free Oracle Cloud account → launch a free ARM VM (4 CPU, 24GB RAM)
2. SSH into VM:
   ```bash
   sudo apt update && sudo apt install -y python3 python3-pip git
   git clone https://github.com/YOUR_USER/ghostai-bot.git
   cd ghostai-bot
   pip3 install -r requirements.txt
   cp .env.example .env
   nano .env  # fill in your values
   ```
3. Run with systemd (auto-restart on crash):
   ```bash
   sudo tee /etc/systemd/system/ghostai-bot.service << EOF
   [Unit]
   Description=GhostAI Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=$USER
   WorkingDirectory=$(pwd)
   EnvironmentFile=$(pwd)/.env
   ExecStart=/usr/bin/python3 -m bot.main
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   EOF

   sudo systemctl enable ghostai-bot
   sudo systemctl start ghostai-bot
   sudo systemctl status ghostai-bot
   ```

---

## Project Structure

```
telebot/
├── bot/
│   ├── main.py              # Entry point
│   ├── config.py             # Environment variables
│   ├── database/
│   │   ├── db.py             # SQLite connection + schema
│   │   └── queries.py        # All CRUD operations
│   ├── handlers/
│   │   ├── welcome.py        # Auto-welcome on join
│   │   ├── moderation.py     # Content filter + actions
│   │   ├── commands.py       # Admin commands + callbacks
│   │   ├── sales.py          # Pricing, promos, CTA
│   │   ├── member_sync.py    # /discover, /groups
│   │   └── bulk_invite.py    # /invite_bulk, /invite_status
│   ├── middlewares/
│   │   ├── throttling.py     # Rate limiting
│   │   └── tracking.py       # Passive member tracking
│   ├── filters/
│   │   └── profanity.py      # Keyword/regex detection
│   ├── services/
│   │   ├── member_manager.py # Cross-group logic
│   │   └── invite_worker.py  # Background invite jobs
│   └── utils/
│       ├── keyboards.py      # Inline keyboards
│       └── helpers.py        # Formatting utilities
├── data/
│   ├── bad_words.txt         # Profanity word list
│   ├── spam_patterns.txt     # Spam regex patterns
│   └── welcome_templates.txt # Welcome message template
├── tests/
│   └── test_all.py           # 85 production tests
├── .env.example
├── .gitignore
├── Dockerfile
├── Procfile
├── requirements.txt
└── README.md
```

---

## Customization

### Add bad words
Edit `data/bad_words.txt` — one word per line, lines starting with `#` are comments.

### Add spam patterns
Edit `data/spam_patterns.txt` — one regex per line.

### Change welcome message
Use `/setwelcome Your message here, {name}!` in the group chat.

### Change rules
Use `/setrules Your rules here` in the group chat.

---

## Running Tests

```bash
python tests/test_all.py
```

Expected output: `85 passed, 0 failed — PRODUCTION READY!`
