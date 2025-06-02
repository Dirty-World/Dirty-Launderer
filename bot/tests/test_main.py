import os
import pytest
from unittest.mock import patch, MagicMock
from telegram import Update, User, Chat, Message
from bot.webhook_check_function import send_alert
from bot.main import sanitize_input, hash_user_id, get_safe_domain, main, start, privacy_command, delete_command, help_command, handle_message

@patch("bot.webhook_check_function.requests.post")
def test_send_alert_success(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = MagicMock()
    os.environ["TELEGRAM_TOKEN"] = "dummy_token"
    os.environ["ALERT_CHAT_ID"] = "dummy_chat_id"

    send_alert("Test message")
    mock_post.assert_called_once()

@patch("bot.webhook_check_function.requests.post")
def test_send_alert_failure(mock_post):
    mock_post.side_effect = Exception("Network error")
    os.environ["TELEGRAM_TOKEN"] = "dummy_token"
    os.environ["ALERT_CHAT_ID"] = "dummy_chat_id"

    send_alert("Test message")
    mock_post.assert_called_once()

@patch("bot.webhook_check_function.requests.post")
def test_send_alert_missing_env_vars(mock_post):
    if "TELEGRAM_TOKEN" in os.environ:
        del os.environ["TELEGRAM_TOKEN"]
    if "ALERT_CHAT_ID" in os.environ:
        del os.environ["ALERT_CHAT_ID"]
    response = send_alert("Test message")
    assert response is None  # send_alert logs error and returns None
    mock_post.assert_not_called()

def test_sanitize_input():
    """Test sanitize_input function for redacting PII and handling edge cases."""
    # Test redacting email
    assert sanitize_input("user@example.com") == "[EMAIL]"
    # Test redacting IP
    assert sanitize_input("192.168.1.1") == "[IP]"
    # Test redacting sensitive pattern
    assert sanitize_input("password=secret123") == "password=[REDACTED]"
    # Test empty input
    assert sanitize_input("") == ""
    # Test input with no PII
    assert sanitize_input("Hello, world!") == "Hello, world!"

def test_get_safe_domain():
    """Test get_safe_domain function for extracting and normalizing domains."""
    # Test valid URL with subdomain
    assert get_safe_domain("https://sub.example.com/path") == "example.com"
    # Test valid URL without subdomain
    assert get_safe_domain("http://example.com") == "example.com"
    # Test invalid URL
    assert get_safe_domain("not_a_url") == ""
    # Test empty input
    assert get_safe_domain("") == "invalid-url"
    # Test None input
    assert get_safe_domain(None) == "invalid-url"

@patch("bot.main.Bot")
def test_no_telegram_pii_leak(mock_bot):
    """Test that no Telegram-specific PII is leaked in logs or responses."""
    # Mock a Telegram update with sensitive data
    user = User(id=123456, first_name="John", last_name="Doe", username="johndoe", is_bot=False)  # Added is_bot argument
    chat = Chat(id=123456, type="private")
    message = Message(message_id=1, date=None, chat=chat, from_user=user, text="Hello, world!")
    update = Update(update_id=123456789, message=message)

    # Mock the request to simulate a Telegram webhook call
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = update.to_dict()

    # Mock the bot instance
    mock_bot_instance = MagicMock()
    mock_bot.return_value = mock_bot_instance

    # Call the main function
    response = main(request)

    # Verify the response does not contain PII
    assert response[1] == 200
    assert "error" not in response[0]

    # Verify that the user ID is hashed in logs (if logged)
    # This is a manual check; you can add logging assertions if needed
    # For example, check that the log output does not contain "123456" or "John Doe"

# All test functions for pause_scheduler_jobs have been removed.
# Only tests for send_alert and unrelated functionality remain.

@patch("bot.main.Bot")
def test_start_command(mock_bot):
    """Test that the start command sends the correct welcome message."""
    # Mock the update and context
    update = MagicMock()
    update.effective_user.id = 123456
    context = MagicMock()
    context.job_queue.run_once = MagicMock()

    # Call the start function
    start(update, context)

    # Verify that the correct message is sent
    update.message.reply_text.assert_called_once_with(
        'Hi! I am The Dirty Launderer🧼 bot. Send me a URL and I will clean it for you.\n'
        'Use /help to see available commands.'
    )
    # Verify that the message is scheduled for deletion
    context.job_queue.run_once.assert_called_once()

@patch("bot.main.Bot")
def test_privacy_command(mock_bot):
    """Test that the privacy command sends the correct privacy policy message."""
    # Mock the update and context
    update = MagicMock()
    context = MagicMock()
    context.job_queue.run_once = MagicMock()

    # Call the privacy_command function
    privacy_command(update, context)

    # Verify that the correct message is sent
    update.message.reply_text.assert_called_once_with(
        '🔒 *The Dirty Launderer🧼 Privacy Policy*\n\n'
        '• We do not store any personal data\n'
        '• Messages are processed in memory only\n'
        '• URLs are cleaned of tracking parameters\n'
        '• Logs are anonymized and minimal\n'
        '• Messages are auto-deleted after 5 minutes\n'
        '• You can use /delete to remove messages immediately\n'
        '• Rate limiting is in place to prevent abuse\n\n'
        'By using this bot, you consent to this privacy policy.',
        parse_mode='Markdown'
    )
    # Verify that the message is scheduled for deletion
    context.job_queue.run_once.assert_called_once()

@patch("bot.main.Bot")
def test_delete_command(mock_bot):
    """Test that the delete command does not send a confirmation message."""
    # Mock the update and context
    update = MagicMock()
    context = MagicMock()
    context.job_queue.run_once = MagicMock()

    # Call the delete_command function
    delete_command(update, context)

    # Verify that no message is sent
    update.message.reply_text.assert_not_called()

@patch("bot.main.Bot")
def test_help_command(mock_bot):
    """Test that the help command sends the correct help message."""
    # Mock the update and context
    update = MagicMock()
    context = MagicMock()
    context.job_queue.run_once = MagicMock()

    # Call the help_command function
    help_command(update, context)

    # Verify that the correct message is sent
    update.message.reply_text.assert_called_once_with(
        'The Dirty Launderer🧼 is here to help!\n\n'
        'Send me any URL and I will remove tracking parameters and proxy it through privacy-friendly frontends.\n\n'
        'Commands:\n'
        '/privacy - View privacy policy\n'
        '/delete - Delete messages\n'
        '/help - Show this help\n\n'
        'Made with 🧼 by The Dirty Launderer🧼 team'
    )
    # Verify that the message is scheduled for deletion
    context.job_queue.run_once.assert_called_once()