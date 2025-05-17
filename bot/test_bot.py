import logging
from google.cloud import secretmanager
import requests
import time
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from main import process_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project configuration
PROJECT_ID = "the-dirty-launderer"
BOT_TOKEN_SECRET = "TELEGRAM_BOT_TOKEN"
CHAT_ID_SECRET = "ADMIN_CHAT_ID"

def get_secret(project_id, secret_name):
    """Get secret from Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        logger.error(f"Error accessing secret: {e}")
        raise

def test_bot():
    """Test the bot by sending commands and messages."""
    try:
        # Get bot token and chat ID
        token = get_secret(PROJECT_ID, BOT_TOKEN_SECRET)
        chat_id = get_secret(PROJECT_ID, CHAT_ID_SECRET)
        logger.info("Successfully retrieved secrets")
        logger.info(f"Chat ID: {chat_id}")

        # Test /start command
        start_url = f"https://api.telegram.org/bot{token}/sendMessage"
        start_data = {
            "chat_id": chat_id,
            "text": "/start"
        }
        logger.info(f"Sending request to: {start_url}")
        logger.info(f"With data: {json.dumps(start_data)}")
        
        start_response = requests.post(start_url, json=start_data)
        try:
            start_response.raise_for_status()
            logger.info(f"Sent /start command, response: {start_response.json()}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            logger.error(f"Response content: {start_response.text}")
            raise

        # Wait a bit for the bot to process
        time.sleep(2)

        # Test URL cleaning with a sample URL
        test_url = "https://twitter.com/example/status/123?utm_source=test&utm_medium=test"
        message_url = f"https://api.telegram.org/bot{token}/sendMessage"
        message_data = {
            "chat_id": chat_id,
            "text": test_url
        }
        message_response = requests.post(message_url, json=message_data)
        message_response.raise_for_status()
        logger.info(f"Sent test URL, response: {message_response.json()}")

        logger.info("Test completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error testing bot: {e}")
        return False

if __name__ == "__main__":
    test_bot() 