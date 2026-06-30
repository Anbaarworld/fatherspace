"""
Admin Handler — FatherSpace
-----------------------------
Commands only accessible to admin Telegram IDs defined in settings.py
Admins can see STATS and manage BANS — but never see real identities.
Even banned users are identified only by their DadAnon ID.
"""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config.settings import ADMIN_IDS
from utils.database import (
    get_stats, ban_user_by_dad_id, unban_user_by_dad_id,
    get_pending_reports, get_user
)


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route admin commands."""
    telegram_id = update.effective_user.id

    if not _is_admin(telegram_id):
        await update.message.reply_text("❌ Not authorised.")
        return

    command = update.message.text.split()[0].lstrip("/")

    if command == "stats":
        await _send_stats(update, context)
    elif command == "admin":
        await _send_admin_menu(update, context)
    elif command == "ban":
        await _ban_user(update, context)
    elif command == "unban":
        await _unban_user(update, context)


async def _send_stats(update, context):
    stats = get_stats()
    channel_lines = "\n".join(
        f"  {r['channel']}: {r['count']} messages"
        for r in stats["channels"]
    ) or "  No messages yet"

    await update.message.reply_text(
        f"📊 *FatherSpace Stats*\n\n"
        f"👨 Active dads: {stats['total_users']}\n"
        f"💬 Total messages: {stats['total_messages']}\n"
        f"🚩 Pending reports: {stats['pending_reports']}\n"
        f"🚫 Banned users: {stats['bans']}\n\n"
        f"*Messages by channel:*\n{channel_lines}",
        parse_mode=ParseMode.MARKDOWN
    )


async def _send_admin_menu(update, context):
    reports = get_pending_reports()
    report_text = ""
    if reports:
        report_text = "\n\n🚩 *Pending Reports:*\n" + "\n".join(
            f"  msg#{r['message_id']} — {r['reason'] or 'No reason given'} "
            f"(by {r['reporter_dad_id']})"
            for r in reports[:5]
        )

    await update.message.reply_text(
        "🛠️ *Admin Panel*\n\n"
        "Commands:\n"
        "/stats — View community stats\n"
        "/ban DadAnon#XXXX — Ban a user by their anonymous ID\n"
        "/unban DadAnon#XXXX — Unban a user\n"
        + report_text + "\n\n"
        "_Note: You cannot see any member's real identity._",
        parse_mode=ParseMode.MARKDOWN
    )


async def _ban_user(update, context):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /ban DadAnon#XXXX")
        return
    dad_id = args[0]
    ban_user_by_dad_id(dad_id)
    await update.message.reply_text(f"🚫 {dad_id} has been banned.")


async def _unban_user(update, context):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /unban DadAnon#XXXX")
        return
    dad_id = args[0]
    unban_user_by_dad_id(dad_id)
    await update.message.reply_text(f"✅ {dad_id} has been unbanned.")
