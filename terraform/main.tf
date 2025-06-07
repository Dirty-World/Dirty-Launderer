terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Main bot function
resource "google_cloudfunctions_function" "dirty_launderer_bot" {
  name        = "dirty-launderer-bot"
  description = "Main Telegram bot function"
  runtime     = "python311"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.function_zip.name
  trigger_http          = true
  entry_point           = "main"

  environment_variables = {
    TELEGRAM_TOKEN         = var.telegram_token
    FIRESTORE_FUNCTION_URL = google_cloudfunctions_function.firestore_function.https_trigger_url
    HASH_SALT             = var.hash_salt
  }
}

# Firestore function
resource "google_cloudfunctions_function" "firestore_function" {
  name        = "dirty-launderer-firestore"
  description = "Firestore operations function"
  runtime     = "python311"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.firestore_function_zip.name
  trigger_http          = true
  entry_point           = "main"

  environment_variables = {
    HASH_SALT = var.hash_salt
  }
}

# Webhook check function
resource "google_cloudfunctions_function" "webhook_check" {
  name        = "dirty-launderer-webhook-check"
  description = "Webhook check function"
  runtime     = "python311"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.webhook_function_zip.name
  trigger_http          = true
  entry_point           = "main"
}

# Storage bucket for function source code
resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project_id}-function-source"
  location = var.region
  uniform_bucket_level_access = true
}

# Main bot function source code
resource "google_storage_bucket_object" "function_zip" {
  name   = "bot-source.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = "../dist/bot-source.zip"
}

# Firestore function source code
resource "google_storage_bucket_object" "firestore_function_zip" {
  name   = "firestore-function.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = "../dist/firestore-function.zip"
}

# Webhook function source code
resource "google_storage_bucket_object" "webhook_function_zip" {
  name   = "webhook-function.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = "../dist/webhook-function.zip"
}

# IAM bindings for functions
resource "google_cloudfunctions_function_iam_member" "firestore_function_invoker" {
  project        = google_cloudfunctions_function.firestore_function.project
  region         = google_cloudfunctions_function.firestore_function.region
  cloud_function = google_cloudfunctions_function.firestore_function.name
  role           = "roles/cloudfunctions.invoker"
  member         = "serviceAccount:${google_cloudfunctions_function.dirty_launderer_bot.service_account_email}"
}

resource "google_cloudfunctions_function_iam_member" "webhook_function_invoker" {
  project        = google_cloudfunctions_function.webhook_check.project
  region         = google_cloudfunctions_function.webhook_check.region
  cloud_function = google_cloudfunctions_function.webhook_check.name
  role           = "roles/cloudfunctions.invoker"
  member         = "serviceAccount:${google_cloudfunctions_function.dirty_launderer_bot.service_account_email}"
} 