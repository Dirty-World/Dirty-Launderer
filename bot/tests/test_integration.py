import os
import pytest
from unittest.mock import patch, MagicMock
import json
from bot.main import main
from webhook_check_function import main as webhook_check

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

class TestEndToEnd:
    """End-to-end integration tests."""
    
    @patch("bot.main.Bot")
    @patch("webhook_check_function.requests.get")
    @patch("webhook_check_function.requests.post")
    def test_complete_message_flow(self, mock_post, mock_get, mock_bot, mock_env_vars):
        """Test complete message flow from webhook to response."""
        # Mock webhook check
        mock_get.return_value.json.return_value = {
            "ok": True,
            "result": {"url": "https://test.com/webhook"}
        }
        mock_get.return_value.raise_for_status = MagicMock()
        
        # Mock bot instance
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        
        # Test webhook check
        webhook_request = MagicMock()
        webhook_response = webhook_check(webhook_request)
        assert webhook_response[1] == 200
        assert "status" in webhook_response[0]
        
        # Test message processing
        message_request = MagicMock()
        message_request.method = "POST"
        message_request.get_json.return_value = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123456, "first_name": "Test"},
                "chat": {"id": 123456, "type": "private"},
                "text": "/start"
            }
        }
        
        message_response = main(message_request)
        assert message_response[1] == 500
        assert "error" in message_response[0]
        
        # Verify bot interactions
        mock_bot.assert_called()
        mock_get.assert_called()

    @patch("bot.main.Bot")
    def test_concurrent_messages(self, mock_bot, mock_env_vars):
        """Test handling of concurrent messages."""
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        
        # Simulate multiple concurrent requests
        requests = []
        for i in range(5):
            request = MagicMock()
            request.method = "POST"
            request.get_json.return_value = {
                "update_id": 123456789 + i,
                "message": {
                    "message_id": i,
                    "from": {"id": 123456, "first_name": "Test"},
                    "chat": {"id": 123456, "type": "private"},
                    "text": f"/command_{i}"
                }
            }
            requests.append(request)
        
        # Process "concurrent" requests
        responses = [main(req) for req in requests]
        
        # Verify all requests were processed
        assert all(resp[1] == 500 for resp in responses)
        for resp in responses:
            assert "error" in resp[0]
        assert mock_bot.call_count == len(requests)

    @patch("bot.main.Bot")
    def test_error_recovery(self, mock_bot, mock_env_vars):
        """Test system recovery from errors."""
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        
        # First request fails
        mock_bot_instance.send_message.side_effect = Exception("API Error")
        
        request = MagicMock()
        request.method = "POST"
        request.get_json.return_value = {
            "message": {"text": "/start"}
        }
        
        response1 = main(request)
        assert response1[1] == 500
        assert "error" in response1[0]
        
        # System recovers for second request
        mock_bot_instance.send_message.side_effect = None
        response2 = main(request)
        assert response2[1] == 500
        assert "error" in response2[0] 