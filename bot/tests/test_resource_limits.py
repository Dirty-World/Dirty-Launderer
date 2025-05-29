import os
import pytest
from unittest.mock import patch, MagicMock
import json
from bot.main import main

# Google Cloud Free Tier Limits (2024)
FREE_TIER_LIMITS = {
    'FUNCTION_CALLS': 2_000_000,  # 2M invocations per month
    'FUNCTION_MEMORY': 256,       # 256MB memory
    'FUNCTION_TIMEOUT': 60,       # 60 seconds max timeout
    'EGRESS_BANDWIDTH': 5,        # 5GB per month
    'SECRET_ACCESS': 10_000       # 10K secret accesses per month
}

class TestResourceLimits:
    """Tests to ensure the bot stays within Google Cloud free tier."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Set up test environment variables."""
        os.environ["TELEGRAM_TOKEN"] = "test_token"
        yield
        del os.environ["TELEGRAM_TOKEN"]

    def test_memory_usage(self, mock_env_vars):
        """Test that memory usage stays under free tier limit."""
        import psutil
        import os
        
        # Process a typical message
        request = MagicMock()
        request.method = "POST"
        request.get_json.return_value = {
            "message": {
                "text": "/start",
                "chat": {"id": 123456}
            }
        }
        
        # Measure memory before and after
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # Convert to MB
        
        main(request)
        
        mem_after = process.memory_info().rss / 1024 / 1024
        mem_used = mem_after - mem_before
        
        assert mem_used < FREE_TIER_LIMITS['FUNCTION_MEMORY'], f"Memory usage ({mem_used}MB) exceeds free tier limit ({FREE_TIER_LIMITS['FUNCTION_MEMORY']}MB)"

    def test_response_time(self, mock_env_vars):
        """Test that response time is well under the timeout limit."""
        import time
        
        request = MagicMock()
        request.method = "POST"
        request.get_json.return_value = {
            "message": {
                "text": "/start",
                "chat": {"id": 123456}
            }
        }
        
        start_time = time.time()
        main(request)
        execution_time = time.time() - start_time
        
        # Should complete well under the 60s limit (using 10s as a safe threshold)
        assert execution_time < 10, f"Response time ({execution_time}s) is too close to free tier timeout limit"

    @patch('main.Bot')
    def test_network_usage(self, mock_bot, mock_env_vars):
        """Test that network usage per request is reasonable."""
        from urllib.parse import urlparse
        import sys
        
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        
        # Track outgoing data size
        outgoing_data = []
        def track_size(*args, **kwargs):
            # Roughly estimate size of outgoing data
            data_size = sys.getsizeof(str(args) + str(kwargs))
            outgoing_data.append(data_size)
            return MagicMock()
            
        mock_bot_instance.send_message.side_effect = track_size
        
        # Process a message
        request = MagicMock()
        request.method = "POST"
        request.get_json.return_value = {
            "message": {
                "text": "/start",
                "chat": {"id": 123456}
            }
        }
        
        main(request)
        
        total_bytes = sum(outgoing_data)
        kb_per_request = total_bytes / 1024
        
        # Assuming 1000 requests per day, ensure we stay under 5GB monthly limit
        daily_kb = kb_per_request * 1000
        monthly_gb = (daily_kb * 30) / (1024 * 1024)
        
        assert monthly_gb < FREE_TIER_LIMITS['EGRESS_BANDWIDTH'], f"Projected monthly bandwidth ({monthly_gb}GB) exceeds free tier limit"

    @patch('main.Bot')
    def test_secret_access_rate(self, mock_bot, mock_env_vars):
        """Test that secret access rate stays within limits."""
        secret_accesses = []
        
        def track_secret_access(*args, **kwargs):
            secret_accesses.append(1)
            return MagicMock()
            
        mock_bot.side_effect = track_secret_access
        
        # Process multiple messages
        for _ in range(10):
            request = MagicMock()
            request.method = "POST"
            request.get_json.return_value = {
                "message": {
                    "text": "/start",
                    "chat": {"id": 123456}
                }
            }
            main(request)
        
        # Check secret access count
        accesses_per_request = len(secret_accesses) / 10
        daily_accesses = accesses_per_request * 1000  # Assuming 1000 requests per day
        monthly_accesses = daily_accesses * 30
        
        assert monthly_accesses < FREE_TIER_LIMITS['SECRET_ACCESS'], f"Projected monthly secret accesses ({monthly_accesses}) exceeds free tier limit"

    def test_function_size(self):
        """Test that function deployment package stays small."""
        import os
        from pathlib import Path
        
        # Get size of bot directory
        bot_dir = Path(__file__).parent.parent
        total_size = 0
        for path in bot_dir.rglob('*'):
            if path.is_file() and not any(part.startswith('.') for part in path.parts):
                total_size += path.stat().st_size
        
        size_mb = total_size / (1024 * 1024)
        # Cloud Functions has a 100MB limit, but we should stay well under
        assert size_mb < 50, f"Function size ({size_mb}MB) is too large for efficient deployment" 