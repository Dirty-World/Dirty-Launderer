import pytest
from unittest.mock import patch, MagicMock
import os
import asyncio

# Mock webhook URL for testing
WEBHOOK_URL = "http://localhost:8080/webhook"

@pytest.fixture(autouse=True)
def mock_secret_manager():
    """Mock the secret manager for all tests."""
    with patch('main.get_secret') as mock_get_secret:
        def mock_get_secret_impl(secret_id):
            # Return mock values for testing
            mock_secrets = {
                'TELEGRAM_BOT_TOKEN': 'mock-telegram-token',
                'ADMIN_CHAT_ID': '123456789',
                'GCP_PROJECT_ID': 'mock-project-id'
            }
            if secret_id not in mock_secrets:
                raise Exception(f"Mock secret {secret_id} not found")
            return mock_secrets[secret_id]
        
        mock_get_secret.side_effect = mock_get_secret_impl
        yield mock_get_secret

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Set mock environment variables
    os.environ['GCP_PROJECT_ID'] = 'mock-project-id'
    os.environ['HASH_SALT'] = 'test-salt'
    
    yield
    
    # Clean up
    os.environ.pop('GCP_PROJECT_ID', None)
    os.environ.pop('HASH_SALT', None)

@pytest.fixture(autouse=True)
def mock_webhook_url():
    """Mock the webhook URL for testing."""
    with patch('tests.test_webhook_health.WEBHOOK_URL', WEBHOOK_URL):
        yield

@pytest.fixture(autouse=True)
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 123456, "first_name": "Test"},
            "chat": {"id": 123456, "type": "private"},
            "text": "/start"
        }
    }
    return request 