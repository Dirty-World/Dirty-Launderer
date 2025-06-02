import os
from unittest.mock import patch, MagicMock
from bot.webhook_check_function import main

@patch("bot.webhook_check_function.requests.get")
@patch("bot.webhook_check_function.requests.post")
def test_main_webhook_check(mock_post, mock_get):
    """Test main webhook check function."""
    # Mock the getWebhookInfo response
    mock_get.return_value.json.return_value = {
        "ok": True,
        "result": {"url": "https://different.url/webhook"}
    }
    mock_get.return_value.raise_for_status = MagicMock()

    # Mock the setWebhook response
    mock_post.return_value.json.return_value = {"ok": True}
    mock_post.return_value.raise_for_status = MagicMock()

    # Set up environment variables
    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["EXPECTED_WEBHOOK_URL"] = "https://test.com/webhook"

    # Create a mock request
    request = MagicMock()

    # Call the function
    response = main(request)

    # Verify the response
    assert response[1] == 200
    assert "status" in response[0]

    # Verify the API calls
    mock_get.assert_called_once()
    mock_post.assert_called_once() 