import os
import asyncio
import sys
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import start, help_command, privacy_command, delete_command, handle_message

async def test_bot():
    """Test core bot functionality."""
    print("Testing bot initialization...")
    
    # Test environment setup
    token = os.environ.get('TELEGRAM_TOKEN')
    if not token:
        print("Error: TELEGRAM_TOKEN environment variable not set")
        return
    
    try:
        # Initialize bot
        application = ApplicationBuilder().token(token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("privacy", privacy_command))
        application.add_handler(CommandHandler("delete", delete_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Bot initialized successfully")
        print("Core functionality test passed")
        
    except Exception as e:
        print(f"Error during bot initialization: {type(e).__name__}: {str(e)}")
        return

if __name__ == "__main__":
    asyncio.run(test_bot()) 