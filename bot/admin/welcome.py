from telegram import Update
from telegram.ext import CallbackContext

def welcome(update: Update, context: CallbackContext) -> None:
    """
    Sends a welcome message to the user with information about the bot's features and admin commands.
    """
    message = (
        "👋 Welcome to The Dirty Launderer🧼 — your privacy-first link cleaner bot.\n\n"
        "🧼 This bot removes tracking parameters from URLs and can proxy uncleanable links via privacy frontends like "
        "Invidious, Nitter, Libreddit, and more.\n\n"
        "🔧 Admin Commands:\n"
        "/setdomain - Set handling for a specific domain\n"
        "/listdomains - View all domain rules\n"
        "/resetdomains - Reset domain settings to default\n"
        "/setdefault - Set default behavior for unknown domains\n"
        "/setlogging - Enable or disable safe logging\n"
        "/showlogging - View current logging mode\n"
        "/previewdomain - Preview handling for a domain\n"
        "/tools - Show admin tools\n"
        "/alerttest - Test an admin alert\n"
        "/ping - Check if the bot is running and webhook is healthy\n"
        "/welcome - Show this message\n\n"
        "👁️ By default, tracking links are auto-cleaned or redirected. Configure behavior per group via these commands.\n\n"
        "💃 A lady in the streets, and clean in the sheets… of tracking parameters. 🧼"
    )
    update.message.reply_text(message)