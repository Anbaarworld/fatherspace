"""
Configuration for FatherSpace Bot
----------------------------------
Fill in your values before running.
Get a BOT_TOKEN from @BotFather on Telegram.
ADMIN_IDS are Telegram user IDs of people who can run admin commands.
"""

# ── Core ────────────────────────────────────────────────────────────────────
BOT_TOKEN = "8928008904:AAEhm4q7mviK-mHMYYwlM6iIlYY4XtKBc7U"          # From @BotFather
ADMIN_IDS = [1849999279]                    # Your Telegram numeric user ID(s)

# ── Data Storage ─────────────────────────────────────────────────────────────
# SQLite DB path — change to full path in production
DB_PATH = "data/fatherspace.db"

# ── Community Channels ───────────────────────────────────────────────────────
# Each channel has: key, emoji, label, description
CHANNELS = [
    {
        "key": "rants",
        "emoji": "💢",
        "label": "Rant Room",
        "description": "Blow off steam. No advice needed. Just speak."
    },
    {
        "key": "parenting",
        "emoji": "👨‍👧",
        "label": "Parenting",
        "description": "Kids, school, discipline, teenage years."
    },
    {
        "key": "relationships",
        "emoji": "💔",
        "label": "Relationships",
        "description": "Marriage, divorce, co-parenting, loneliness."
    },
    {
        "key": "finance",
        "emoji": "💰",
        "label": "Finance",
        "description": "Breadwinner pressure, debt, job stress."
    },
    {
        "key": "mental_health",
        "emoji": "🧠",
        "label": "Mental Health",
        "description": "Anxiety, depression, feeling lost or invisible."
    },
    {
        "key": "wins",
        "emoji": "🎉",
        "label": "Dad Wins",
        "description": "Celebrate fatherhood. Share the good stuff."
    },
]

# ── Community Rules ───────────────────────────────────────────────────────────
RULES = """
📜 *FatherSpace Community Rules*

1. 🤐 *No identity fishing* — Never ask who someone is in real life
2. 📵 *No screenshots* — What's shared here stays here
3. 🤝 *Respect all dads* — Different backgrounds, same struggles
4. 🚫 *No abuse* — No insults, hate speech, or harassment
5. 🆘 *Crisis first* — If someone sounds dangerous, report it. We have support.
6. 🎭 *Stay anonymous* — Don't share your real name, location, or workplace

Break these rules and you're out. Permanently.
"""

# ── Onboarding Message ────────────────────────────────────────────────────────
WELCOME_MESSAGE = """
👋 *Welcome to FatherSpace.*

This is a safe, anonymous space for fathers.

✅ Nobody knows who you are — not even the admins
✅ You've been assigned a random Father ID
✅ Speak freely. Rant. Ask. Celebrate. Cry if you need to.

Use /menu to choose where to post.
Use /rules to read community guidelines.
Use /report to flag harmful content.

_You are not alone._
"""

# ── Crisis Response ────────────────────────────────────────────────────────────
CRISIS_KEYWORDS = [
    "kill myself", "end it all", "suicide", "can't go on",
    "want to die", "no reason to live", "end my life"
]

CRISIS_MESSAGE = """
🆘 *Hey. I see you.*

What you just shared sounds really heavy. You don't have to carry this alone.

Please reach out right now:
• 🇳🇬 Nigeria: Mentally Aware Nigeria Initiative — 0800 800 2000
• 💬 Talk to someone in this community — type /support
• 🌍 International: findahelpline.com

You matter. Your kids need you. Please hold on. 🙏
"""
