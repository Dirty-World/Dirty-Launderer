# Dirty Launderer Bot

A Telegram bot for cleaning and sanitizing URLs, removing tracking parameters, and ensuring safe navigation.

## Features

- URL cleaning and sanitization
- Tracking parameter removal
- Rate limiting
- PII detection and handling
- Secure secret management
- Health monitoring

## Installation

```bash
pip install dirty-launderer-bot
```

For development:
```bash
pip install -e ".[dev]"
```

## Usage

```python
from bot import main

# Run the bot
main()
```

Or use the command-line interface:
```bash
dirty-launderer
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/gregmiller/Dirty-Launderer.git
cd Dirty-Launderer/bot
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Run tests:
```bash
pytest
```

## Configuration

The bot requires the following environment variables:
- `TELEGRAM_TOKEN`: Your Telegram bot token
- `EXPECTED_WEBHOOK_URL`: The webhook URL for your bot
- `ALERT_CHAT_ID`: Chat ID for admin alerts

## Error Handling

The bot follows a simple but effective error handling strategy:

### Architecture

1. **Command Handlers**
   - Each command handler (`start`, `help`, `privacy`, `delete`) has its own error handling
   - Errors are logged with detailed information
   - User-friendly error messages are sent to the chat
   - Messages are auto-deleted after 5 minutes for privacy

2. **Message Handler**
   - Handles all non-command messages
   - Attempts to send user-friendly error messages
   - Falls back gracefully if error message can't be sent

3. **Application Error Handler**
   - Catches all errors in handlers
   - Logs errors with type information
   - Lets errors propagate naturally

4. **Main Function**
   - Handles HTTP-level errors (invalid method, JSON parsing)
   - Treats all bot errors as client-side issues (400)
   - Provides detailed error logging
   - Ensures cleanup after each request

### Best Practices

1. **Error Types**
   - All errors are treated as client-side issues (400)
   - No distinction between API and server errors
   - Detailed error logging for debugging
   - User-friendly error messages in chat

2. **Error Flow**
   ```
   Command/Message Handler
   ↓
   Application Error Handler (logs error)
   ↓
   Process Update (re-raises error)
   ↓
   Main Function (returns 400)
   ```

3. **Logging**
   - Use `logger.error()` for all errors
   - Include error type in logs
   - Sanitize user input before logging
   - Hash user IDs for privacy

4. **Cleanup**
   - Always call `cleanup_session()` in finally blocks
   - Delete error messages after 5 minutes
   - Clear rate limiting data
   - Run garbage collection

### Example

```python
async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Command logic here
        await update.message.reply_text("Success!")
    except Exception as e:
        logger.error(f"Error in command: {type(e).__name__}")
        # Send user-friendly error message
        msg = await update.message.reply_text("Sorry, something went wrong.")
        # Auto-delete after 5 minutes
        context.application.create_task(
            delete_message_after_delay(context, update.message.chat_id, msg.message_id)
        )
    finally:
        cleanup_session()

## License

MIT License - see LICENSE file for details 