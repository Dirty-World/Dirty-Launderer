import os
import logging
from telegram import Bot
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

async def send_alert(message: str, bot: Bot = None) -> bool:
    """
    Send an alert message to the admin chat.
    
    Args:
        message (str): The message to send
        bot (Bot, optional): The Telegram bot instance. If not provided, a new one will be created.
        
    Returns:
        bool: True if the alert was sent successfully, False otherwise
    """
    try:
        # Get admin chat ID from environment variable
        admin_chat_id = os.environ.get('ALERT_CHAT_ID')
        if not admin_chat_id:
            logger.error("ALERT_CHAT_ID environment variable not set")
            return False
            
        # Create bot instance if not provided
        if not bot:
            token = os.environ.get('TELEGRAM_BOT_TOKEN')
            if not token:
                logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
                return False
            bot = Bot(token=token)
            
        # Send alert message
        await bot.send_message(
            chat_id=admin_chat_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        return True
        
    except Exception as e:
        logger.error(f"Failed to send alert: {str(e)}")
        return False 