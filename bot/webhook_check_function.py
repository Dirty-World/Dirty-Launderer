import os
import requests
import logging
from urllib.parse import urlparse
from google.cloud import secretmanager
from typing import Optional, Tuple, Any, Dict, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> str:
    """Fetch a secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def is_valid_url(url: Optional[str]) -> bool:
    """Validate URL format."""
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    except Exception:
        return False

def send_alert(message: str, token: str, chat_id: str, requests_mod=requests) -> None:
    """Send alert to admin chat."""
    try:
        requests_mod.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": f"[The Dirty Launderer Webhook] {message}",
            },
            timeout=10
        )
    except Exception as e:
        logger.error(f"Failed to send alert: {type(e).__name__}: {e}")

def load_config(env: dict = os.environ, secret_func: Callable = get_secret) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Load configuration from environment and Secret Manager if needed."""
    token = env.get('TELEGRAM_TOKEN')
    if not token:
        project_id = env.get('GCP_PROJECT_ID')
        if project_id:
            try:
                token = secret_func(project_id, "TELEGRAM_BOT_TOKEN")
            except Exception as e:
                logger.error(f"Error loading token from Secret Manager: {e}")
                token = None
    expected_url = env.get('EXPECTED_WEBHOOK_URL')
    alert_chat_id = env.get('ALERT_CHAT_ID')
    return token, expected_url, alert_chat_id

def get_current_webhook(token: str, requests_mod=requests) -> Optional[str]:
    """Get the current webhook URL from Telegram API."""
    get_webhook_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    response = requests_mod.get(get_webhook_url, timeout=10)
    response.raise_for_status()
    webhook_info = response.json()
    return webhook_info.get("result", {}).get("url", "")

def set_webhook(token: str, url: str, requests_mod=requests) -> None:
    """Set the webhook URL via Telegram API."""
    set_webhook_url = f"https://api.telegram.org/bot{token}/setWebhook"
    payload = {
        "url": url,
        "allowed_updates": ["message", "callback_query"],
        "max_connections": 100
    }
    response = requests_mod.post(set_webhook_url, json=payload, timeout=10)
    response.raise_for_status()

def main(request, env: dict = os.environ, requests_mod=requests, secret_func: Callable = get_secret) -> Tuple[Dict[str, Any], int]:
    """Cloud Function entry point for webhook check."""
    try:
        token, expected_url, alert_chat_id = load_config(env, secret_func)

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
        try:
            current_url = get_current_webhook(token, requests_mod)
        except requests_mod.RequestException as e:
            error_msg = f"HTTP error: {type(e).__name__}: {e}"
            logger.error(error_msg)
            if alert_chat_id:
                send_alert(error_msg, token, alert_chat_id, requests_mod)
            return {"error": error_msg}, 500

        # Check if webhook needs updating
        if current_url != expected_url:
            logger.warning(f"Webhook mismatch. Current: {current_url}")
            try:
                set_webhook(token, expected_url, requests_mod)
                success_msg = f"Webhook successfully updated to: {expected_url}"
                logger.info(success_msg)
                if alert_chat_id:
                    send_alert(success_msg, token, alert_chat_id, requests_mod)
                return {"status": "updated", "message": success_msg}, 200
            except requests_mod.RequestException as e:
                error_msg = f"HTTP error during webhook update: {type(e).__name__}: {e}"
                logger.error(error_msg)
                if alert_chat_id:
                    send_alert(error_msg, token, alert_chat_id, requests_mod)
                return {"error": error_msg}, 500

        logger.info("Webhook is correctly configured")
        return {"status": "ok", "message": "Webhook is up to date"}, 200

    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}: {e}"
        logger.error(error_msg)
        # Try to send alert if possible
        token = env.get('TELEGRAM_TOKEN')
        alert_chat_id = env.get('ALERT_CHAT_ID')
        if token and alert_chat_id:
            try:
                send_alert(error_msg, token, alert_chat_id, requests_mod)
            except Exception as alert_exc:
                logger.error(f"Failed to send alert in exception handler: {alert_exc}")
        return {"error": error_msg}, 500 