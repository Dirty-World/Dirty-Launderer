import logging
from telegram import Update
from telegram.ext import CallbackContext
from google.cloud import firestore

# Set up logging
# NOTE: Do not log any identifiable information about Telegram groups or users.
logger = logging.getLogger(__name__)

def configsummary(update: Update, context: CallbackContext) -> None:
    """Provide a summary of the group's configuration."""
    logger.info("Configsummary function called.")
    chat_id = str(update.effective_chat.id)
    db = firestore.Client()
    doc_ref = db.collection("group_config").document(chat_id)

    try:
        doc = doc_ref.get()
    except Exception as e:
        logger.error("Failed to retrieve group configuration due to an error.")
        update.message.reply_text("❌ Failed to retrieve group configuration. Please try again later.")
        return

    if not doc.exists:
        update.message.reply_text("⚠️ No config found for this group.")
        return

    data = doc.to_dict()
    default_behavior = data.get("default_behavior", "clean")
    domain_rules = data.get("domain_rules", {})
    if not isinstance(domain_rules, dict):
        domain_rules = {}

    lines = [f"🛠️ Current Group Config:", f"Default behavior: {default_behavior}"]
    if domain_rules:
        lines.append("\nOverrides:")
        for domain, action in domain_rules.items():
            lines.append(f"- {domain}: {action}")
    else:
        lines.append("No domain-specific overrides configured.")

    update.message.reply_text("\n".join(lines))