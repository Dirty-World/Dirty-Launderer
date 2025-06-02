import os
import requests
from unittest.mock import patch, MagicMock
from webhook_check_function import (
    is_valid_url,
    get_current_webhook,
    set_webhook,
    send_alert,
    main
)

def test_url_validation():
    """Test URL validation functionality."""
    print("\nTesting URL validation...")
    
    # Test valid URLs
    valid_urls = [
        "https://example.com",
        "https://sub.example.com/path",
        "http://localhost:8080",
        "https://api.telegram.org/bot123/setWebhook"
    ]
    
    # Test invalid URLs
    invalid_urls = [
        "not-a-url",
        "ftp://",
        "http://",
        "",
        None
    ]
    
    # Test valid URLs
    for url in valid_urls:
        assert is_valid_url(url), f"URL should be valid: {url}"
        print(f"✓ Valid URL test passed: {url}")
    
    # Test invalid URLs
    for url in invalid_urls:
        assert not is_valid_url(url), f"URL should be invalid: {url}"
        print(f"✓ Invalid URL test passed: {url}")

def test_webhook_functions():
    """Test webhook-related functions with mocked requests."""
    print("\nTesting webhook functions...")
    
    # Mock response for getWebhookInfo
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {
        "ok": True,
        "result": {
            "url": "https://example.com/webhook"
        }
    }
    mock_get_response.raise_for_status = MagicMock()
    
    # Mock response for setWebhook
    mock_set_response = MagicMock()
    mock_set_response.raise_for_status = MagicMock()
    
    # Create mock requests
    mock_requests = MagicMock()
    mock_requests.get.return_value = mock_get_response
    mock_requests.post.return_value = mock_set_response
    
    # Test get_current_webhook
    with patch('webhook_check_function.requests', mock_requests):
        current_url = get_current_webhook("test-token", mock_requests)
        assert current_url == "https://example.com/webhook"
        print("✓ get_current_webhook test passed")
    
    # Test set_webhook
    with patch('webhook_check_function.requests', mock_requests):
        set_webhook("test-token", "https://new-url.com/webhook", mock_requests)
        print("✓ set_webhook test passed")

def test_main_function():
    """Test the main function with mocked dependencies."""
    print("\nTesting main function...")
    
    # Mock environment variables
    mock_env = {
        'TELEGRAM_TOKEN': 'test-token',
        'EXPECTED_WEBHOOK_URL': 'https://example.com/webhook',
        'ALERT_CHAT_ID': '123456'
    }
    
    # Mock requests
    mock_requests = MagicMock()
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {
        "ok": True,
        "result": {
            "url": "https://example.com/webhook"
        }
    }
    mock_get_response.raise_for_status = MagicMock()
    mock_requests.get.return_value = mock_get_response
    
    # Test main function
    with patch('webhook_check_function.requests', mock_requests):
        response, status_code = main(MagicMock(), env=mock_env, requests_mod=mock_requests)
        assert status_code == 200
        assert response["status"] == "ok"
        print("✓ main function test passed")

if __name__ == "__main__":
    print("Starting webhook check tests...")
    
    # Run tests
    test_url_validation()
    test_webhook_functions()
    test_main_function()
    
    print("\nAll webhook check tests completed successfully!") 