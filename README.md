# The Dirty Launderer Bot

A Telegram bot that cleans URLs by removing tracking parameters and proxying through privacy-friendly frontends.

## Features

- URL cleaning and tracking parameter removal
- Privacy-friendly frontend proxying
- Rate limiting
- Auto-deleting messages
- No data storage
- Minimal logging

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Set up environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your-bot-token"
   export EXPECTED_WEBHOOK_URL="your-webhook-url"
   export ALERT_CHAT_ID="admin-chat-id"
   ```

2. Run the bot:
   ```bash
   python bot/main.py
   ```

## Development

### Architecture

The bot uses a hybrid async/sync architecture with multiple Cloud Functions:

1. **Main Bot Function (Sync)**:
   - Entry point for Cloud Functions
   - Handles HTTP requests
   - Creates event loop for async operations
   - Returns HTTP responses
   - Dependencies: python-telegram-bot, flask, requests

2. **Webhook Check Function (Sync)**:
   - Monitors webhook configuration
   - Sends alerts for misconfigurations
   - Dependencies: google-cloud-secret-manager, requests

3. **Firestore Function (Sync)**:
   - Manages database operations
   - Handles data persistence
   - Dependencies: google-cloud-firestore

4. **Process Update (Async)**:
   - Processes Telegram updates
   - Handles message routing
   - Manages bot state
   - Returns operation results

5. **Command Handlers (Async)**:
   - Handle specific commands
   - Process user input
   - Send responses
   - Manage rate limiting

### Event Loop Management

The bot uses a per-request event loop pattern:

1. **Loop Creation**:
   ```python
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   ```

2. **Async Execution**:
   ```python
   result = loop.run_until_complete(process_update(request_json))
   ```

3. **Cleanup**:
   ```python
   loop.close()
   ```

### Error Handling

The bot implements a comprehensive error handling strategy:

1. **Client Errors (400)**:
   - Invalid requests
   - Rate limiting
   - User input errors

2. **Server Errors (500)**:
   - Internal processing errors
   - External service failures
   - Resource exhaustion

### Resource Management

1. **Memory**:
   - Per-request cleanup
   - No persistent storage
   - Garbage collection after requests

2. **Connections**:
   - Short-lived connections
   - Proper cleanup
   - Timeout handling

### Testing

Run tests with:
```bash
pytest
```

Test categories:
- Unit tests
- Integration tests
- Error handling tests
- Resource limit tests

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN`: Bot authentication token
- `EXPECTED_WEBHOOK_URL`: Webhook URL for updates
- `ALERT_CHAT_ID`: Admin chat for alerts
- `HASH_SALT`: Salt for user ID hashing
- `GCS_BUCKET_NAME`: GCS bucket for function source code
- `PROJECT_ID`: Google Cloud project ID

### Dependencies

Each function has its own requirements file:
- `requirements-main.txt`: Main bot function dependencies
- `requirements-webhook.txt`: Webhook check function dependencies
- `requirements-firestore.txt`: Firestore function dependencies

### Rate Limiting

- Default: 10 requests per minute
- Configurable via `RATE_LIMIT` constant
- Per-user tracking
- Auto-cleanup of old entries

## License

MIT License - see LICENSE.md for details 