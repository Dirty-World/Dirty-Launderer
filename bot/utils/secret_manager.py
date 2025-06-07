import os
import logging
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

def get_secret(secret_id: str) -> str:
    """
    Get a secret from Google Cloud Secret Manager.
    
    Args:
        secret_id (str): The ID of the secret to retrieve
        
    Returns:
        str: The secret value
        
    Raises:
        Exception: If the secret cannot be retrieved
    """
    try:
        # Get project ID from environment variable
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            raise EnvironmentError("GOOGLE_CLOUD_PROJECT environment variable not set")
            
        # Create the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()
        
        # Build the resource name of the secret version
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        
        # Access the secret version
        response = client.access_secret_version(request={"name": name})
        
        # Return the secret payload
        return response.payload.data.decode("UTF-8")
        
    except Exception as e:
        logger.error(f"Failed to get secret {secret_id}: {str(e)}")
        raise

def create_secret(secret_id, secret_value):
    """Create a new secret in environment variables.
    Note: This is a no-op as environment variables should be set externally."""
    raise NotImplementedError(
        "Environment variables must be set externally. "
        "Please set the environment variable manually or use your deployment platform's secret management."
    ) 