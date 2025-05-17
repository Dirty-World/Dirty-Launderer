@echo off
setlocal

REM Change to terraform directory
cd terraform

REM Set your project ID
set PROJECT_ID=the-dirty-launderer

REM Import PubSub subscriptions
terraform init
terraform import google_pubsub_subscription.shutdown_trigger_sub projects/%PROJECT_ID%/subscriptions/dev-budget-trigger-sub
terraform import google_pubsub_subscription.budget_alert_subscription_main projects/%PROJECT_ID%/subscriptions/budget-alert-subscription-main

REM Import Cloud Function
terraform import google_cloudfunctions_function.budget_alert_function projects/%PROJECT_ID%/locations/us-central1/functions/budget-alert-function 