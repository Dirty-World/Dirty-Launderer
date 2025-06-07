import os
import json
import logging
from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ApplicationHandlerStop
import hashlib
from urllib.parse import urlparse
import gc
import time
from collections import defaultdict
import re
import html
from utils.secret_manager import get_secret
import asyncio
from flask import Flask, request
from utils.rate_limiter import check_rate_limit
from utils.input_sanitizer import sanitize_input, get_safe_domain
from utils.alert import send_alert

# Configure logging with minimal metadata
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'  # Removed timestamp and logger name
)
logger = logging.getLogger(__name__)

# Rate limiting
RATE_LIMIT = 10  # requests per minute
rate_limit_store = defaultdict(list)

# User consent store
user_consent = set()

app = Flask(__name__)

def get_telegram_token():
    """Get the Telegram bot token from Secret Manager."""
    try:
        logger.debug("Attempting to get TELEGRAM_BOT_TOKEN from Secret Manager")
        token = get_secret('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("Failed to get TELEGRAM_BOT_TOKEN from Secret Manager")
            raise EnvironmentError("Failed to get TELEGRAM_BOT_TOKEN from Secret Manager")
        logger.debug("Successfully retrieved TELEGRAM_BOT_TOKEN")
        return token
    except Exception as e:
        logger.error(f"Error getting token from Secret Manager: {str(e)}")
        raise

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
        if not parsed.netloc:
            return 'invalid-url'
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
        return False, "Rate limit exceeded. Please try again in a minute."
    
    user_requests.append(current_time)
    return True, None

async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id, message_id):
    """Delete message after 5 minutes for privacy."""
    try:
        await asyncio.sleep(300)  # 5 minutes
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.error(f"Error deleting message: {type(e).__name__}")

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send privacy policy information."""
    try:
        user_hash = hash_user_id(update.effective_user.id if update.effective_user else None)
        rate_ok, rate_message = check_rate_limit(user_hash)
        if not rate_ok:
            msg = await update.message.reply_text(rate_message)
            context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
            return

        try:
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
            msg = await update.message.reply_text(privacy_text, parse_mode=ParseMode.MARKDOWN)
            context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
        except Exception as e:
            logger.error(f"Error sending privacy message: {type(e).__name__}")
            raise ApplicationHandlerStop()
    except ApplicationHandlerStop:
        raise
    except Exception as e:
        logger.error(f"Error in privacy command: {type(e).__name__}")
        raise ApplicationHandlerStop()
    finally:
        cleanup_session()

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete user's messages for privacy."""
    try:
        user_hash = hash_user_id(update.effective_user.id if update.effective_user else None)
        rate_ok, rate_message = check_rate_limit(user_hash)
        if not rate_ok:
            msg = await update.message.reply_text(rate_message)
            context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
            return

        try:
            if update.message.reply_to_message:
                try:
                    await update.message.reply_to_message.delete()
                except Exception:
                    pass
            await update.message.delete()
        except Exception as e:
            logger.error(f"Error deleting messages: {type(e).__name__}")
            raise ApplicationHandlerStop()
    except ApplicationHandlerStop:
        raise
    except Exception as e:
        logger.error(f"Error in delete command: {type(e).__name__}")
        raise ApplicationHandlerStop()
    finally:
        cleanup_session()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    try:
        user_hash = hash_user_id(update.effective_user.id if update.effective_user else None)
        rate_ok, rate_message = check_rate_limit(user_hash)
        if not rate_ok:
            msg = await update.message.reply_text(rate_message)
            context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
            return

        logger.info(f"Command: start, User: {user_hash}")
        try:
            msg = await update.message.reply_text(
                'Hi! I am The Dirty Launderer🧼 bot. Send me a URL and I will clean it for you.\n'
                'Use /help to see available commands.'
            )
            context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
        except Exception as e:
            logger.error(f"Error sending start message: {type(e).__name__}")
            raise ApplicationHandlerStop()
    except ApplicationHandlerStop:
        raise
    except Exception as e:
        logger.error(f"Error in start command: {type(e).__name__}")
        raise ApplicationHandlerStop()
    finally:
        cleanup_session()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    try:
        user_hash = hash_user_id(update.effective_user.id if update.effective_user else None)
        rate_ok, rate_message = check_rate_limit(user_hash)
        if not rate_ok:
            msg = await update.message.reply_text(rate_message)
            context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
            return

        logger.info(f"Command: help, User: {user_hash}")
        try:
            msg = await update.message.reply_text(
                'The Dirty Launderer🧼 is here to help!\n\n'
                'Send me any URL and I will remove tracking parameters and proxy it through privacy-friendly frontends.\n\n'
                'Commands:\n'
                '/privacy - View privacy policy\n'
                '/delete - Delete messages\n'
                '/help - Show this help\n\n'
                'Made with 🧼 by The Dirty Launderer🧼 team'
            )
            context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
        except Exception as e:
            logger.error(f"Error sending help message: {type(e).__name__}")
            raise ApplicationHandlerStop()
    except ApplicationHandlerStop:
        raise
    except Exception as e:
        logger.error(f"Error in help command: {type(e).__name__}")
        raise ApplicationHandlerStop()
    finally:
        cleanup_session()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    try:
        if update.message and update.message.text:
            user_hash = hash_user_id(update.effective_user.id if update.effective_user else None)
            rate_ok, rate_message = check_rate_limit(user_hash)
            if not rate_ok:
                msg = await update.message.reply_text(rate_message)
                context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
                return

            # Sanitize and check input
            sanitized_text = sanitize_input(update.message.text)
            if len(sanitized_text) > 2000:  # Reasonable limit for URLs
                logger.warning(f"Message too long from {user_hash}")
                msg = await update.message.reply_text('Message too long')
                context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
                return

            # Process the message (e.g., clean URL)
            # For now, just send a placeholder message
            msg = await update.message.reply_text('URL cleaning functionality coming soon!')
            context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        if update.message:
            try:
                msg = await update.message.reply_text("Sorry, I encountered an error processing your message.")
                context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
            except Exception as reply_error:
                logger.error(f"Error sending error message: {str(reply_error)}")
    finally:
        cleanup_session()

async def process_update(request_json):
    """Process a Telegram update."""
    try:
        # Create application
        application = ApplicationBuilder().token(get_secret("TELEGRAM_BOT_TOKEN")).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("privacy", privacy_command))
        application.add_handler(CommandHandler("delete", delete_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Add error handler
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Handle errors in a user-friendly way."""
            try:
                logger.error(f"Error: {context.error}")
                if update and update.effective_message:
                    try:
                        msg = await update.effective_message.reply_text(
                            "Sorry, something went wrong. Please try again later."
                        )
                        # Schedule message deletion
                        asyncio.create_task(delete_message_after_delay(context, update.effective_message.chat_id, msg.message_id))
                    except Exception as e:
                        logger.error(f"Error sending error message: {type(e).__name__}")
            except Exception as e:
                logger.error(f"Error in error handler: {type(e).__name__}")
            finally:
                cleanup_session()
        
        application.add_error_handler(error_handler)
        
        # Process update
        update = Update.de_json(request_json, application.bot)
        await application.process_update(update)
        
        return ({"status": "ok"}, 200)
    except Exception as e:
        logger.error(f"Error processing update: {type(e).__name__}: {str(e)}")
        return ({"error": "Bad request"}, 400)
    finally:
        # Clean up
        if 'application' in locals():
            await application.shutdown()

@app.route('/', methods=['POST'])
def main(request):
    """Main entry point for the Cloud Function."""
    try:
        # Validate request method
        if request.method != "POST":
            logger.error(f"Invalid request method: {request.method}")
            return ({"error": "Method not allowed"}, 405)

        # Parse request JSON
        try:
            request_json = request.get_json()
        except Exception as e:
            logger.error(f"Invalid JSON: {str(e)}")
            return ({"error": "Invalid JSON"}, 400)

        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Process update
            result = loop.run_until_complete(process_update(request_json))
            return result
        except Exception as e:
            logger.error(f"Error processing update: {type(e).__name__}: {str(e)}")
            return ({"error": "Bad request"}, 400)
        finally:
            # Clean up event loop
            loop.close()
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}")
        return ({"error": "Bad request"}, 400)

