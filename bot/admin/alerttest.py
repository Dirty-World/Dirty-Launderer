import os
import logging
from telegram import Update, Bot
from telegram.ext import CallbackContext

# Set up logging
# NOTE: Do not log any identifiable information about Telegram groups or users.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_alert(update, context):
    """Send a test alert to admin chat."""
    admin_chat_id = os.environ.get("ADMIN_CHAT_ID")
    if not admin_chat_id:
        update.message.reply_text("❌ ADMIN_CHAT_ID not configured.")
        return

    bot = Bot(token=os.environ.get("TELEGRAM_TOKEN"))
    try:
        bot.send_message(chat_id=admin_chat_id, text="✅ This is a test alert from The Dirty Launderer🧼.")
        logger.info("Alert sent successfully to admin chat ID.")
        update.message.reply_text("✅ Alert sent to admin chat ID.")
    except Exception as e:
        logger.error("Failed to send alert due to an error.")
        update.message.reply_text(f"❌ Failed to send alert: {e}")