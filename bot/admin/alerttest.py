import os
import logging
from telegram import Update, Bot
from telegram.ext import CallbackContext

# Set up logging
# NOTE: Do not log any identifiable information about Telegram groups or users.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def alerttest(update: Update, context: CallbackContext) -> None:
    """Send a test alert to the admin chat ID."""
    logger.info("Starting alerttest function.")
    token = os.environ.get("TELEGRAM_TOKEN")
    admin_chat_id = os.environ.get("ADMIN_CHAT_ID")

    # Validate environment variables
    if not token or not admin_chat_id:
        logger.warning("Missing TELEGRAM_TOKEN or ADMIN_CHAT_ID environment variables.")
        update.message.reply_text("❌ Missing TELEGRAM_TOKEN or ADMIN_CHAT_ID environment variables.")
        return

    bot = Bot(token=token)
    try:
        bot.send_message(chat_id=admin_chat_id, text="✅ This is a test alert from Dirty Launderer.")
        logger.info("Alert sent successfully to admin chat ID.")
        update.message.reply_text("✅ Alert sent to admin chat ID.")
    except Exception as e:
        logger.error("Failed to send alert due to an error.")
        update.message.reply_text(f"❌ Failed to send alert: {e}")