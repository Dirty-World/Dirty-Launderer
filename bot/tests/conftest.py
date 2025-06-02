import pytest
from unittest.mock import patch
import os

# Mock secrets for testing
MOCK_SECRETS = {
    'TELEGRAM_BOT_TOKEN': 'mock_telegram_token',
    'ADMIN_CHAT_ID': '4666042499'
}

@pytest.fixture(autouse=True)
def mock_secret_manager():
    """Mock the secret manager for all tests."""
    with patch('bot.utils.secret_manager.get_secret') as mock_get_secret:
        def mock_get_secret_impl(secret_id):
            if secret_id in MOCK_SECRETS:
                return MOCK_SECRETS[secret_id]
            raise Exception(f"Mock secret {secret_id} not found")
        
        mock_get_secret.side_effect = mock_get_secret_impl
        yield mock_get_secret

@pytest.fixture(autouse=True)
def mock_environment():
    """Set up mock environment variables for testing."""
    os.environ['TELEGRAM_TOKEN'] = MOCK_SECRETS['TELEGRAM_BOT_TOKEN']
    os.environ['ADMIN_CHAT_ID'] = MOCK_SECRETS['ADMIN_CHAT_ID']
    yield
    # Clean up
    os.environ.pop('TELEGRAM_TOKEN', None)
    os.environ.pop('ADMIN_CHAT_ID', None) 