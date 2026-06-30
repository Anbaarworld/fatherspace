"""
FatherSpace Bot - Anonymous Support Community for Fathers
=========================================================
A Telegram bot that enables fathers to share, vent, and seek advice
with complete anonymity. Neither other members nor admins can identify users.

Setup:
    pip install python-telegram-bot==20.7
    Set BOT_TOKEN in config/settings.py
    Run: python bot.py
"""

import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from config.settings import BOT_TOKEN
from handlers.registration import handle_start, handle_new_member
from handlers.messaging import handle_message, handle_callback
from handlers.admin import handle_admin_command
from handlers.moderation import handle_report

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # --- Registration & Onboarding ---
    app.add_handler(CommandHandler("start", handle_start))

    # --- Core Messaging ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))

    # --- Inline Buttons (channel select, reactions, replies) ---
    app.add_handler(CallbackQueryHandler(handle_callback))

    # --- Admin Commands ---
    app.add_handler(CommandHandler("admin", handle_admin_command))
    app.add_handler(CommandHandler("stats", handle_admin_command))
    app.add_handler(CommandHandler("ban", handle_admin_command))
    app.add_handler(CommandHandler("unban", handle_admin_command))

    # --- Moderation ---
    app.add_handler(CommandHandler("report", handle_report))

    logger.info("FatherSpace Bot is running...")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
