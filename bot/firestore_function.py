import os
import json
import logging
from flask import Flask, request, jsonify
from google.cloud import firestore
from typing import Dict, List, Optional, Any
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore client
db = firestore.Client()

def hash_domain(domain: str) -> str:
    """Hash a domain to avoid storing PII."""
    if not domain:
        return 'unknown'
    salt = os.environ.get('HASH_SALT', 'default-salt')
    return hashlib.sha256(f"{salt}{domain.lower()}".encode()).hexdigest()[:8]

def get_group_config(chat_id: str) -> Dict[str, Any]:
    """Get configuration for a specific group."""
    try:
        doc_ref = db.collection("group_config").document(str(chat_id))
        doc = doc_ref.get()
        
        if not doc.exists:
            return {
                "default_behavior": "clean",
                "domain_rules": {}
            }
            
        config = doc.to_dict()
        if "domain_rules" in config:
            readable_rules = {}
            for hashed_domain, rule in config["domain_rules"].items():
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
    """Update configuration for a specific group."""
    try:
        doc_ref = db.collection("group_config").document(str(chat_id))
        
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
    """Get the current proxy configuration."""
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
    """Update the proxy configuration."""
    try:
        doc_ref = db.collection("config").document("proxies")
        doc_ref.set(config)
        return True
    except Exception as e:
        logger.error(f"Error updating proxy config: {str(e)}")
        return False

def get_user_consent(user_id: str) -> bool:
    """Check if a user has given consent."""
    try:
        doc_ref = db.collection("user_consent").document(str(user_id))
        doc = doc_ref.get()
        return doc.exists
    except Exception as e:
        logger.error(f"Error checking user consent: {str(e)}")
        return False

def set_user_consent(user_id: str, has_consent: bool = True) -> bool:
    """Set user consent status."""
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

@app.route('/', methods=['POST'])
def main(request):
    """Cloud Function entry point."""
    try:
        request_json = request.get_json()
        if not request_json:
            return jsonify({"error": "No JSON data provided"}), 400

        action = request_json.get('action')
        if not action:
            return jsonify({"error": "No action specified"}), 400

        # Handle different actions
        if action == 'get_group_config':
            chat_id = request_json.get('chat_id')
            if not chat_id:
                return jsonify({"error": "No chat_id provided"}), 400
            config = get_group_config(chat_id)
            return jsonify({"config": config})

        elif action == 'update_group_config':
            chat_id = request_json.get('chat_id')
            config = request_json.get('config')
            if not chat_id or not config:
                return jsonify({"error": "Missing chat_id or config"}), 400
            success = update_group_config(chat_id, config)
            return jsonify({"success": success})

        elif action == 'get_proxy_config':
            config = get_proxy_config()
            return jsonify({"config": config})

        elif action == 'update_proxy_config':
            config = request_json.get('config')
            if not config:
                return jsonify({"error": "No config provided"}), 400
            success = update_proxy_config(config)
            return jsonify({"success": success})

        elif action == 'get_user_consent':
            user_id = request_json.get('user_id')
            if not user_id:
                return jsonify({"error": "No user_id provided"}), 400
            has_consent = get_user_consent(user_id)
            return jsonify({"has_consent": has_consent})

        elif action == 'set_user_consent':
            user_id = request_json.get('user_id')
            has_consent = request_json.get('has_consent', True)
            if not user_id:
                return jsonify({"error": "No user_id provided"}), 400
            success = set_user_consent(user_id, has_consent)
            return jsonify({"success": success})

        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500 