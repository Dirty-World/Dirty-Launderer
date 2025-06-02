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
    os.environ["ALERT_CHAT_ID"] = "dummy_chat_id"  # Added for alert message

    # Create a mock request
    request = MagicMock()

    # Call the function
    response = main(request)

    # Verify the response
    assert response[1] == 200
    assert "status" in response[0]
    assert response[0]["status"] == "updated"

    # Verify the API calls
    mock_get.assert_called_once()
    assert mock_post.call_count == 2  # Expect two calls: setWebhook and sendMessage

    # Verify first call is for setWebhook
    mock_post.assert_any_call(
        'https://api.telegram.org/bottest_token/setWebhook',
        json={'url': 'https://test.com/webhook', 'allowed_updates': ['message', 'callback_query'], 'max_connections': 100},
        timeout=10
    )

    # Verify second call is for sendMessage
    mock_post.assert_any_call(
        'https://api.telegram.org/bottest_token/sendMessage',
        data={'chat_id': 'dummy_chat_id', 'text': '[The Dirty Launderer Webhook] Webhook successfully updated to: https://test.com/webhook'},
        timeout=10
    ) 