import json
from proxy_helper import validate_all_proxies, write_to_firestore
import os
import telegram
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_and_validate_proxies(request):
    logger.info("Starting proxy validation...")

    try:
        validated = validate_all_proxies()
        logger.info("Proxy validation completed.")
    except Exception as e:
        logger.error(f"Error during proxy validation: {e}")
        return (f"Error during proxy validation: {e}", 500)

    try:
        write_to_firestore(validated)
        logger.info("Validated proxies written to Firestore.")
    except Exception as e:
        logger.error(f"Error writing to Firestore: {e}")
        return (f"Error writing to Firestore: {e}", 500)

    all_down = all(len(lst) == 0 for lst in validated.values())
    if all_down:
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = os.environ.get("ADMIN_CHAT_ID")
        if not token or not chat_id:
            logger.error("Missing Telegram configuration for sending alerts.")
            return ("Missing Telegram configuration.", 500)

        try:
            bot = telegram.Bot(token=token)
            bot.send_message(chat_id=chat_id, text="⚠️ All proxy instances failed validation!")
            logger.warning("All proxies failed validation. Admin notified via Telegram.")
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return (f"Error sending Telegram alert: {e}", 500)

    num_valid_proxies = sum(len(lst) for lst in validated.values())
    logger.info(f"Proxy validation completed. {num_valid_proxies} proxies are functional.")
    return (f"Proxy list validated and stored in Firestore. {num_valid_proxies} proxies are functional.", 200)