import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Rate limiting
RATE_LIMIT = 10  # requests per minute
rate_limit_store = defaultdict(list)

def check_rate_limit(user_hash):
    """Check if user has exceeded rate limit."""
    current_time = time.time()
    user_requests = rate_limit_store[user_hash]
    user_requests = [t for t in user_requests if current_time - t < 60]
    rate_limit_store[user_hash] = user_requests
    
    if len(user_requests) >= RATE_LIMIT:
        logger.warning(f"Rate limit exceeded for user {user_hash}")
        return False, "Rate limit exceeded. Please try again in a minute."
    
    user_requests.append(current_time)
    return True, None

def cleanup_session():
    """Ensure no user data persists between requests."""
    # Clear rate limiting data older than 1 minute
    current_time = time.time()
    for user_hash in list(rate_limit_store.keys()):
        rate_limit_store[user_hash] = [t for t in rate_limit_store[user_hash] if current_time - t < 60]
        if not rate_limit_store[user_hash]:
            del rate_limit_store[user_hash] 