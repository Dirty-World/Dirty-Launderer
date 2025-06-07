import os
import json
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ApplicationHandlerStop
import hashlib
from urllib.parse import urlparse
import gc
import time
from collections import defaultdict
import re
import html
import asyncio
from flask import Flask, request, jsonify
from utils.rate_limiter import check_rate_limit, cleanup_session
from utils.input_sanitizer import sanitize_input, get_safe_domain
from utils.alert import send_alert
from typing import Dict, List, Optional, Any

# Configure logging with minimal metadata
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'  # Removed timestamp and logger name
)
logger = logging.getLogger(__name__)

# User consent store
user_consent = set()

app = Flask(__name__)

# Get environment variables
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
FIRESTORE_FUNCTION_URL = os.environ.get('FIRESTORE_FUNCTION_URL')
HASH_SALT = os.environ.get('HASH_SALT', 'default-salt')

def get_telegram_token():
    """Get the Telegram bot token from environment variable."""
    try:
        logger.debug("Attempting to get TELEGRAM_TOKEN from environment")
        token = TELEGRAM_TOKEN
        if not token:
            logger.error("Failed to get TELEGRAM_TOKEN from environment")
            raise EnvironmentError("Failed to get TELEGRAM_TOKEN from environment")
        logger.debug("Successfully retrieved TELEGRAM_TOKEN")
        return token
    except Exception as e:
        logger.error(f"Error getting token from environment: {str(e)}")
        raise

def hash_user_id(user_id: int) -> str:
    """Hash a user ID to avoid storing PII."""
    return hashlib.sha256(f"{HASH_SALT}{user_id}".encode()).hexdigest()[:8]

def hash_domain(domain: str) -> str:
    """Hash a domain to avoid storing PII."""
    if not domain:
        return 'unknown'
    return hashlib.sha256(f"{HASH_SALT}{domain.lower()}".encode()).hexdigest()[:8]

def get_group_config(chat_id: str) -> Dict[str, Any]:
    """Get configuration for a specific group."""
    try:
        response = requests.post(
            FIRESTORE_FUNCTION_URL,
            json={
                'action': 'get_group_config',
                'chat_id': chat_id
            }
        )
        response.raise_for_status()
        return response.json()['config']
    except Exception as e:
        logger.error(f"Error getting group config: {str(e)}")
        return {
            "default_behavior": "clean",
            "domain_rules": {}
        }

def update_group_config(chat_id: str, config: Dict[str, Any]) -> bool:
    """Update configuration for a specific group."""
    try:
        response = requests.post(
            FIRESTORE_FUNCTION_URL,
            json={
                'action': 'update_group_config',
                'chat_id': chat_id,
                'config': config
            }
        )
        response.raise_for_status()
        return response.json()['success']
    except Exception as e:
        logger.error(f"Error updating group config: {str(e)}")
        return False

def get_proxy_config() -> Dict[str, List[str]]:
    """Get the current proxy configuration."""
    try:
        response = requests.post(
            FIRESTORE_FUNCTION_URL,
            json={
                'action': 'get_proxy_config'
            }
        )
        response.raise_for_status()
        return response.json()['config']
    except Exception as e:
        logger.error(f"Error getting proxy config: {str(e)}")
        return {}

def get_user_consent(user_id: str) -> bool:
    """Check if a user has given consent."""
    try:
        response = requests.post(
            FIRESTORE_FUNCTION_URL,
            json={
                'action': 'get_user_consent',
                'user_id': user_id
            }
        )
        response.raise_for_status()
        return response.json()['has_consent']
    except Exception as e:
        logger.error(f"Error checking user consent: {str(e)}")
        return False

def set_user_consent(user_id: str, has_consent: bool = True) -> bool:
    """Set user consent status."""
    try:
        response = requests.post(
            FIRESTORE_FUNCTION_URL,
            json={
                'action': 'set_user_consent',
                'user_id': user_id,
                'has_consent': has_consent
            }
        )
        response.raise_for_status()
        return response.json()['success']
    except Exception as e:
        logger.error(f"Error setting user consent: {str(e)}")
        return False

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
                msg = await update.message.reply_text("URL is too long. Please send a shorter URL.")
                context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
                return

            # Get group config
            group_config = get_group_config(str(update.message.chat_id))
            
            # Get domain from URL
            domain = get_safe_domain(sanitized_text)
            if not domain:
                msg = await update.message.reply_text("Invalid URL. Please send a valid URL.")
                context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
                return

            # Check domain rules
            hashed_domain = hash_domain(domain)
            if hashed_domain in group_config.get("domain_rules", {}):
                rule = group_config["domain_rules"][hashed_domain]
                if rule.get("behavior") == "block":
                    msg = await update.message.reply_text(f"Domain blocked: {rule.get('reason', 'No reason provided')}")
                    context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
                    return

            # Process URL based on default behavior
            if group_config.get("default_behavior") == "block":
                msg = await update.message.reply_text("URL processing is blocked in this group.")
                context.application.create_task(delete_message_after_delay(context, update.message.chat_id, msg.message_id))
                return

            # Continue with URL processing...
            # ... rest of the message handling code ...

    except Exception as e:
        logger.error(f"Error handling message: {type(e).__name__}")
        raise ApplicationHandlerStop()
    finally:
        cleanup_session()

async def process_update(request_json):
    """Process a Telegram update."""
    try:
        # Create application
        application = ApplicationBuilder().token(get_telegram_token()).build()
        
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
async def main(request):
    """Main entry point for the Cloud Function."""
    try:
        # Validate request method
        if request.method != "POST":
            return jsonify({"error": "Method not allowed"}), 405

        # Parse JSON
        try:
            update = request.get_json()
        except Exception as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            return jsonify({"error": "Invalid JSON"}), 400

        # Process update
        try:
            response = await process_update(update)
            return jsonify(response), 200
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

