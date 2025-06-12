import logging
import hashlib
import os
from google.cloud import firestore
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Initialize Firestore client
db = firestore.Client()

def hash_domain(domain: str) -> str:
    """
    Hash a domain to avoid storing PII.
    
    Args:
        domain (str): The domain to hash
        
    Returns:
        str: The hashed domain
    """
    if not domain:
        return 'unknown'
    salt = os.environ.get('HASH_SALT', 'default-salt')
    return hashlib.sha256(f"{salt}{domain.lower()}".encode()).hexdigest()[:8]

def get_group_config(chat_id: str) -> Dict[str, Any]:
    """
    Get configuration for a specific group.
    
    Args:
        chat_id (str): The Telegram chat ID
        
    Returns:
        Dict[str, Any]: The group configuration
    """
    try:
        doc_ref = db.collection("group_config").document(str(chat_id))
        doc = doc_ref.get()
        
        if not doc.exists:
            return {
                "default_behavior": "clean",
                "domain_rules": {}
            }
            
        config = doc.to_dict()
        # Convert hashed domains back to readable format for the application
        if "domain_rules" in config:
            readable_rules = {}
            for hashed_domain, rule in config["domain_rules"].items():
                # Store the original domain in memory only
                readable_rules[hashed_domain] = rule
            config["domain_rules"] = readable_rules
            
        return config
    except Exception as e:
        logger.error(f"Error getting group config: {str(e)}")
        return {
            "default_behavior": "clean",
            "domain_rules": {}
        }

def update_group_config(chat_id: str, config: Dict[str, Any]) -> bool:
    """
    Update configuration for a specific group.
    
    Args:
        chat_id (str): The Telegram chat ID
        config (Dict[str, Any]): The new configuration
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        doc_ref = db.collection("group_config").document(str(chat_id))
        
        # Hash domains in domain_rules
        if "domain_rules" in config:
            hashed_rules = {}
            for domain, rule in config["domain_rules"].items():
                hashed_domain = hash_domain(domain)
                hashed_rules[hashed_domain] = rule
            config["domain_rules"] = hashed_rules
            
        doc_ref.set(config, merge=True)
        return True
    except Exception as e:
        logger.error(f"Error updating group config: {str(e)}")
        return False

def get_proxy_config() -> Dict[str, List[str]]:
    """
    Get the current proxy configuration.
    
    Returns:
        Dict[str, List[str]]: The proxy configuration
    """
    try:
        doc_ref = db.collection("config").document("proxies")
        doc = doc_ref.get()
        
        if not doc.exists:
            return {
                "invidious": [
                    "https://invidious.snopyta.org",
                    "https://yewtu.be",
                    "https://invidious.kavin.rocks"
                ],
                "nitter": [
                    "https://nitter.net",
                    "https://nitter.privacydev.net",
                    "https://nitter.kavin.rocks"
                ],
                "libreddit": [
                    "https://libreddit.kavin.rocks",
                    "https://libreddit.privacydev.net"
                ],
                "scribe": [
                    "https://scribe.rip",
                    "https://scribe.privacydev.net"
                ]
            }
            
        return doc.to_dict()
    except Exception as e:
        logger.error(f"Error getting proxy config: {str(e)}")
        return {}

def update_proxy_config(config: Dict[str, List[str]]) -> bool:
    """
    Update the proxy configuration.
    
    Args:
        config (Dict[str, List[str]]): The new proxy configuration
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        doc_ref = db.collection("config").document("proxies")
        doc_ref.set(config)
        return True
    except Exception as e:
        logger.error(f"Error updating proxy config: {str(e)}")
        return False

def get_user_consent(user_id: str) -> bool:
    """
    Check if a user has given consent.
    
    Args:
        user_id (str): The Telegram user ID
        
    Returns:
        bool: True if user has given consent, False otherwise
    """
    try:
        doc_ref = db.collection("user_consent").document(str(user_id))
        doc = doc_ref.get()
        return doc.exists
    except Exception as e:
        logger.error(f"Error checking user consent: {str(e)}")
        return False

def set_user_consent(user_id: str, has_consent: bool = True) -> bool:
    """
    Set user consent status.
    
    Args:
        user_id (str): The Telegram user ID
        has_consent (bool): Whether the user has given consent
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        doc_ref = db.collection("user_consent").document(str(user_id))
        if has_consent:
            doc_ref.set({"timestamp": firestore.SERVER_TIMESTAMP})
        else:
            doc_ref.delete()
        return True
    except Exception as e:
        logger.error(f"Error setting user consent: {str(e)}")
        return False 