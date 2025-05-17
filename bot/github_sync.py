import os
import requests
from google.cloud import storage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
GITHUB_URL = os.environ.get("GITHUB_PROXY_JSON_URL")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
DEST_PATH = os.environ.get("GCS_DEST_PATH", "proxies.json")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Validate required environment variables
REQUIRED_ENV_VARS = ["GITHUB_PROXY_JSON_URL", "BUCKET_NAME"]
for var in REQUIRED_ENV_VARS:
    if not os.environ.get(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

def main(request=None):
    """
    Fetches a JSON file from GitHub and uploads it to a Google Cloud Storage bucket.

    Args:
        request: Optional HTTP request object (for serverless environments).

    Returns:
        Tuple[str, int]: A message and HTTP status code.
    """
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        # Fetch the JSON file from GitHub
        logger.info("Fetching proxies.json from GitHub...")
        resp = requests.get(GITHUB_URL, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Failed to fetch from GitHub: {resp.status_code} {resp.text}")
            return f"Failed to fetch from GitHub: {resp.status_code} {resp.text}", 500

        content = resp.text
        logger.info("Successfully fetched proxies.json from GitHub.")

        # Upload the content to Google Cloud Storage
        client = storage.Client()
        try:
            bucket = client.get_bucket(BUCKET_NAME)
        except Exception as e:
            logger.error(f"Failed to access bucket {BUCKET_NAME}: {str(e)}")
            return f"❌ Failed to access bucket {BUCKET_NAME}: {str(e)}", 500

        blob = bucket.blob(DEST_PATH)
        blob.upload_from_string(content, content_type="application/json")
        logger.info(f"Successfully uploaded proxies.json to gs://{BUCKET_NAME}/{DEST_PATH}")

        return f"✅ Synced proxies.json to gs://{BUCKET_NAME}/{DEST_PATH}", 200

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error: {str(e)}")
        return f"❌ HTTP request error: {str(e)}", 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"❌ Sync error: {str(e)}", 500
