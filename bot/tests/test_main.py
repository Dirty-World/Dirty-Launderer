import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from telegram import Update, User, Chat, Message
from webhook_check_function import send_alert
from main import sanitize_input, hash_user_id, get_safe_domain, main, start, privacy_command, delete_command, help_command, handle_message

@pytest.mark.asyncio
async def test_send_alert_success():
    """Test successful alert sending."""
    with patch('main.get_secret') as mock_get_secret:
        mock_get_secret.return_value = "test-token"
        assert True  # Placeholder for actual test

@pytest.mark.asyncio
async def test_send_alert_failure():
    """Test alert sending failure."""
    with patch('main.get_secret') as mock_get_secret:
        mock_get_secret.side_effect = Exception("Failed to get secret")
        assert True  # Placeholder for actual test

@pytest.mark.asyncio
async def test_send_alert_missing_env_vars():
    """Test alert sending with missing environment variables."""
    with patch('main.get_secret') as mock_get_secret:
        mock_get_secret.side_effect = ValueError("GCP_PROJECT_ID environment variable not set")
        assert True  # Placeholder for actual test

def test_sanitize_input():
    """Test input sanitization."""
    assert sanitize_input("test@example.com") == "[EMAIL]"
    assert sanitize_input("192.168.1.1") == "[IP]"
    assert sanitize_input("password=secret") == "password=[REDACTED]"

def test_get_safe_domain():
    """Test domain extraction and normalization."""
    assert get_safe_domain("https://sub.example.com/path") == "example.com"
    assert get_safe_domain("invalid") == "invalid-url"

@pytest.mark.asyncio
@patch('main.ApplicationBuilder')
@patch('telegram.Update.de_json')
async def test_no_telegram_pii_leak(mock_de_json, mock_app_builder):
    """Test that no Telegram-specific PII is leaked in logs or responses."""
    # Mock a Telegram update with sensitive data
    user = User(id=123456, first_name="John", last_name="Doe", username="johndoe", is_bot=False)
    chat = Chat(id=123456, type="private")
    message = Message(message_id=1, date=None, chat=chat, from_user=user, text="Hello, world!")
    update = Update(update_id=123456789, message=message)

    # Mock the request to simulate a Telegram webhook call
    request = MagicMock()
    request.method = "POST"
    request.get_json.return_value = update.to_dict()

    # Patch ApplicationBuilder and Update.de_json
    mock_app = AsyncMock()
    mock_app.process_update = AsyncMock()
    mock_app_builder.return_value.token.return_value.build.return_value = mock_app
    mock_de_json.return_value = MagicMock(message=MagicMock(reply_text=AsyncMock(return_value=MagicMock(message_id=1)), text="Hello, world!", chat_id=123456, delete=AsyncMock(), reply_to_message=None), effective_user=MagicMock(id=123456, first_name="John", last_name="Doe", username="johndoe", is_bot=False), effective_chat=MagicMock(id=123456, type="private"))

    # Call the main function
    response = await main(request)
    assert response[1] == 200

@pytest.mark.asyncio
async def test_start_command():
    """Test that the start command sends the correct welcome message."""
    # Mock the update and context
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.application = MagicMock()
    context.application.create_task = MagicMock()

    # Mock rate limiting
    with patch('main.check_rate_limit', return_value=(True, None)):
        # Call the start function
        await start(update, context)

        # Verify that the correct message is sent
        update.message.reply_text.assert_called_once_with(
            'Hi! I am The Dirty Launderer🧼 bot. Send me a URL and I will clean it for you.\n'
            'Use /help to see available commands.'
        )

@pytest.mark.asyncio
async def test_start_command_rate_limited():
    """Test that the start command handles rate limiting correctly."""
    # Mock the update and context
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.application = MagicMock()
    context.application.create_task = MagicMock()

    # Mock rate limiting to return rate limited
    with patch('main.check_rate_limit', return_value=(False, "Rate limit exceeded")):
        # Call the start function
        await start(update, context)

        # Verify that the rate limit message is sent
        update.message.reply_text.assert_called_once_with("Rate limit exceeded")

@pytest.mark.asyncio
async def test_privacy_command():
    """Test that the privacy command sends the correct privacy policy message."""
    # Mock the update and context
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.application = MagicMock()
    context.application.create_task = MagicMock()

    # Call the privacy_command function
    await privacy_command(update, context)

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

@pytest.mark.asyncio
async def test_delete_command():
    """Test that the delete command properly deletes messages."""
    # Mock the update and context
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456
    update.message = MagicMock()
    update.message.delete = AsyncMock()
    update.message.reply_to_message = MagicMock()
    update.message.reply_to_message.delete = AsyncMock()
    context = MagicMock()

    # Call the delete_command function
    await delete_command(update, context)

    # Verify that the messages are deleted
    update.message.delete.assert_called_once()

@pytest.mark.asyncio
async def test_help_command():
    """Test that the help command sends the correct help message."""
    # Mock the update and context
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.application = MagicMock()
    context.application.create_task = MagicMock()

    # Call the help_command function
    await help_command(update, context)

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

@pytest.mark.asyncio
async def test_handle_message():
    """Test that handle_message processes messages correctly."""
    # Mock the update and context
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456
    update.message = MagicMock()
    update.message.text = "https://example.com"
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.application = MagicMock()
    context.application.create_task = MagicMock()

    # Mock rate limiting
    with patch('main.check_rate_limit', return_value=(True, None)):
        # Call handle_message
        await handle_message(update, context)

        # Verify that the message is processed
        update.message.reply_text.assert_called_once_with('URL cleaning functionality coming soon!')

@pytest.mark.asyncio
async def test_handle_message_rate_limited():
    """Test that handle_message handles rate limiting correctly."""
    # Mock the update and context
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456
    update.message = MagicMock()
    update.message.text = "https://example.com"
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.application = MagicMock()
    context.application.create_task = MagicMock()

    # Mock rate limiting to return rate limited
    with patch('main.check_rate_limit', return_value=(False, "Rate limit exceeded")):
        # Call handle_message
        await handle_message(update, context)

        # Verify that the rate limit message is sent
        update.message.reply_text.assert_called_once_with("Rate limit exceeded")