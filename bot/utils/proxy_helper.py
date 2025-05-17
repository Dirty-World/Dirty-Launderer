# proxy_helper.py
# Loads rotating proxy frontends for services like Nitter, Invidious, Libreddit
# Reads proxies.json and selects a random instance for each service
# Used in each domain handler to dynamically pick live proxy URLs

import json
import random
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Cache for proxies to avoid repeated file reads
_cached_proxies = None

def get_proxy_instance(service, proxies_file="proxies_validated.json"):
    """
    Selects a random proxy instance for the given service.

    Args:
        service (str): The name of the service (e.g., "nitter", "invidious").
        proxies_file (str): The name of the proxies file (default: "proxies_validated.json").

    Returns:
        str: A random proxy URL for the service, or None if no proxies are available.
    """
    global _cached_proxies

    if not isinstance(service, str):
        raise TypeError("Service name must be a string.")

    try:
        # Load proxies from file if not already cached
        if _cached_proxies is None:
            proxies_path = Path(__file__).parent / proxies_file
            if not proxies_path.exists():
                raise FileNotFoundError(f"Proxies file not found: {proxies_path}")
            
            with open(proxies_path, "r") as f:
                proxies = json.load(f)
                if not isinstance(proxies, dict):
                    raise ValueError("Proxies file does not contain a valid JSON object.")
                _cached_proxies = proxies

        # Get candidates for the specified service
        candidates = _cached_proxies.get(service, [])
        if candidates:
            return random.choice(candidates)
        else:
            logging.error(f"No proxies found for service: {service}")
            return None
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logging.error(f"Error processing proxies file: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return None