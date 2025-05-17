import os
import pytest
from unittest.mock import patch, MagicMock
import json
from webhook_check_function import main, is_valid_url, send_alert

@pytest.fixture
def mock_env_vars():
    """Set up test environment variables."""
    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["EXPECTED_WEBHOOK_URL"] = "https://test.com/webhook"
    os.environ["ALERT_CHAT_ID"] = "123456"
    yield
    del os.environ["TELEGRAM_TOKEN"]
    del os.environ["EXPECTED_WEBHOOK_URL"]
    del os.environ["ALERT_CHAT_ID"]

def test_is_valid_url():
    """Test URL validation."""
    assert is_valid_url("https://test.com/webhook")
    assert is_valid_url("http://localhost:8080")
    assert not is_valid_url("not_a_url")
    assert not is_valid_url("")
    assert not is_valid_url(None)

@patch("webhook_check_function.requests.post")
def test_send_alert_success(mock_post, mock_env_vars):
    """Test successful alert sending."""
    mock_post.return_value.raise_for_status = MagicMock()
    
    send_alert("test_token", "123456", "Test message")
    
    mock_post.assert_called_once()
    args = mock_post.call_args
    assert args[1]["json"]["chat_id"] == "123456"
    assert "Test message" in args[1]["json"]["text"]

@patch("webhook_check_function.requests.post")
def test_send_alert_failure(mock_post, mock_env_vars):
    """Test alert sending failure."""
    mock_post.side_effect = Exception("Network error")
    
    # Should not raise exception
    send_alert("test_token", "123456", "Test message")
    
    mock_post.assert_called_once()

@patch("webhook_check_function.requests.get")
@patch("webhook_check_function.requests.post")
def test_webhook_check_success(mock_post, mock_get, mock_env_vars):
    """Test successful webhook check."""
    mock_get.return_value.json.return_value = {
        "ok": True,
        "result": {
            "url": "https://different.url/webhook"
        }
    }
    mock_get.return_value.raise_for_status = MagicMock()
    mock_post.return_value.raise_for_status = MagicMock()
    
    request = MagicMock()
    response = main(request)
    
    assert response[1] == 200
    assert response[0]["status"] == "updated"
    mock_get.assert_called_once()
    mock_post.assert_called_once()

@patch("webhook_check_function.requests.get")
def test_webhook_check_already_set(mock_get, mock_env_vars):
    """Test webhook already correctly set."""
    mock_get.return_value.json.return_value = {
        "ok": True,
        "result": {
            "url": "https://test.com/webhook"
        }
    }
    mock_get.return_value.raise_for_status = MagicMock()
    
    request = MagicMock()
    response = main(request)
    
    assert response[1] == 200
    assert response[0]["status"] == "ok"
    mock_get.assert_called_once()

@patch("webhook_check_function.requests.get")
def test_webhook_check_missing_env_vars(mock_get):
    """Test webhook check with missing environment variables."""
    request = MagicMock()
    response = main(request)
    
    assert response[1] == 500
    assert "error" in response[0]
    mock_get.assert_not_called()

@patch("webhook_check_function.requests.get")
def test_webhook_check_invalid_url(mock_get):
    """Test webhook check with invalid URL."""
    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["EXPECTED_WEBHOOK_URL"] = "not_a_url"
    os.environ["ALERT_CHAT_ID"] = "123456"
    
    request = MagicMock()
    response = main(request)
    
    assert response[1] == 500
    assert "Invalid" in response[0]["error"]
    mock_get.assert_not_called()

@patch("webhook_check_function.requests.get")
def test_webhook_check_api_error(mock_get, mock_env_vars):
    """Test webhook check with API error."""
    mock_get.side_effect = Exception("API error")
    
    request = MagicMock()
    response = main(request)
    
    assert response[1] == 500
    assert "error" in response[0]
    mock_get.assert_called_once() 