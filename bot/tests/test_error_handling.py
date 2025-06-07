import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes, Application
from main import (
    get_telegram_token,
    get_safe_domain,
    check_rate_limit,
    delete_message_after_delay,
    process_update,
    main
)
from utils.rate_limiter import check_rate_limit

@pytest.mark.asyncio
async def test_get_telegram_token_error():
    """Test error handling in get_telegram_token."""
    with patch('main.get_secret', side_effect=Exception("Secret not found")):
        with pytest.raises(Exception):
            get_telegram_token()

@pytest.mark.asyncio
async def test_get_telegram_token_empty():
    """Test handling of empty token."""
    with patch('main.get_secret', return_value=None):
        with pytest.raises(EnvironmentError):
            get_telegram_token()

def test_get_safe_domain_invalid_inputs():
    """Test get_safe_domain with invalid inputs."""
    assert get_safe_domain(None) == 'invalid-url'
    assert get_safe_domain('') == 'invalid-url'
    assert get_safe_domain('not-a-url') == 'invalid-url'

def test_check_rate_limit_edge_cases():
    """Test rate limit edge cases."""
    # Test empty user hash
    result, message = check_rate_limit('')
    assert result is True
    assert message is None

    # Test None user hash
    result, message = check_rate_limit(None)
    assert result is True
    assert message is None

@pytest.mark.asyncio
async def test_delete_message_error():
    """Test error handling in delete_message_after_delay."""
    # Create a mock bot with an async delete_message method
    mock_bot = AsyncMock()
    mock_bot.delete_message.side_effect = Exception("Delete failed")
    
    # Create a mock context with the bot
    mock_context = MagicMock()
    mock_context.bot = mock_bot
    
    # Mock asyncio.sleep to avoid actual delay
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        # The function should not raise an exception
        await delete_message_after_delay(mock_context, 123, 456)
        
        # Verify sleep was called with correct duration
        mock_sleep.assert_called_once_with(300)
        
        # Verify delete_message was called
        mock_bot.delete_message.assert_called_once_with(chat_id=123, message_id=456)

@pytest.mark.asyncio
async def test_process_update_error():
    """Test error handling in process_update."""
    with patch('main.ApplicationBuilder') as mock_builder:
        mock_builder.return_value.token.return_value.build.side_effect = Exception("Build failed")
        with pytest.raises(Exception):
            await process_update({})

@pytest.mark.asyncio
async def test_main_invalid_method():
    """Test main function with invalid HTTP method."""
    mock_request = MagicMock()
    mock_request.method = "GET"
    
    response, status_code = await main(mock_request)
    assert status_code == 405
    assert response == 'Only POST requests are accepted'

@pytest.mark.asyncio
async def test_main_invalid_json():
    """Test main function with invalid JSON."""
    mock_request = MagicMock()
    mock_request.method = "POST"
    mock_request.get_json.side_effect = Exception("Invalid JSON")
    
    response, status_code = await main(mock_request)
    assert status_code == 400
    assert response == {'error': 'BadRequest'}

@pytest.mark.asyncio
async def test_command_handlers_error_handling():
    """Test error handling in command handlers."""
    # Create a mock update
    mock_update = MagicMock(spec=Update)
    mock_update.message = MagicMock(spec=Message)
    mock_update.message.chat_id = 123
    mock_update.message.message_id = 456
    mock_update.message.text = "test message"  # Set the text attribute
    mock_update.effective_user = MagicMock(spec=User)
    mock_update.effective_user.id = 789
    
    # Create a mock context with application
    mock_context = MagicMock()
    mock_context.bot = AsyncMock()
    mock_context.application = MagicMock()
    mock_context.application.create_task = MagicMock()
    mock_context.bot.send_message.side_effect = Exception("Send failed")
    
    # Test that handlers don't raise exceptions
    from main import start, help_command, privacy_command, delete_command, handle_message
    
    await start(mock_update, mock_context)
    await help_command(mock_update, mock_context)
    await privacy_command(mock_update, mock_context)
    await delete_command(mock_update, mock_context)
    await handle_message(mock_update, mock_context) 