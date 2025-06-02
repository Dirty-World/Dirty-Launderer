import os
import pytest
from unittest.mock import patch, MagicMock
import json
from bot.webhook_check_function import main, is_valid_url, send_alert

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

@pytest.fixture
def mock_secret_manager():
    """Mock the Secret Manager to return a dummy token."""
    with patch('bot.webhook_check_function.get_secret') as mock_get_secret:
        mock_get_secret.return_value = "dummy_token"
        yield mock_get_secret

def test_is_valid_url():
    """Test URL validation."""
    assert is_valid_url("https://example.com")
    assert not is_valid_url("not_a_url")
    assert not is_valid_url("")

@patch("bot.webhook_check_function.requests.post")
def test_send_alert_success(mock_post):
    """Test successful alert sending."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = MagicMock()
    os.environ["TELEGRAM_TOKEN"] = "dummy_token"
    os.environ["ALERT_CHAT_ID"] = "dummy_chat_id"

    send_alert("Test message")
    mock_post.assert_called_once()

@patch("bot.webhook_check_function.requests.post")
def test_send_alert_failure(mock_post):
    """Test alert sending failure."""
    mock_post.side_effect = Exception("Network error")
    os.environ["TELEGRAM_TOKEN"] = "dummy_token"
    os.environ["ALERT_CHAT_ID"] = "dummy_chat_id"

    send_alert("Test message")
    mock_post.assert_called_once()

@patch("bot.webhook_check_function.requests.get")
@patch("bot.webhook_check_function.requests.post")
def test_webhook_check_success(mock_post, mock_get):
    """Test successful webhook check."""
    mock_get.return_value.json.return_value = {
        "ok": True,
        "result": {"url": "https://test.com/webhook"}
    }
    mock_get.return_value.raise_for_status = MagicMock()
    mock_post.return_value.json.return_value = {"ok": True}
    mock_post.return_value.raise_for_status = MagicMock()

    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["EXPECTED_WEBHOOK_URL"] = "https://test.com/webhook"

    request = MagicMock()
    response = main(request)
    assert response[1] == 200
    assert "status" in response[0]

@patch("bot.webhook_check_function.requests.get")
@patch("bot.webhook_check_function.requests.post")
def test_webhook_check_already_set(mock_post, mock_get):
    """Test webhook check when URL is already set."""
    mock_get.return_value.json.return_value = {
        "ok": True,
        "result": {"url": "https://test.com/webhook"}
    }
    mock_get.return_value.raise_for_status = MagicMock()

    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["EXPECTED_WEBHOOK_URL"] = "https://test.com/webhook"

    request = MagicMock()
    response = main(request)
    assert response[1] == 200
    assert "status" in response[0]
    mock_post.assert_not_called()

@patch("bot.webhook_check_function.requests.get")
def test_webhook_check_missing_env_vars(mock_get):
    """Test webhook check with missing environment variables."""
    if "TELEGRAM_TOKEN" in os.environ:
        del os.environ["TELEGRAM_TOKEN"]
    if "EXPECTED_WEBHOOK_URL" in os.environ:
        del os.environ["EXPECTED_WEBHOOK_URL"]

    request = MagicMock()
    response = main(request)
    assert response[1] == 500
    assert "error" in response[0]
    mock_get.assert_not_called()

@patch("bot.webhook_check_function.requests.get")
def test_webhook_check_invalid_url(mock_get):
    """Test webhook check with invalid URL."""
    mock_get.return_value.json.return_value = {
        "ok": True,
        "result": {"url": "invalid_url"}
    }
    mock_get.return_value.raise_for_status = MagicMock()

    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["EXPECTED_WEBHOOK_URL"] = "invalid_url"

    request = MagicMock()
    response = main(request)
    assert response[1] == 500
    assert "error" in response[0]
    assert "Invalid EXPECTED_WEBHOOK_URL format" in response[0]["error"]

@patch("bot.webhook_check_function.requests.get")
def test_webhook_check_api_error(mock_get):
    """Test webhook check with API error."""
    mock_get.side_effect = Exception("API Error")
    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["EXPECTED_WEBHOOK_URL"] = "https://test.com/webhook"

    request = MagicMock()
    response = main(request)
    assert response[1] == 500
    assert "error" in response[0] 