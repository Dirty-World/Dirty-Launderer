import os
import requests
import logging
from urllib.parse import urlparse
from google.cloud import secretmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_secret(project_id, secret_id, version_id="latest"):
    """Fetch a secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def is_valid_url(url):
    """Validate URL format."""
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    except:
        return False

def send_alert(message):
    """Send alert to admin chat."""
    try:
        requests.post(
            f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
            data={
                "chat_id": os.environ["ALERT_CHAT_ID"],
                "text": f"[The Dirty Launderer Webhook] {message}",
            },
            timeout=10
        )
    except Exception as e:
        logger.error(f"Failed to send alert: {type(e).__name__}")

def main(request):
    """Cloud Function entry point for webhook check."""
    try:
        # Fetch the token from Secret Manager
        project_id = os.environ.get('GCP_PROJECT_ID')
        token = get_secret(project_id, "TELEGRAM_BOT_TOKEN")
        expected_url = os.environ.get('EXPECTED_WEBHOOK_URL')
        alert_chat_id = os.environ.get('ALERT_CHAT_ID')

        if not token or not expected_url:
            error_msg = "Missing required environment variables or secrets"
            logger.error(error_msg)
            return {"error": error_msg}, 500

        if not is_valid_url(expected_url):
            error_msg = f"Invalid EXPECTED_WEBHOOK_URL format: {expected_url}"
            logger.error(error_msg)
            return {"error": error_msg}, 500

        # Check current webhook
        logger.info("Checking current webhook configuration...")
        get_webhook_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        response = requests.get(get_webhook_url, timeout=10)
        response.raise_for_status()
        webhook_info = response.json()

        current_url = webhook_info.get("result", {}).get("url", "")
        
        # Check if webhook needs updating
        if current_url != expected_url:
            logger.warning(f"Webhook mismatch. Current: {current_url}")
            
            # Set the webhook
            set_webhook_url = f"https://api.telegram.org/bot{token}/setWebhook"
            payload = {
                "url": expected_url,
                "allowed_updates": ["message", "callback_query"],
                "max_connections": 100
            }
            set_response = requests.post(set_webhook_url, json=payload, timeout=10)
            set_response.raise_for_status()

            success_msg = f"Webhook successfully updated to: {expected_url}"
            logger.info(success_msg)
            send_alert(success_msg)
            return {"status": "updated", "message": success_msg}, 200

        logger.info("Webhook is correctly configured")
        return {"status": "ok", "message": "Webhook is up to date"}, 200

    except requests.exceptions.RequestException as e:
        error_msg = f"HTTP error: {type(e).__name__}"
        logger.error(error_msg)
        send_alert(f"Error: {error_msg}")
        return {"error": error_msg}, 500

    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}"
        logger.error(error_msg)
        send_alert(f"Error: {error_msg}")
        return {"error": error_msg}, 500 