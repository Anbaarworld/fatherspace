"""
Registration & Onboarding Handler
-----------------------------------
Handles /start command and first-time user setup.
Assigns anonymous DadAnon ID. No real data collected.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from utils.database import register_user, is_banned, init_db
from config.settings import WELCOME_MESSAGE, CHANNELS, RULES


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for every new and returning user."""
    init_db()

    telegram_id = update.effective_user.id

    if is_banned(telegram_id):
        await update.message.reply_text(
            "❌ You have been removed from FatherSpace for violating community rules."
        )
        return

    user = register_user(telegram_id)
    dad_id = user["dad_id"]
    is_new = user["message_count"] == 0 and user["joined_at"]

    greeting = (
        f"🔐 *Your anonymous ID:* `{dad_id}`\n\n"
        + WELCOME_MESSAGE
    )

    keyboard = [
        [InlineKeyboardButton("📋 View Channels", callback_data="show_channels")],
        [InlineKeyboardButton("📜 Read Rules", callback_data="show_rules")],
        [InlineKeyboardButton("🆘 Crisis Support", callback_data="show_crisis")],
    ]

    await update.message.reply_text(
        greeting,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called when someone joins a linked group (optional use)."""
    pass


async def send_channel_menu(update_or_query, context, is_callback=False):
    """Send the channel selection menu."""
    channel_buttons = []
    for ch in CHANNELS:
        channel_buttons.append([
            InlineKeyboardButton(
                f"{ch['emoji']} {ch['label']}",
                callback_data=f"select_channel:{ch['key']}"
            )
        ])
    channel_buttons.append([
        InlineKeyboardButton("❓ How does this work?", callback_data="how_it_works")
    ])

    text = "📡 *Choose a channel to post in:*\n\n" + "\n".join(
        f"{ch['emoji']} *{ch['label']}* — {ch['description']}"
        for ch in CHANNELS
    )

    markup = InlineKeyboardMarkup(channel_buttons)

    if is_callback:
        await update_or_query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup
        )
    else:
        await update_or_query.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup
        )
