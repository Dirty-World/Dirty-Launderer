import os
import requests
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate required environment variables
REQUIRED_ENV_VARS = ["TELEGRAM_TOKEN", "EXPECTED_WEBHOOK_URL"]
for var in REQUIRED_ENV_VARS:
    if not os.environ.get(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
EXPECTED_WEBHOOK_URL = os.environ["EXPECTED_WEBHOOK_URL"]
ALERT_CHAT_ID = os.environ.get("ALERT_CHAT_ID")  # Optional

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

if not is_valid_url(EXPECTED_WEBHOOK_URL):
    raise ValueError(f"Invalid EXPECTED_WEBHOOK_URL: {EXPECTED_WEBHOOK_URL}")

def send_alert(message):
    if ALERT_CHAT_ID:
        alert_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": ALERT_CHAT_ID,
            "text": f"🚨 [Dirty Launderer Webhook] {message}"
        }
        try:
            response = requests.post(alert_url, data=payload, timeout=10)
            response.raise_for_status()
            logger.info("Alert sent successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send alert: {e}")
    else:
        logger.warning("ALERT_CHAT_ID is not set. Alerts will not be sent.")

def main(request):
    try:
        logger.info("Checking Telegram webhook...")
        get_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
        response = requests.get(get_url, timeout=10)
        response.raise_for_status()

        info = response.json()
        current_url = info.get("result", {}).get("url", "")

        if current_url != EXPECTED_WEBHOOK_URL:
            logger.warning(f"Webhook URL mismatch. Expected: {EXPECTED_WEBHOOK_URL}, Found: {current_url}")
            set_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
            set_resp = requests.post(set_url, data={"url": EXPECTED_WEBHOOK_URL}, timeout=10)
            set_resp.raise_for_status()

            send_alert(f"✅ Webhook successfully re-registered to: {EXPECTED_WEBHOOK_URL}")
            logger.info("Webhook re-registered successfully.")
            return {"status": "success", "message": "Webhook re-registered"}, 200

        logger.info("Webhook is up to date.")
        return {"status": "success", "message": "Webhook is up to date"}, 200

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error while checking or setting webhook: {e}")
        send_alert(f"❌ HTTP error while checking or setting webhook: {e}")
        return {"status": "error", "message": f"HTTP error: {e}"}, 500

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        send_alert(f"❌ Unexpected error: {e}")
        return {"status": "error", "message": f"Error: {e}"}, 500
