import logging
from telegram import Update
from telegram.ext import CallbackContext
from google.cloud import firestore

# Set up logging
# NOTE: Do not log any identifiable information about Telegram groups or users.
logger = logging.getLogger(__name__)

def proxies(update: Update, context: CallbackContext) -> None:
    """Provide a summary of active proxy frontends."""
    logger.info("Proxies function called.")
    db = firestore.Client()
    doc_ref = db.collection("validated_proxies").document("active")

    try:
        doc = doc_ref.get()
    except Exception as e:
        logger.error("Failed to retrieve proxy data due to an error.")
        update.message.reply_text("❌ Failed to retrieve proxy data. Please try again later.")
        return

    if not doc.exists:
        update.message.reply_text("❌ No validated proxies available.")
        return

    proxies = doc.to_dict()
    if not isinstance(proxies, dict):
        logger.warning("Invalid proxy data format retrieved.")
        update.message.reply_text("❌ Invalid proxy data format.")
        return

    lines = ["🛡️ Active Proxy Frontends:"]
    for service, urls in proxies.items():
        lines.append(f"- {service.capitalize()}: {len(urls)}")

    update.message.reply_text("\n".join(lines))