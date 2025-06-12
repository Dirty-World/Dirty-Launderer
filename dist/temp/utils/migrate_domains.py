import logging
from google.cloud import firestore
from .firestore import hash_domain
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def backup_domain_rules():
    """
    Create a backup of domain rules before migration.
    Returns the path to the backup file.
    """
    try:
        db = firestore.Client()
        group_configs = db.collection("group_config").stream()
        
        # Create backup directory if it doesn't exist
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"domain_rules_backup_{timestamp}.json")
        
        backup_data = {}
        for doc in group_configs:
            config = doc.to_dict()
            if "domain_rules" in config:
                backup_data[doc.id] = config["domain_rules"]
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
            
        logger.info(f"Created backup at {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return None

def migrate_domain_rules():
    """
    Migrate existing domain rules to use hashed domains.
    This is a one-time migration that should be run after deploying the new code.
    """
    try:
        # Create backup before migration
        backup_file = backup_domain_rules()
        if not backup_file:
            logger.error("Failed to create backup, aborting migration")
            return False
            
        db = firestore.Client()
        group_configs = db.collection("group_config").stream()
        
        for doc in group_configs:
            config = doc.to_dict()
            if "domain_rules" in config:
                hashed_rules = {}
                for domain, rule in config["domain_rules"].items():
                    # Skip if domain is already hashed (8 chars)
                    if len(domain) == 8 and all(c in "0123456789abcdef" for c in domain):
                        hashed_rules[domain] = rule
                        continue
                        
                    hashed_domain = hash_domain(domain)
                    hashed_rules[hashed_domain] = rule
                    logger.info(f"Migrated domain {domain} to {hashed_domain}")
                
                # Update the document with hashed rules
                doc.reference.update({"domain_rules": hashed_rules})
                logger.info(f"Updated group config for {doc.id}")
        
        logger.info("Domain migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during domain migration: {str(e)}")
        return False

def rollback_domain_rules(backup_file: str = None):
    """
    Rollback domain rules to their original state using a backup file.
    
    Args:
        backup_file (str): Path to the backup file. If None, uses the most recent backup.
    """
    try:
        if not backup_file:
            # Find the most recent backup
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                logger.error("No backup directory found")
                return False
                
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith("domain_rules_backup_")]
            if not backup_files:
                logger.error("No backup files found")
                return False
                
            backup_file = os.path.join(backup_dir, sorted(backup_files)[-1])
            
        # Load backup data
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
            
        # Restore from backup
        db = firestore.Client()
        for chat_id, domain_rules in backup_data.items():
            doc_ref = db.collection("group_config").document(chat_id)
            doc = doc_ref.get()
            
            if doc.exists:
                config = doc.to_dict()
                config["domain_rules"] = domain_rules
                doc_ref.set(config)
                logger.info(f"Restored domain rules for chat {chat_id}")
            else:
                logger.warning(f"Chat {chat_id} no longer exists, skipping")
                
        logger.info(f"Rollback completed successfully using {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Error during rollback: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="Domain rules migration tool")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous state")
    parser.add_argument("--backup", help="Path to backup file for rollback")
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_domain_rules(args.backup)
    else:
        migrate_domain_rules() 