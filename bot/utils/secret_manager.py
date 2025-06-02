import os
from google.cloud import secretmanager

def get_secret(secret_id, version_id="latest"):
    """Fetch a secret from Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GCP_PROJECT_ID')
        if not project_id:
            raise ValueError("GCP_PROJECT_ID environment variable not set")
            
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        raise Exception(f"Error accessing secret {secret_id}: {str(e)}")

def create_secret(secret_id, secret_value):
    """Create a new secret in Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GCP_PROJECT_ID')
        if not project_id:
            raise ValueError("GCP_PROJECT_ID environment variable not set")
            
        parent = f"projects/{project_id}"
        
        # Create the secret
        secret = client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        
        # Add the secret version
        client.add_secret_version(
            request={
                "parent": secret.name,
                "payload": {"data": secret_value.encode("UTF-8")},
            }
        )
        
        return True
    except Exception as e:
        raise Exception(f"Error creating secret {secret_id}: {str(e)}") 