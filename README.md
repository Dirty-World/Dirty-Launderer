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

## License

MIT License - see LICENSE file for details 