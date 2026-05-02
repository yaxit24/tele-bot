# GhostAI Bot — Admin & User Guide

---

## 🚀 Getting Started

Once the bot is deployed and running in your group, it works **automatically** for:
- Welcoming new members
- Moderating content (profanity, spam, sexual content)
- Tracking members across groups
- Sending scheduled promos every 6 hours

You only need commands for manual actions.

---

## 👑 Admin Commands

> **Who is an admin?** Anyone whose Telegram user ID is in the `ADMIN_IDS` environment variable.

---

### Moderation

| Command | How to Use | What It Does |
|---------|-----------|--------------|
| `/ban` | Reply to a user's message | Permanently bans the user from the group |
| `/unban` | Reply to a banned user's message | Unbans the user |
| `/mute` | Reply to a user's message | Mutes for 60 min (default) |
| `/mute 30` | Reply to a user's message | Mutes for 30 minutes |
| `/unmute` | Reply to a user's message | Removes mute restriction |
| `/warn Spamming` | Reply to a user's message | Warns the user with reason "Spamming" |
| `/warn` | Reply to a user's message | Warns without a specific reason |
| `/warnings` | Reply to a user's message | Shows how many warnings the user has |
| `/clearwarnings` | Reply to a user's message | Resets user's warning count to 0 |

**Auto-escalation:**
- 3 warnings → auto-mute (60 min)
- 5 warnings → auto-ban

---

### Content Settings

| Command | Example | What It Does |
|---------|---------|--------------|
| `/setwelcome` | `/setwelcome Welcome {name}! Check out GhostAI 🚀` | Sets custom welcome message. Use `{name}` for the user's first name |
| `/setrules` | `/setrules 1. No spam 2. Be respectful 3. English only` | Sets community rules |

---

### Analytics & Monitoring

| Command | What It Shows |
|---------|---------------|
| `/stats` | Quick overview: total members, warned, banned, violations today |
| `/analytics` | Full breakdown: members + discovery stats + violation counts |
| `/funnel` | Invite conversion funnel: sent → joined → skipped → failed |

---

### Member Discovery (Cross-Group Growth)

| Command | What It Does |
|---------|--------------|
| `/discover` | Shows top 20 users who are in OTHER groups the bot is in, but NOT in your main community. Best invite candidates. |
| `/groups` | Lists all groups the bot is tracking + member count per group |

**How it works:**
1. Add the bot to multiple related Telegram groups (interview prep, exam help, etc.)
2. The bot silently tracks who's active in those groups
3. `/discover` shows you who to invite — sorted by activity level

---

### Bulk Invite System

| Command | What It Does |
|---------|--------------|
| `/invite_bulk` | Starts the invite wizard. You can then: |
| | • **Upload a .txt file** with user IDs (one per line) |
| | • **Paste IDs** directly as text (comma or newline separated) |
| `/invite_status` | Shows progress of the current running invite job |
| `/invite_stop` | Cancels the running invite job immediately |
| `/invite_history` | Shows past invite jobs and their results |

**How bulk invite works:**
1. Run `/invite_bulk`
2. Bot asks for user IDs — upload file or paste them
3. Bot creates an invite link for your community
4. Bot DMs each user with a personalized invitation
5. Rate: 1 message every 36 seconds (100/hour)
6. Bot tracks: sent, skipped (already in group), unreachable (blocked bot), failed

**Where to get user IDs:**
- From `/discover` command (shows IDs of potential members)
- From Telethon scraper (Phase 4, future)
- Manually from other tools

---

### Sales & Promotion

| Command | What It Does |
|---------|--------------|
| `/promote` | Immediately sends a GhostAI promo message to the group |
| `/pricing` | Shows GhostAI pricing info (anyone can use this) |

**Auto-promos:** The bot automatically posts a promotional message every 6 hours (configurable via `PROMO_INTERVAL_HOURS`).

---

## 👤 Regular User Commands

These work for everyone in the group:

| Command | What It Does |
|---------|--------------|
| `/rules` | Shows community rules |
| `/pricing` | Shows GhostAI pricing information |
| `/report` | Reply to an offensive message → sends it to admins for review |

---

## 🤖 Automatic Features (No Commands Needed)

### Welcome Messages
- When someone joins the group, bot sends a welcome message with:
  - Personalized greeting using their name
  - Link to GhostAI
  - Button to view rules

### Content Moderation
- **Profanity** → Message deleted + warning
- **Sexual content** → Message deleted + warning
- **Spam** (crypto scams, excessive links, etc.) → Message deleted + warning
- After warnings exceed threshold → auto-mute → auto-ban

### Member Tracking
- Every message in any group the bot is in gets the sender's info logged
- This builds the database for `/discover` to find invite candidates
- **Zero impact on users** — completely silent, no extra messages

---

## 📊 Understanding Analytics Output

### `/stats` example:
```
📊 Community Statistics

👥 Total Members: 145
⚠️ Warned Members: 3
🚫 Banned Members: 1
📋 Violations Today: 7
```

### `/analytics` example:
```
📈 Full Analytics

👥 Members: 145 tracked
🔍 Discovery: 89 potential invites found
📋 Violations: 7 today, 23 this week
🎯 Invite Jobs: 2 completed, 1 running
```

### `/funnel` example:
```
🎯 Invite Funnel

📤 Total Sent: 200
✅ Joined: 45 (22.5%)
⏭️ Skipped: 30
🚫 Unreachable: 80
❌ Failed: 45
```

---

## ⚠️ Important Notes

1. **Bot must be Admin** in the group with permissions: Delete messages, Ban users, Invite via link
2. **Privacy mode must be OFF** (set via @BotFather → `/setprivacy` → Disable)
3. **Only one instance** can run at a time — stop local bot before deploying to Railway
4. **Bulk invite DMs** only work if users have interacted with the bot before (Telegram restriction). Most discovered users won't be reachable — that's normal.
5. **Rate limits**: If you get Telegram throttle errors, reduce `INVITE_RATE_PER_HOUR` to 60

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Bot doesn't respond | Check if it's running (`/stats` test). Verify bot is admin in group. |
| Welcome not sent | Ensure bot has `chat_member` updates enabled (privacy mode OFF) |
| Moderation not working | Ensure bot has "Delete messages" permission |
| Ban/mute fails | Ensure bot has "Ban users" + "Restrict members" permission |
| Invite DMs not sending | Most users haven't started the bot — this is expected |
| "Conflict" error in logs | Two bot instances running. Stop one. |
| Database locked | Restart the bot (Railway auto-restarts) |

---

## 🔄 Workflow: Growing Your Community

1. **Add bot to 3-5 related groups** (interview prep, coding, exam groups)
2. **Wait 1-2 weeks** for tracking to build up data
3. **Run `/discover`** to see potential members
4. **Run `/invite_bulk`** with those user IDs
5. **Check `/funnel`** to see conversion rates
6. **Repeat** weekly

---

## 🎛️ Configuration Quick Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_WARNINGS` | 3 | Warnings before auto-mute |
| `BAN_AFTER_WARNINGS` | 5 | Warnings before auto-ban |
| `MUTE_DURATION_MINUTES` | 60 | How long mute lasts |
| `PROMO_INTERVAL_HOURS` | 6 | Hours between auto-promos |
| `INVITE_RATE_PER_HOUR` | 100 | DMs per hour for bulk invite |
| `INVITE_RETRY_AFTER_DAYS` | 1 | Days before retrying failed invite |
| `MAX_INVITE_ATTEMPTS` | 2 | Max retries per user |
