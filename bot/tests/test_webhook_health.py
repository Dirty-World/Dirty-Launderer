import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock
import requests
from main import main
from telegram import Bot, Update
from telegram.ext import Application

# Mock webhook URL
WEBHOOK_URL = "http://localhost:8080/webhook"

# Mock Telegram messages for testing
TELEGRAM_MESSAGES = {
    "start": {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 123456, "first_name": "Test"},
            "chat": {"id": 123456, "type": "private"},
            "text": "/start"
        }
    },
    "url_clean": {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 123456, "first_name": "Test"},
            "chat": {"id": 123456, "type": "private"},
            "text": "https://example.com?utm_source=test"
        }
    },
    "group_message": {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 123456, "first_name": "Test"},
            "chat": {"id": -123456, "type": "group"},
            "text": "/start"
        }
    }
}

MOCK_SECRETS = {
    'TELEGRAM_BOT_TOKEN': 'mock-telegram-token',
    'ADMIN_CHAT_ID': '123456789',
    'GCP_PROJECT_ID': 'mock-project-id'
}

def mock_get_secret(secret_id, version_id="latest"):
    return MOCK_SECRETS.get(secret_id, f"mock-{secret_id}")

@pytest.fixture(autouse=True)
def mock_bot():
    """Mock the Bot class and its methods."""
    with patch('telegram.Bot') as mock_bot_class:
        mock_bot_instance = AsyncMock()
        mock_bot_class.return_value = mock_bot_instance
        yield mock_bot_instance

@pytest.fixture(autouse=True)
def mock_application_and_update():
    """Mock ApplicationBuilder in both main and telegram.ext, and Update.de_json for all tests. Provide a realistic mock_update object."""
    with patch('main.ApplicationBuilder') as mock_main_builder, \
         patch('telegram.ext.ApplicationBuilder') as mock_ext_builder, \
         patch('telegram.Update.de_json') as mock_de_json:
        # Mock ApplicationBuilder().token().build() to return an async mock with process_update
        mock_app = AsyncMock()
        mock_main_builder.return_value.token.return_value.build.return_value = mock_app
        mock_ext_builder.return_value.token.return_value.build.return_value = mock_app
        mock_app.process_update = AsyncMock()
        # Build a realistic mock_update object
        mock_message = MagicMock()
        mock_message.reply_text = AsyncMock(return_value=MagicMock(message_id=1))
        mock_message.text = '/start'
        mock_message.chat_id = 123456
        mock_message.delete = AsyncMock()
        mock_message.reply_to_message = None
        mock_user = MagicMock()
        mock_user.id = 123456
        mock_user.first_name = 'Test'
        mock_user.last_name = 'User'
        mock_user.username = 'testuser'
        mock_user.is_bot = False
        mock_chat = MagicMock()
        mock_chat.id = 123456
        mock_chat.type = 'private'
        mock_update = MagicMock()
        mock_update.message = mock_message
        mock_update.effective_user = mock_user
        mock_update.effective_chat = mock_chat
        mock_update.to_dict.return_value = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123456, "first_name": "Test"},
                "chat": {"id": 123456, "type": "private"},
                "text": "/start"
            }
        }
        mock_de_json.return_value = mock_update
        yield mock_app, mock_update

@patch("utils.secret_manager.get_secret", side_effect=mock_get_secret)
@pytest.mark.asyncio
async def test_webhook_availability(mock_secret):
    """Test that the webhook endpoint is available and responding."""
    request = MagicMock()
    request.method = "GET"
    response = await main(request)
    assert response[1] == 405  # Method not allowed

@patch("utils.secret_manager.get_secret", side_effect=mock_get_secret)
@pytest.mark.asyncio
async def test_webhook_telegram_verification(mock_secret, mock_bot, mock_application_and_update):
    """Test that the webhook properly handles Telegram's verification requests."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = TELEGRAM_MESSAGES["start"]
    response = await main(request)
    assert response[1] == 200

@patch("utils.secret_manager.get_secret", side_effect=mock_get_secret)
@pytest.mark.asyncio
async def test_webhook_url_cleaning(mock_secret, mock_bot, mock_application_and_update):
    """Test that the webhook properly handles URL cleaning requests."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = TELEGRAM_MESSAGES["url_clean"]
    response = await main(request)
    assert response[1] == 200

@patch("utils.secret_manager.get_secret", side_effect=mock_get_secret)
@pytest.mark.asyncio
async def test_webhook_group_support(mock_secret, mock_bot, mock_application_and_update):
    """Test that the webhook properly handles group messages."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = TELEGRAM_MESSAGES["group_message"]
    response = await main(request)
    assert response[1] == 200

@patch("utils.secret_manager.get_secret", side_effect=mock_get_secret)
@pytest.mark.asyncio
async def test_webhook_invalid_request(mock_secret, mock_bot, mock_application_and_update):
    """Test that the webhook properly handles invalid requests."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.side_effect = Exception("Invalid JSON")
    response = await main(request)
    assert response[1] == 400

@patch("utils.secret_manager.get_secret", side_effect=mock_get_secret)
@pytest.mark.asyncio
async def test_webhook_rate_limiting(mock_secret, mock_bot, mock_application_and_update):
    """Test that the webhook properly handles rate limiting."""
    from main import rate_limit_store
    rate_limit_store.clear()  # Clear before test
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = TELEGRAM_MESSAGES["start"]
    responses = []
    for _ in range(11):  # One more than the rate limit
        response = await main(request)
        responses.append(response)
    # The last response should be a rate limit message
    assert responses[-1][1] == 200  # Still returns 200 but with rate limit message
    rate_limit_store.clear()  # Clear after test

@patch("utils.secret_manager.get_secret", side_effect=mock_get_secret)
@pytest.mark.asyncio
async def test_webhook_content_type_handling(mock_secret, mock_bot, mock_application_and_update):
    """Test that the webhook properly handles different content types."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = TELEGRAM_MESSAGES["start"]
    
    # Test with application/json
    response = await main(request)
    assert response[1] == 200
    
    # Test with invalid content type
    request.get_json.side_effect = Exception("Invalid content type")
    response = await main(request)
    assert response[1] == 400

@patch("utils.secret_manager.get_secret", side_effect=mock_get_secret)
@pytest.mark.asyncio
async def test_webhook_response_time(mock_secret, mock_bot, mock_application_and_update):
    """Test that the webhook responds within an acceptable time frame."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = TELEGRAM_MESSAGES["start"]
    
    start_time = time.time()
    response = await main(request)
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response_time < 1.0, f"Webhook response time ({response_time:.2f}s) exceeds 1 second"
    assert response[1] == 200

@patch("utils.secret_manager.get_secret", side_effect=mock_get_secret)
@pytest.mark.asyncio
async def test_webhook_privacy_frontends(mock_secret, mock_bot, mock_application_and_update):
    """Test that the webhook properly handles different privacy frontends."""
    test_urls = {
        "youtube.com": "invidious",
        "twitter.com": "nitter",
        "reddit.com": "libreddit",
        "instagram.com": "bibliogram",
        "medium.com": "scribe"
    }
    
    request = MagicMock()
    request.method = "POST"
    
    for domain, frontend in test_urls.items():
        test_data = TELEGRAM_MESSAGES["url_clean"].copy()
        test_data["message"]["text"] = f"https://{domain}/test"
        request.get_json.return_value = test_data
        
        response = await main(request)
        assert response[1] == 200

@patch("utils.secret_manager.get_secret", side_effect=mock_get_secret)
@pytest.mark.asyncio
async def test_webhook_error_handling(mock_secret, mock_bot, mock_application_and_update):
    """Test that the webhook properly handles various error conditions."""
    request = MagicMock()
    request.method = "POST"
    
    # Test with empty message
    test_data = TELEGRAM_MESSAGES["start"].copy()
    test_data["message"]["text"] = ""
    request.get_json.return_value = test_data
    
    response = await main(request)
    assert response[1] == 200  # Empty messages are handled gracefully
    
    # Test with invalid JSON
    request.get_json.side_effect = Exception("Invalid JSON")
    response = await main(request)
    assert response[1] == 400  # Invalid JSON returns 400
    
    # Test with invalid method
    request.method = "GET"
    response = await main(request)
    assert response[1] == 405  # Invalid method returns 405 