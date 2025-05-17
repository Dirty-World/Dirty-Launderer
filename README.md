[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=flat&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/)

# The Dirty Launderer🧼 Infrastructure

Infrastructure as Code (IaC) repository for The Dirty Launderer🧼 bot. This repository contains all the necessary Terraform configurations and deployment workflows to set up and maintain the bot's cloud infrastructure on Google Cloud Platform.

## 🏗️ Infrastructure Components

- **Cloud Functions**
  - Main bot function (Python 3.11 runtime)
  - Event-driven architecture
  - Telegram webhook integration

- **Firestore**
  - Document database for storing:
    - Domain configurations
    - User preferences
    - Logging settings
  - Native GCP integration

- **Cloud Storage**
  - Artifact storage for bot deployments
  - Version control for releases

- **Monitoring & Logging**
  - Cloud Monitoring dashboards
  - PII-safe structured logging
  - Alert policies
  - Error reporting

- **Security**
  - Workload Identity Federation
  - Secret Manager integration
  - Minimal IAM permissions

## 📁 Repository Structure

```
dirty-launderer-infra/
├── terraform/
│   ├── environments/          # Environment-specific configs
│   │   ├── dev/
│   │   └── prod/
│   ├── modules/              # Reusable Terraform modules
│   │   ├── function/
│   │   ├── firestore/
│   │   ├── monitoring/
│   │   └── security/
│   └── shared/              # Shared configurations
├── .github/
│   └── workflows/           # GitHub Actions
│       ├── deploy.yml       # Infrastructure deployment
│       └── test.yml        # Terraform validation
└── README.md
```

## 🚀 Deployment Process

1. **Prerequisites**:
   - Google Cloud project with required APIs enabled
   - GitHub repository secrets configured
   - Workload Identity Federation set up

2. **GitHub Secrets Required**:
   - `GCP_PROJECT_ID` - Google Cloud project identifier
   - `GCS_BUCKET_NAME` - Artifact storage bucket
   - `GITHUB_TOKEN` - For repository dispatch events

3. **Deployment Flow**:
   - Triggered by:
     - Push to main branch
     - Manual workflow dispatch
     - Repository dispatch from main bot repo
   - Actions:
     - Validates Terraform configurations
     - Applies infrastructure changes
     - Updates Cloud Function code
     - Configures monitoring and alerts
     - Sets up Telegram webhook

4. **Environment Support**:
   - Development (`dev`)
   - Production (`prod`)
   - Environment-specific configurations and secrets

## 🔧 Local Development

1. **Setup**:
   ```bash
   # Install required tools
   terraform init
   
   # Configure GCP authentication
   gcloud auth application-default login
   ```

2. **Testing**:
   ```bash
   # Validate Terraform configurations
   terraform validate
   
   # Check planned changes
   terraform plan
   ```

3. **Manual Deployment**:
   ```bash
   # Apply changes to dev
   terraform workspace select dev
   terraform apply
   
   # Apply to production
   terraform workspace select prod
   terraform apply
   ```

## 🔒 Security Notes

- All secrets are managed through Google Cloud Secret Manager
- Minimal IAM roles following principle of least privilege
- Workload Identity Federation used for GitHub Actions
- Regular security scanning and updates

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `terraform fmt` and `terraform validate`
5. Submit a pull request

## 💬 Support

For infrastructure-related issues or questions:
1. Check existing GitHub issues
2. Review the documentation
3. Create a new issue with the "infrastructure" label

Made with 🧼 by The Dirty Launderer🧼 team
