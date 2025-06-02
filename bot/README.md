# Dirty Launderer Bot

## Environment Variables

The bot uses environment variables for configuration and secrets. Copy `env.example` to `.env` and fill in your values:

```bash
cp env.example .env
```

Required environment variables:
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `CODECOV_TOKEN`: Your Codecov token (if using code coverage)

## Development

1. Create a virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your values
```

4. Run tests:
```bash
pytest
```

## Deployment

For deployment, set the required environment variables in your deployment platform (e.g., Heroku, Google Cloud Run, etc.).

### Production Dependencies

For production deployment, use the production requirements file which includes only the essential packages:

```bash
pip install -r requirements-prod.txt
```

This will install only the necessary packages for running the bot in production, excluding development and testing dependencies.

### Environment Variables in Production

The bot expects the following environment variables to be set in production:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- Any other secrets used by your bot

You can set these in your deployment platform's environment configuration or secret management system. 