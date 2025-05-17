#!/bin/bash

# Set your project ID
PROJECT_ID="the-dirty-launderer"

# Import PubSub subscriptions
terraform import google_pubsub_subscription.shutdown_trigger_sub projects/$PROJECT_ID/subscriptions/dev-budget-trigger-sub
terraform import google_pubsub_subscription.budget_alert_subscription_main projects/$PROJECT_ID/subscriptions/budget-alert-subscription-main

# Import Cloud Function
terraform import google_cloudfunctions_function.budget_alert_function projects/$PROJECT_ID/locations/us-central1/functions/budget-alert-function 