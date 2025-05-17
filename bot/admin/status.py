import os
import logging
import requests
import time
from telegram import Update
from telegram.ext import CallbackContext
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Set up logging
# NOTE: Do not log any identifiable information about Telegram groups or users.
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Cache for webhook status
webhook_cache = {"data": None, "last_checked": 0}

def status(update: Update, context: CallbackContext) -> None:
    """Check the bot's status and webhook information."""
    logger.info("Status function called.")
    token = os.environ.get("TELEGRAM_TOKEN")

    # Validate the token
    if not token:
        logger.warning("TELEGRAM_TOKEN is not set.")
        update.message.reply_text("❌ TELEGRAM_TOKEN is not set.")
        return

    # Check cache
    current_time = time.time()
    if webhook_cache["data"] and current_time - webhook_cache["last_checked"] < 300:
        logger.info("Using cached webhook status.")
        update.message.reply_text(webhook_cache["data"])
        return

    # Retry-enabled session
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        resp = session.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
        data = resp.json()

        if data.get("ok"):
            webhook_set = "Webhook is set" if data["result"].get("url") else "No webhook set"
            message = f"✅ Bot is running.\n🌐 {webhook_set}"
            logger.info("Webhook status retrieved successfully.")
        else:
            message = "⚠️ Could not verify webhook info."
            logger.warning("Failed to verify webhook info.")

        # Update cache
        webhook_cache["data"] = message
        webhook_cache["last_checked"] = current_time
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e}")
        message = "❌ Network error. Please try again later."

    update.message.reply_text(message)
