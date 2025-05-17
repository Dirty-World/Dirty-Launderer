# firestore.py
# Firestore backend for Dirty Launderer bot
# Uses consistent naming conventions for collections and global config

from google.cloud import firestore

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

# Per-group config stored in collection: dirty_launderer_group_configs
def get_group_config(chat_id):
    doc_ref = client.collection("dirty_launderer_group_configs").document(str(chat_id))
    try:
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        print(f"Error fetching group config for chat_id {chat_id}: {e}")
    return DEFAULT_CONFIG

def set_group_domain(chat_id, domain, mode):
    doc_ref = client.collection("dirty_launderer_group_configs").document(str(chat_id))
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
    doc_ref = client.collection("dirty_launderer_group_configs").document(str(chat_id))
    try:
        doc_ref.set(DEFAULT_CONFIG.copy())
    except Exception as e:
        print(f"Error resetting group config for chat_id {chat_id}: {e}")

def set_group_logging(chat_id, enabled):
    doc_ref = client.collection("dirty_launderer_group_configs").document(str(chat_id))
    try:
        # Fetch existing data or use default
        doc = doc_ref.get()
        data = doc.to_dict() if doc.exists else DEFAULT_CONFIG.copy()

        # Update the logging field
        data["logging"] = enabled
        doc_ref.set(data)
    except Exception as e:
        print(f"Error setting logging for chat_id {chat_id}: {e}")

# Global fallback setting stored in: dirty_launderer_global_config/default
def set_default_mode(mode):
    ref = client.collection("dirty_launderer_global_config").document("default")
    try:
        ref.set({"mode": mode})
    except Exception as e:
        print(f"Error setting default mode to {mode}: {e}")

def get_default_mode():
    ref = client.collection("dirty_launderer_global_config").document("default")
    try:
        doc = ref.get()
        if doc.exists:
            return doc.to_dict().get("mode", "proxy")
    except Exception as e:
        print(f"Error fetching default mode: {e}")
    return "proxy"
