import os
from unittest.mock import patch, MagicMock
from bot.webhook_check_function import main

@patch("webhook_check_function.requests.get")
@patch("webhook_check_function.requests.post")
def test_main_webhook_check(mock_post, mock_get):
    """Test the main function for webhook check and update."""
    # Mock the environment variables
    os.environ["TELEGRAM_TOKEN"] = "dummy_token"
    os.environ["EXPECTED_WEBHOOK_URL"] = "https://example.com/webhook"
    os.environ["ALERT_CHAT_ID"] = "dummy_chat_id"

    # Mock the response for getWebhookInfo
    mock_get.return_value.json.return_value = {"result": {"url": "https://example.com/old_webhook"}}
    mock_get.return_value.raise_for_status = MagicMock()

    # Mock the response for setWebhook and sendMessage
    mock_post.return_value.raise_for_status = MagicMock()

    # Call the main function
    response, status_code = main(MagicMock())

    # Verify the response
    assert status_code == 200
    assert response["status"] == "updated"
    assert "Webhook successfully updated" in response["message"]

    # There should be two POST calls: setWebhook and sendMessage
    assert mock_post.call_count == 2
    set_webhook_call = mock_post.call_args_list[0]
    send_alert_call = mock_post.call_args_list[1]

    # Check setWebhook call
    assert set_webhook_call[0][0] == "https://api.telegram.org/botdummy_token/setWebhook"
    assert set_webhook_call[1]["json"]["url"] == "https://example.com/webhook"

    # Check sendMessage call
    assert send_alert_call[0][0] == "https://api.telegram.org/botdummy_token/sendMessage"
    assert send_alert_call[1]["data"]["chat_id"] == "dummy_chat_id"
    assert "Webhook successfully updated" in send_alert_call[1]["data"]["text"] 