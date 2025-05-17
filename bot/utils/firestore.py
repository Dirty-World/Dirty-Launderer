# firestore.py
# Firestore backend for The Dirty Launderer🧼 bot
# Uses consistent naming conventions for collections and global config

from google.cloud import firestore
import logging

logger = logging.getLogger(__name__)
client = firestore.Client()

# Default config used for groups with no overrides
DEFAULT_CONFIG = {
    "domains": {
        "tiktok.com": "proxy",
        "twitter.com": "proxy",
        "youtube.com": "proxy",
        "instagram.com": "clean",
        "facebook.com": "proxy",
        "reddit.com": "proxy",
        "amazon.com": "clean"
    },
    "logging": False
}

def get_group_config(chat_id):
    """Get group-specific configuration."""
    try:
        # Per-group config stored in collection: the_dirty_launderer_group_configs
        doc_ref = client.collection("the_dirty_launderer_group_configs").document(str(chat_id))
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        logger.error(f"Failed to get group config: {type(e).__name__}")
        return None

def set_group_config(chat_id, config):
    """Set group-specific configuration."""
    try:
        doc_ref = client.collection("the_dirty_launderer_group_configs").document(str(chat_id))
        doc_ref.set(config)
        return True
    except Exception as e:
        logger.error(f"Failed to set group config: {type(e).__name__}")
        return False

def update_group_config(chat_id, updates):
    """Update group-specific configuration."""
    try:
        doc_ref = client.collection("the_dirty_launderer_group_configs").document(str(chat_id))
        doc_ref.update(updates)
        return True
    except Exception as e:
        logger.error(f"Failed to update group config: {type(e).__name__}")
        return False

def delete_group_config(chat_id):
    """Delete group-specific configuration."""
    try:
        doc_ref = client.collection("the_dirty_launderer_group_configs").document(str(chat_id))
        doc_ref.delete()
        return True
    except Exception as e:
        logger.error(f"Failed to delete group config: {type(e).__name__}")
        return False

def get_global_config():
    """Get global configuration."""
    try:
        # Global fallback setting stored in: the_dirty_launderer_global_config/default
        ref = client.collection("the_dirty_launderer_global_config").document("default")
        doc = ref.get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        logger.error(f"Failed to get global config: {type(e).__name__}")
        return None

def set_global_config(config):
    """Set global configuration."""
    try:
        ref = client.collection("the_dirty_launderer_global_config").document("default")
        ref.set(config)
        return True
    except Exception as e:
        logger.error(f"Failed to set global config: {type(e).__name__}")
        return False

def set_group_domain(chat_id, domain, mode):
    doc_ref = client.collection("the_dirty_launderer_group_configs").document(str(chat_id))
    try:
        # Fetch existing data or use default
        doc = doc_ref.get()
        data = doc.to_dict() if doc.exists else DEFAULT_CONFIG.copy()

        # Update the domain mode
        data["domains"][domain] = mode
        doc_ref.set(data)
    except Exception as e:
        print(f"Error setting group domain for chat_id {chat_id}, domain {domain}: {e}")

def reset_group_config(chat_id):
    doc_ref = client.collection("the_dirty_launderer_group_configs").document(str(chat_id))
    try:
        doc_ref.set(DEFAULT_CONFIG.copy())
    except Exception as e:
        print(f"Error resetting group config for chat_id {chat_id}: {e}")

def set_group_logging(chat_id, enabled):
    doc_ref = client.collection("the_dirty_launderer_group_configs").document(str(chat_id))
    try:
        # Fetch existing data or use default
        doc = doc_ref.get()
        data = doc.to_dict() if doc.exists else DEFAULT_CONFIG.copy()

        # Update the logging field
        data["logging"] = enabled
        doc_ref.set(data)
    except Exception as e:
        print(f"Error setting logging for chat_id {chat_id}: {e}")

# Global fallback setting stored in: the_dirty_launderer_global_config/default
def set_default_mode(mode):
    ref = client.collection("the_dirty_launderer_global_config").document("default")
    try:
        ref.set({"mode": mode})
    except Exception as e:
        print(f"Error setting default mode to {mode}: {e}")

def get_default_mode():
    ref = client.collection("the_dirty_launderer_global_config").document("default")
    try:
        doc = ref.get()
        if doc.exists:
            return doc.to_dict().get("mode", "proxy")
    except Exception as e:
        print(f"Error fetching default mode: {e}")
    return "proxy"
