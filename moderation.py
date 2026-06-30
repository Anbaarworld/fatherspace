"""
Moderation Handler — FatherSpace
----------------------------------
Allows members to report harmful content.
Reports are filed against message IDs only — no identity revealed.
Admins review reports and can ban by DadAnon ID.
"""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.database import get_user, register_user, file_report
from config.settings import ADMIN_IDS


async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command or report reason followup."""
    telegram_id = update.effective_user.id
    user = get_user(telegram_id)
    if not user:
        user = register_user(telegram_id)

    # If user is providing a reason for a pending report
    if context.user_data.get("reporting_msg_id"):
        msg_id = context.user_data.pop("reporting_msg_id")
        reason = update.message.text
        file_report(user["dad_id"], msg_id, reason)

        # Notify admins
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"🚩 *New Report Filed*\n\n"
                        f"Message ID: #{msg_id}\n"
                        f"Reported by: {user['dad_id']}\n"
                        f"Reason: {reason}\n\n"
                        f"Use /admin to review."
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass

        await update.message.reply_text(
            "✅ Report submitted. Admins will review it shortly.\n"
            "_Thank you for keeping FatherSpace safe._",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Fresh /report command with no context
    await update.message.reply_text(
        "🚩 *Report harmful content*\n\n"
        "To report a message, tap the 🚩 Report button under it.\n\n"
        "Or type: /report followed by the message number\n"
        "Example: `/report 42`",
        parse_mode=ParseMode.MARKDOWN
    )
