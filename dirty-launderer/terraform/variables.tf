# Required variables - no default as it should be explicitly provided
variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
  default     = "the-dirty-launderer"  # Static project ID
}

# Non-sensitive variables with static defaults
variable "region" {
  description = "Region to deploy resources"
  type        = string
  default     = "us-central1"
}

variable "GCS_BUCKET_NAME" {
  description = "The name of the GCS bucket used to store the bot ZIP"
  type        = string
  default     = "dirty-launderer-bucket"  # Using existing bucket
}

variable "bot_source_archive" {
  description = "The name of the source archive object for the bot function"
  type        = string
  default     = "bot-source.zip"
}

variable "github_proxy_sync_source" {
  description = "The name of the source archive object for the GitHub proxy sync function"
  type        = string
  default     = "github-proxy-sync.zip"
}

variable "github_proxy_json_url" {
  description = "The URL of the GitHub JSON file containing proxy information"
  type        = string
  default     = "https://raw.githubusercontent.com/the-dirty-launderer/proxy-list/main/proxies.json"
}

variable "budget_amount" {
  description = "The budget amount in USD"
  type        = number
  default     = 1
}

variable "environment" {
  description = "The environment (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
} 