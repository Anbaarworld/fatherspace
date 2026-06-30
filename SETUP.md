# FatherSpace Bot — Setup & Deployment Guide

## What You Have
A fully anonymous Telegram bot where:
- Members post as `DadAnon#XXXX` — no real name, no phone number
- Even admins cannot identify any member
- Real Telegram IDs are hashed and never stored in readable form
- Instant messaging, voice notes, photos, reactions, and replies all work

---

## Step 1: Get a Bot Token (5 minutes, free)

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Choose a name: e.g. **FatherSpace**
4. Choose a username: e.g. **fatherspace_ng_bot** (must end in `bot`)
5. BotFather gives you a token like: `7412938471:AAFxyz...`
6. Copy it — you'll need it next

---

## Step 2: Get Your Admin ID

1. Open Telegram and search for `@userinfobot`
2. Send `/start`
3. It replies with your numeric ID e.g. `123456789`
4. This is your ADMIN_ID

---

## Step 3: Configure the Bot

Open `config/settings.py` and fill in:

```python
BOT_TOKEN = "7412938471:AAFxyz..."   # Your token from BotFather
ADMIN_IDS = [123456789]              # Your numeric Telegram ID
```

Also change the secret salt (for security):
```python
# In utils/database.py, line ~15
_SALT = "your_unique_secret_phrase_here_make_it_long"
```

---

## Step 4: Install & Run Locally

```bash
# Install Python 3.10+ if not installed
python --version

# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

You should see:
```
FatherSpace Bot is running...
```

Test it by messaging your bot on Telegram.

---

## Step 5: Deploy to a Server (So It Runs 24/7)

### Option A: Railway.app (Easiest, Free tier available)
1. Go to railway.app
2. Connect your GitHub and push this folder
3. Add environment variable: `FATHERSPACE_SALT=your_secret`
4. Deploy — done

### Option B: Render.com (Free tier)
1. Push code to GitHub
2. Create a new "Web Service" on Render
3. Set start command: `python bot.py`
4. Add env vars and deploy

### Option C: VPS (DigitalOcean/Hetzner — ~$5/month)
```bash
# On your server
git clone your-repo
cd fatherspace
pip install -r requirements.txt
# Run with screen so it persists after logout
screen -S fatherspace
python bot.py
# Press Ctrl+A then D to detach
```

---

## How It Works — Anonymity Flow

```
Dad's Telegram App
       │
       │  (message sent privately to bot)
       ▼
  FatherSpace Bot
       │
       │  1. Looks up DadAnon#XXXX from hashed ID
       │  2. Checks for crisis keywords
       │  3. Strips ALL identity information
       ▼
  Broadcast Engine
       │
       │  Sends to ALL members as:
       │  "DadAnon#4521 says: [message]"
       ▼
  Every Member's Telegram
       │
       │  Sees: DadAnon#4521's message
       │  Can: Reply, React, Report
       │  Cannot: Know who DadAnon#4521 is
       ▼
  Nobody knows. Not even you (admin).
```

---

## Admin Commands

All run in your private chat with the bot:

| Command | What It Does |
|---|---|
| `/stats` | See member count, message volume, reports |
| `/admin` | Full admin panel + pending reports |
| `/ban DadAnon#XXXX` | Ban a user by their anonymous ID |
| `/unban DadAnon#XXXX` | Restore access |

---

## Channel Structure

| Channel | Purpose |
|---|---|
| 💢 Rant Room | Blow off steam |
| 👨‍👧 Parenting | Kids, school, teens |
| 💔 Relationships | Marriage, divorce, co-parenting |
| 💰 Finance | Breadwinner stress, debt |
| 🧠 Mental Health | Anxiety, depression |
| 🎉 Dad Wins | Celebrate! |

---

## Privacy Architecture (For Trust Page)

You can publish this to members:

> **What we collect:** Nothing that identifies you.
> We generate a random `DadAnon` ID when you first message the bot.
> Your Telegram ID is processed through a one-way cryptographic hash
> (SHA-256) before anything touches our database. This hash cannot be reversed.
> We store: your DadAnon ID, when you joined, how many messages you've sent,
> and the messages themselves — all linked only to your anonymous ID.
> **Not even the people running this service can find out who you are.**

---

## Growth Roadmap

| Phase | Action |
|---|---|
| **Week 1** | Test with 10 trusted fathers, fix bugs |
| **Month 1** | Invite 50–100 dads via word of mouth |
| **Month 3** | Launch social media presence (share anonymous quotes) |
| **Month 6** | Partner with therapists for weekly live Q&A sessions |
| **Year 1** | Build dedicated app, pitch to corporate HR departments |

---

## Files Overview

```
fatherspace/
├── bot.py                    # Entry point — run this
├── requirements.txt          # pip dependencies
├── config/
│   └── settings.py           # ← EDIT THIS with your token + admin ID
├── handlers/
│   ├── registration.py       # /start, onboarding, channel menu
│   ├── messaging.py          # Core: anonymous broadcast engine
│   ├── admin.py              # Admin commands
│   └── moderation.py         # Report system
└── utils/
    └── database.py           # SQLite storage (privacy-first design)
```

---

## Questions?
The code is yours. A developer can extend it with:
- Scheduled motivational messages
- Weekly polls
- Therapist integration (paid tier)
- Full mobile app (React Native) using same backend logic
