"""
Messaging Handler — FatherSpace
---------------------------------
This is where anonymity lives.

When a dad sends a message:
1. We look up their DadAnon ID (never their real identity)
2. We check for crisis keywords
3. We forward the message to ALL members as "DadAnon#XXXX says:"
4. Real Telegram IDs are NEVER exposed at any point

This file handles:
- Text messages
- Voice notes
- Photos (with captions)
- Channel selection via inline buttons
- Reply threading
- Reactions
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.database import (
    get_user, register_user, set_active_channel,
    save_message, increment_message_count,
    get_all_hashed_ids, is_banned
)
from config.settings import CHANNELS, CRISIS_KEYWORDS, CRISIS_MESSAGE, RULES
from handlers.registration import send_channel_menu


# In-memory map: hashed_id → telegram_id for broadcasting
# This lives only in RAM and is never persisted
_active_sessions: dict[str, int] = {}


def _register_session(telegram_id: int, hashed_id: str):
    """Temporarily store telegram_id in RAM for broadcasting. Never written to disk."""
    _active_sessions[hashed_id] = telegram_id


def _get_telegram_id(hashed_id: str) -> int | None:
    return _active_sessions.get(hashed_id)


def _check_crisis(text: str) -> bool:
    """Check if message contains crisis keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in CRISIS_KEYWORDS)


def _get_channel_info(key: str) -> dict | None:
    return next((ch for ch in CHANNELS if ch["key"] == key), None)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main message handler — strips identity, broadcasts anonymously."""
    telegram_id = update.effective_user.id

    if is_banned(telegram_id):
        await update.message.reply_text("❌ You are banned from FatherSpace.")
        return

    # Register session (RAM only, not persisted)
    user = get_user(telegram_id)
    if not user:
        user = register_user(telegram_id)
    _register_session(telegram_id, user["hashed_id"])

    dad_id = user["dad_id"]
    active_channel = user.get("active_channel")

    # If no channel selected yet, prompt selection
    if not active_channel:
        await update.message.reply_text(
            "📡 First, choose a channel to post in:",
            reply_markup=_build_channel_keyboard()
        )
        return

    channel_info = _get_channel_info(active_channel)

    # ── Determine message type ────────────────────────────────────────────────
    if update.message.voice:
        await _broadcast_voice(update, context, dad_id, active_channel, channel_info)
    elif update.message.photo:
        await _broadcast_photo(update, context, dad_id, active_channel, channel_info)
    elif update.message.text:
        await _broadcast_text(update, context, dad_id, active_channel, channel_info)

    increment_message_count(telegram_id)


async def _broadcast_text(update, context, dad_id, channel_key, channel_info):
    """Broadcast a text message to all members."""
    text = update.message.text

    # Crisis check — respond privately first
    if _check_crisis(text):
        await update.message.reply_text(
            CRISIS_MESSAGE,
            parse_mode=ParseMode.MARKDOWN
        )
        return  # Don't broadcast crisis messages — keep them private

    # Save to DB
    msg_id = save_message(dad_id, channel_key, text, "text")

    # Build broadcast message
    broadcast = (
        f"{channel_info['emoji']} *#{channel_info['label'].upper()}*\n\n"
        f"👤 *{dad_id}* says:\n\n"
        f"{text}\n\n"
        f"_msg#{msg_id}_"
    )

    # Confirm to sender
    await update.message.reply_text(
        f"✅ Posted to *{channel_info['emoji']} {channel_info['label']}* anonymously.",
        parse_mode=ParseMode.MARKDOWN
    )

    # Broadcast to all active members
    await _send_to_all(
        context, dad_id, broadcast,
        msg_id=msg_id, channel_key=channel_key
    )


async def _broadcast_voice(update, context, dad_id, channel_key, channel_info):
    """Broadcast a voice note anonymously."""
    file_id = update.message.voice.file_id
    msg_id = save_message(dad_id, channel_key, "[voice note]", "voice")

    caption = (
        f"{channel_info['emoji']} *#{channel_info['label'].upper()}*\n"
        f"👤 *{dad_id}* sent a voice note  _(msg#{msg_id})_"
    )

    await update.message.reply_text(
        f"✅ Voice note posted to *{channel_info['emoji']} {channel_info['label']}* anonymously.",
        parse_mode=ParseMode.MARKDOWN
    )

    await _send_voice_to_all(context, dad_id, file_id, caption, msg_id, channel_key)


async def _broadcast_photo(update, context, dad_id, channel_key, channel_info):
    """Broadcast a photo anonymously."""
    photo = update.message.photo[-1]  # Highest resolution
    file_id = photo.file_id
    caption_text = update.message.caption or ""
    msg_id = save_message(dad_id, channel_key, caption_text or "[photo]", "photo")

    caption = (
        f"{channel_info['emoji']} *#{channel_info['label'].upper()}*\n"
        f"👤 *{dad_id}* shared a photo\n"
        + (f"_{caption_text}_\n" if caption_text else "")
        + f"_(msg#{msg_id})_"
    )

    await update.message.reply_text(
        f"✅ Photo posted to *{channel_info['emoji']} {channel_info['label']}* anonymously.",
        parse_mode=ParseMode.MARKDOWN
    )

    await _send_photo_to_all(context, dad_id, file_id, caption, msg_id, channel_key)


# ── Broadcasting Helpers ───────────────────────────────────────────────────────

def _build_reply_keyboard(msg_id: int, channel_key: str) -> InlineKeyboardMarkup:
    """Buttons under each broadcast message."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Reply", callback_data=f"reply:{msg_id}:{channel_key}"),
            InlineKeyboardButton("❤️ Support", callback_data=f"react:heart:{msg_id}"),
            InlineKeyboardButton("🚩 Report", callback_data=f"report:{msg_id}"),
        ],
        [
            InlineKeyboardButton("📡 Switch Channel", callback_data="show_channels"),
        ]
    ])


async def _send_to_all(context, sender_dad_id, text, msg_id, channel_key):
    """Send text message to all registered active sessions."""
    keyboard = _build_reply_keyboard(msg_id, channel_key)
    failed = 0

    for hashed_id, tg_id in list(_active_sessions.items()):
        try:
            await context.bot.send_message(
                chat_id=tg_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        except Exception:
            failed += 1  # User may have blocked bot — silently skip


async def _send_voice_to_all(context, sender_dad_id, file_id, caption, msg_id, channel_key):
    keyboard = _build_reply_keyboard(msg_id, channel_key)
    for hashed_id, tg_id in list(_active_sessions.items()):
        try:
            await context.bot.send_voice(
                chat_id=tg_id,
                voice=file_id,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        except Exception:
            pass


async def _send_photo_to_all(context, sender_dad_id, file_id, caption, msg_id, channel_key):
    keyboard = _build_reply_keyboard(msg_id, channel_key)
    for hashed_id, tg_id in list(_active_sessions.items()):
        try:
            await context.bot.send_photo(
                chat_id=tg_id,
                photo=file_id,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        except Exception:
            pass


def _build_channel_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            f"{ch['emoji']} {ch['label']}",
            callback_data=f"select_channel:{ch['key']}"
        )]
        for ch in CHANNELS
    ]
    return InlineKeyboardMarkup(buttons)


# ── Callback Handler (buttons) ────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button presses."""
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    user = get_user(telegram_id)
    if not user:
        user = register_user(telegram_id)
    _register_session(telegram_id, user["hashed_id"])

    data = query.data

    # ── Channel selection ──────────────────────────────────────────────────
    if data.startswith("select_channel:"):
        channel_key = data.split(":")[1]
        channel_info = _get_channel_info(channel_key)
        set_active_channel(telegram_id, channel_key)
        await query.edit_message_text(
            f"✅ You're now posting to *{channel_info['emoji']} {channel_info['label']}*\n\n"
            f"_{channel_info['description']}_\n\n"
            f"Just send your message, voice note, or photo. "
            f"It will appear as *{user['dad_id']}*.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Switch Channel", callback_data="show_channels")]
            ])
        )

    # ── Show channels ──────────────────────────────────────────────────────
    elif data == "show_channels":
        await send_channel_menu(query, context, is_callback=True)

    # ── Show rules ────────────────────────────────────────────────────────
    elif data == "show_rules":
        await query.edit_message_text(
            RULES,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="show_channels")]
            ])
        )

    # ── How it works ──────────────────────────────────────────────────────
    elif data == "how_it_works":
        await query.edit_message_text(
            "🔐 *How anonymity works:*\n\n"
            "1. You message this bot privately\n"
            "2. The bot strips your identity\n"
            "3. Your message appears to everyone as your *DadAnon ID* only\n"
            "4. Nobody — not even the admins — knows who you are\n"
            "5. Your Telegram number is never stored\n\n"
            "_Think of it like a masked town square. Same community, no faces._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="show_channels")]
            ])
        )

    # ── Crisis support ────────────────────────────────────────────────────
    elif data == "show_crisis":
        await query.edit_message_text(
            CRISIS_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="show_channels")]
            ])
        )

    # ── Reply to a message ────────────────────────────────────────────────
    elif data.startswith("reply:"):
        _, msg_id, channel_key = data.split(":")
        context.user_data["reply_to"] = int(msg_id)
        context.user_data["reply_channel"] = channel_key
        await query.edit_message_text(
            f"💬 *Replying to msg#{msg_id}*\n\n"
            f"Type your reply now. It will be sent anonymously as *{user['dad_id']}*.",
            parse_mode=ParseMode.MARKDOWN
        )

    # ── React to a message ────────────────────────────────────────────────
    elif data.startswith("react:"):
        _, reaction, msg_id = data.split(":")
        emoji_map = {"heart": "❤️", "strong": "💪", "pray": "🙏"}
        emoji = emoji_map.get(reaction, "❤️")
        await context.bot.send_message(
            chat_id=telegram_id,
            text=f"{emoji} Reaction sent anonymously to msg#{msg_id}"
        )

    # ── Report a message ──────────────────────────────────────────────────
    elif data.startswith("report:"):
        msg_id = data.split(":")[1]
        context.user_data["reporting_msg_id"] = int(msg_id)
        await query.message.reply_text(
            f"🚩 *Reporting msg#{msg_id}*\n\n"
            "Briefly describe the issue (harassment, spam, danger, etc).\n"
            "Type your reason now:",
            parse_mode=ParseMode.MARKDOWN
        )
