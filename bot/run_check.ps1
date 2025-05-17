$token = $(gcloud secrets versions access latest --secret="TELEGRAM_BOT_TOKEN")
$env:TELEGRAM_TOKEN = $token
$env:EXPECTED_WEBHOOK_URL = "https://us-central1-the-dirty-launderer.cloudfunctions.net/dirty-launderer-bot"
python webhook_check.py 