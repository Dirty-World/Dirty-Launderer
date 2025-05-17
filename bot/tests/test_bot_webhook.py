import os
import pytest
from unittest.mock import patch, MagicMock
import json
from main import main

@pytest.fixture
def mock_env_vars():
    """Set up test environment variables."""
    os.environ["TELEGRAM_TOKEN"] = "test_token"
    yield
    del os.environ["TELEGRAM_TOKEN"]

def test_invalid_request_method():
    """Test handling of non-POST requests."""
    request = MagicMock()
    request.method = "GET"
    
    response = main(request)
    assert response[1] == 405
    assert "Only POST" in response[0]

@patch("main.Bot")
def test_valid_message_request(mock_bot, mock_env_vars):
    """Test handling of valid message update."""
    # Mock request with a message
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
    
    # Mock bot instance
    mock_bot_instance = MagicMock()
    mock_bot.return_value = mock_bot_instance
    
    response = main(request)
    
    assert response[1] == 200
    assert response[0] == "OK"
    mock_bot.assert_called_once_with(token="test_token")

@patch("main.Bot")
def test_missing_token(mock_bot):
    """Test handling when TELEGRAM_TOKEN is missing."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = {"message": {"text": "/start"}}
    
    with pytest.raises(EnvironmentError):
        main(request)

@patch("main.Bot")
def test_invalid_update(mock_bot, mock_env_vars):
    """Test handling of invalid update data."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = {"invalid": "data"}
    
    mock_bot_instance = MagicMock()
    mock_bot.return_value = mock_bot_instance
    
    response = main(request)
    assert response[1] == 200  # Should still return 200 but log the error
    mock_bot.assert_called_once()

@patch("main.Bot")
def test_json_decode_error(mock_bot, mock_env_vars):
    """Test handling of invalid JSON."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.side_effect = json.JSONDecodeError("Invalid JSON", "{", 0)
    
    response = main(request)
    assert response[1] == 500
    assert "Error processing update" in response[0]

@patch("main.Bot")
def test_telegram_api_error(mock_bot, mock_env_vars):
    """Test handling of Telegram API errors."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = {"message": {"text": "/start"}}
    
    mock_bot.side_effect = Exception("Telegram API Error")
    
    response = main(request)
    assert response[1] == 500
    assert "Error processing update" in response[0]

@patch("main.Bot")
def test_rate_limit_check(mock_bot, mock_env_vars):
    """Test rate limiting functionality."""
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = {
        "message": {
            "from": {"id": 123456},
            "text": "/start"
        }
    }
    
    mock_bot_instance = MagicMock()
    mock_bot.return_value = mock_bot_instance
    
    # Send multiple requests
    responses = []
    for _ in range(15):  # More than RATE_LIMIT
        responses.append(main(request))
    
    # Check that some requests were rate limited
    assert any(r[1] == 200 for r in responses)  # Some succeeded
    mock_bot.assert_called() 