import os
import json
import logging
from telegram import Update, Bot, ParseMode
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import hashlib
from urllib.parse import urlparse
import gc
import time
from collections import defaultdict
import re
import html

# Configure logging with minimal metadata
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'  # Removed timestamp and logger name
)
logger = logging.getLogger(__name__)

# Get token from environment variable
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', 'test_token')
if not TELEGRAM_TOKEN:
    logger.error("Missing TELEGRAM_TOKEN environment variable")
    raise EnvironmentError("Missing TELEGRAM_TOKEN environment variable")

# Rate limiting
RATE_LIMIT = 10  # requests per minute
rate_limit_store = defaultdict(list)

# User consent store
user_consent = set()

def sanitize_input(text):
    """Sanitize user input for logging."""
    if not text:
        return ''
    # Remove any PII patterns (emails, IPs, etc.)
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', text)
    text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]', text)
    text = re.sub(r'(password|token|key|secret)=[\S]+', r'\1=[REDACTED]', text)
    return html.escape(text)

def hash_user_id(user_id):
    """Hash user ID to avoid logging PII."""
    if not user_id:
        return 'unknown'
    # Add salt from environment variable or use default
    salt = os.environ.get('HASH_SALT', 'default-salt')
    return hashlib.sha256(f"{salt}{user_id}".encode()).hexdigest()[:8]

def get_safe_domain(url):
    """Extract and normalize domain for logging."""
    try:
        if not url:
            return 'invalid-url'
        parsed = urlparse(url)
        # Get base domain without subdomains
        domain_parts = parsed.netloc.split('.')
        if len(domain_parts) > 2:
            return '.'.join(domain_parts[-2:])
        return parsed.netloc
    except:
        return 'invalid-url'

def cleanup_session():
    """Ensure no user data persists between requests."""
    gc.collect()
    # Clear rate limiting data older than 1 minute
    current_time = time.time()
    for user_hash in list(rate_limit_store.keys()):
        rate_limit_store[user_hash] = [t for t in rate_limit_store[user_hash] if current_time - t < 60]
        if not rate_limit_store[user_hash]:
            del rate_limit_store[user_hash]

def check_rate_limit(user_hash):
    """Check if user has exceeded rate limit."""
    current_time = time.time()
    user_requests = rate_limit_store[user_hash]
    user_requests = [t for t in user_requests if current_time - t < 60]
    rate_limit_store[user_hash] = user_requests
    
    if len(user_requests) >= RATE_LIMIT:
        logger.warning(f"Rate limit exceeded for user {user_hash}")
        return False
    
    user_requests.append(current_time)
    return True

def delete_message_after_delay(context, chat_id, message_id):
    """Delete message after 5 minutes for privacy."""
    try:
        time.sleep(300)  # 5 minutes
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.error(f"Error deleting message: {type(e).__name__}")

def privacy_command(update, context):
    """Send privacy policy information."""
    try:
        user_hash = hash_user_id(update.effective_user.id if update.effective_user else None)
        if not check_rate_limit(user_hash):
            return

        privacy_text = (
            "🔒 *The Dirty Launderer🧼 Privacy Policy*\n\n"
            "• We do not store any personal data\n"
            "• Messages are processed in memory only\n"
            "• URLs are cleaned of tracking parameters\n"
            "• Logs are anonymized and minimal\n"
            "• Messages are auto-deleted after 5 minutes\n"
            "• You can use /delete to remove messages immediately\n"
            "• Rate limiting is in place to prevent abuse\n\n"
            "By using this bot, you consent to this privacy policy."
        )
        
        msg = update.message.reply_text(privacy_text, parse_mode=ParseMode.MARKDOWN)
        context.job_queue.run_once(
            lambda _: delete_message_after_delay(context, update.message.chat_id, msg.message_id),
            300
        )
    finally:
        cleanup_session()

def delete_command(update, context):
    """Delete user's messages for privacy."""
    try:
        user_hash = hash_user_id(update.effective_user.id if update.effective_user else None)
        if not check_rate_limit(user_hash):
            return

        if update.message.reply_to_message:
            try:
                update.message.reply_to_message.delete()
            except Exception:
                pass
        update.message.delete()
    finally:
        cleanup_session()

def start(update, context):
    """Send a message when the command /start is issued."""
    try:
        user_hash = hash_user_id(update.effective_user.id if update.effective_user else None)
        if not check_rate_limit(user_hash):
            return

        logger.info(f"Command: start, User: {user_hash}")
        msg = update.message.reply_text(
            'Hi! I am The Dirty Launderer🧼 bot. Send me a URL and I will clean it for you.\n'
            'Use /help to see available commands.'
        )
        context.job_queue.run_once(
            lambda _: delete_message_after_delay(context, update.message.chat_id, msg.message_id),
            300
        )
    finally:
        cleanup_session()

def help_command(update, context):
    """Send a message when the command /help is issued."""
    try:
        user_hash = hash_user_id(update.effective_user.id if update.effective_user else None)
        if not check_rate_limit(user_hash):
            return

        logger.info(f"Command: help, User: {user_hash}")
        msg = update.message.reply_text(
            'The Dirty Launderer🧼 is here to help!\n\n'
            'Send me any URL and I will remove tracking parameters and proxy it through privacy-friendly frontends.\n\n'
            'Commands:\n'
            '/privacy - View privacy policy\n'
            '/delete - Delete messages\n'
            '/help - Show this help\n\n'
            'Made with 🧼 by The Dirty Launderer🧼 team'
        )
        context.job_queue.run_once(
            lambda _: delete_message_after_delay(context, update.message.chat_id, msg.message_id),
            300
        )
    finally:
        cleanup_session()

def handle_message(update, context):
    """Handle incoming messages."""
    try:
        if update.message and update.message.text:
            user_hash = hash_user_id(update.effective_user.id if update.effective_user else None)
            if not check_rate_limit(user_hash):
                return  # Exit early if rate limit exceeded

            # Sanitize and check input
            sanitized_text = sanitize_input(update.message.text)
            if len(sanitized_text) > 2000:  # Reasonable limit for URLs
                logger.warning(f"Message too long from {user_hash}")
                msg = update.message.reply_text('Message too long')
                context.job_queue.run_once(
                    lambda _: delete_message_after_delay(context, update.message.chat_id, msg.message_id),
                    300
                )
                return

            # Process the message (e.g., clean URL)
            # For now, just send a placeholder message
            msg = update.message.reply_text('URL cleaning functionality coming soon!')
            context.job_queue.run_once(
                lambda _: delete_message_after_delay(context, update.message.chat_id, msg.message_id),
                300
            )
    finally:
        cleanup_session()

def main(request):
    """Cloud Function entry point."""
    try:
        # Parse the request body
        if request.method != "POST":
            logger.warning("Invalid request method")
            return 'Only POST requests are accepted', 405

        # Log minimal request info
        request_json = request.get_json(force=True)
        update_type = 'message' if 'message' in request_json else 'callback_query' if 'callback_query' in request_json else 'unknown'
        logger.info(f"Update type: {update_type}")

        try:
            # Initialize bot and get the update
            bot = Bot(token=TELEGRAM_TOKEN)
            update = Update.de_json(request_json, bot)

            # Set up the dispatcher
            dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
            
            # Add handlers
            dispatcher.add_handler(CommandHandler("start", start))
            dispatcher.add_handler(CommandHandler("help", help_command))
            dispatcher.add_handler(CommandHandler("privacy", privacy_command))
            dispatcher.add_handler(CommandHandler("delete", delete_command))
            dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

            # Process the update
            dispatcher.process_update(update)
            
            return 'OK', 200

        except Exception as e:
            # Log specific bot-related errors
            error_type = type(e).__name__
            logger.error(f"Bot error: {error_type}")
            if hasattr(e, 'message'):
                # Only log error message if it exists and doesn't contain PII
                safe_error = sanitize_input(str(e.message))
                logger.error(f"Error details: {safe_error}")
            return {'error': error_type}, 500

    except Exception as e:
        # Log general errors
        logger.error(f"Error: {type(e).__name__}")
        return 'Error processing update', 500
    
    finally:
        cleanup_session()
