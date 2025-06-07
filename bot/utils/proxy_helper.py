# proxy_helper.py
# Loads rotating proxy frontends for services like Nitter, Invidious, Libreddit
# Uses Firestore to store and retrieve proxy configurations
# Used in each domain handler to dynamically pick live proxy URLs

import random
import logging
from .firestore import get_proxy_config

# Configure logging
logging.basicConfig(level=logging.ERROR)

def get_proxy_instance(service: str) -> str:
    """
    Selects a random proxy instance for the given service.

    Args:
        service (str): The name of the service (e.g., "nitter", "invidious").

    Returns:
        str: A random proxy URL for the service, or None if no proxies are available.
    """
    if not isinstance(service, str):
        raise TypeError("Service name must be a string.")

    try:
        # Get proxies from Firestore
        proxies = get_proxy_config()
        
        # Get candidates for the specified service
        candidates = proxies.get(service, [])
        if candidates:
            return random.choice(candidates)
        else:
            logging.error(f"No proxies found for service: {service}")
            return None
    except Exception as e:
        logging.error(f"Error getting proxy instance: {e}")
        return None