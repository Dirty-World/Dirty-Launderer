> 🚧 **UNDER CONSTRUCTION** 🚧
> 
> This project is currently being developed. Features and documentation may be incomplete.

<div align="center">
  <img src="assets/dirty-launderer-logo.png" alt="The Dirty Launderer Logo" width="300"/>
</div>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://telegram.org/)
[![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/)

# The Dirty Launderer 🧼

💃 A lady in the streets, and clean in the sheets... of tracking parameters. 🧼

A privacy-first Telegram bot that automatically cleanses URLs of tracking parameters and provides privacy-respecting alternatives through services like Invidious, Nitter, Libreddit, and more.

## 🎯 Purpose

The Dirty Launderer serves as your personal privacy guardian by:
- 🧹 Stripping tracking parameters from shared URLs
- 🔄 Redirecting social media links to privacy-respecting frontends
- 🛡️ Protecting your digital footprint from unnecessary surveillance
- ✨ Making privacy-conscious browsing effortless
- 🧼 Keeping your online activities clean and tracker-free

Think of it as your digital laundromat - keeping your browsing pristine and your data private! ✨

## 🤖 Features

- 🧹 **URL Cleaning**: Automatically removes tracking parameters (UTM, fbclid, etc.)
- 🔒 **Privacy Alternatives**: 
  - 📺 YouTube → Invidious
  - 🐦 Twitter → Nitter
  - 🤖 Reddit → Libreddit
  - 📸 Instagram → Bibliogram
  - ✨ And more!
- 👥 **Group Support**: Works in both private chats and group conversations
- ⚙️ **Customizable Settings**: Choose which services and parameters to clean
- 🤫 **Zero Logging**: No storage of user data or cleaned URLs
- 🏠 **Self-hostable**: Run your own instance for maximum privacy
- 🌐 **Multi-environment Support**: Separate configurations for development and production

## 🏗️ Architecture & Deployment

This project uses a **two-repository deployment architecture** for security and separation of concerns:

### 📦 Repository Structure
1. **[Main Repository (This Repo)](https://github.com/Dirty-World/Dirty-Launderer)**: Contains bot code, tests, and application logic
2. **[Infrastructure Repository](https://github.com/Dirty-World/Dirty-Launderer-Infra)**: Contains Terraform configurations and infrastructure definitions

### 🔄 Deployment Flow
```mermaid
graph LR
    A[Code Push to Main] --> B[Build & Test Bot Code]
    B --> C[Package & Upload to GCS]
    C --> D[Trigger Infrastructure Repo]
    D --> E[Download Bot Code from GCS]
    E --> F[Apply Terraform]
    F --> G[Deploy Cloud Functions]
```

1. **Main Repo Workflow**:
   - Runs tests and builds bot code
   - Creates deployment package (`bot-source.zip`)
   - Uploads package to Google Cloud Storage
   - Triggers infrastructure repository via repository dispatch

2. **Infrastructure Repo Workflow** (Automatically triggered):
   - Downloads the bot package from GCS
   - Runs Terraform to provision/update infrastructure
   - Deploys Cloud Functions with the new code
   - Sets up monitoring and webhooks

### 🔐 Security Model
- **Workload Identity Federation**: No service account keys stored anywhere
- **Google Secret Manager**: All sensitive values (tokens, IDs) stored securely in GCP
- **Cross-Repository Authentication**: Infrastructure repo triggered securely from main repo
- **Least Privilege**: Each repository has only the permissions it needs

## 🛠️ Tech Stack

- 🐍 **Python 3.11**: Core programming language
- ☁️ **Google Cloud Functions**: Serverless compute
- 📦 **Firestore**: Configuration storage (no user data)
- 💾 **Cloud Storage**: Artifact storage
- 🔐 **Secret Manager**: Secure credentials management
- 🔄 **GitHub Actions**: CI/CD pipeline

## 🚀 Getting Started

1. 📋 **Prerequisites**:
   - Python 3.11
   - Google Cloud SDK
   - Telegram Bot Token (from @BotFather)

2. 💻 **Local Setup**:
   ```bash
   # Clone the repository
   git clone https://github.com/Dirty-World/dirty-launderer.git
   cd dirty-launderer

   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements-dev.txt
   ```

3. ⚙️ **Configuration**:
   - Create a `.env` file with required environment variables
   - Set up Google Cloud credentials
   - Configure Telegram webhook

## 🧪 Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=bot
```

## 📦 Deployment

### 🏗️ Two-Repository Setup Required

**Before deploying the bot, you must set up both repositories:**

1. **First**: Set up the [Infrastructure Repository](https://github.com/Dirty-World/Dirty-Launderer-Infra)
   - Contains Terraform configurations
   - Provisions Google Cloud resources
   - Must be configured before deploying bot code

2. **Then**: Deploy bot code from this repository
   - Automatically triggered on push to `main` branch
   - Can also be triggered manually via GitHub Actions

### 🚀 Automatic Deployment

The bot is automatically deployed via our two-stage pipeline when:
- 🔄 Code is pushed to the main branch
- 🖱️ Manual workflow dispatch is triggered from GitHub Actions

### 🔧 Manual Deployment Prerequisites

If you need to deploy manually, ensure you have:
- Google Cloud SDK installed and authenticated
- Access to the `the-dirty-launderer` GCP project
- Required secrets configured in Google Secret Manager
- Infrastructure repository properly set up with Terraform

For detailed setup instructions, see the [Infrastructure Repository](https://github.com/Dirty-World/Dirty-Launderer-Infra).

## 🔒 Security

- 🔐 All sensitive data is stored in Google Cloud Secret Manager
- 🔒 Webhook endpoints are secured with HTTPS
- ✅ Input validation and sanitization
- 🔄 Regular security updates and monitoring

## 📝 Contributing

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/amazing-feature`)
3. 💻 Make your changes
4. 🧪 Run tests
5. 📤 Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 💬 Support

For bot-related issues or questions:
1. 🔍 Check existing GitHub issues
2. 📖 Review the documentation
3. ➕ Create a new issue with details about your problem

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

🧼 Made with love by The Dirty Launderer 🧼 team

## ⚙️ Admin Configuration

Administrators can configure the bot's behavior through various commands:

### 🎛️ Domain Handling
- `/setdomain` - Configure how specific domains are handled:
  - 🧹 `clean` - Remove tracking parameters
  - 🔄 `proxy` - Redirect through privacy-respecting frontend
  - 💤 `ignore` - Leave URLs unchanged
- `/listdomains` - View current domain rules
- `/resetdomains` - Reset to default settings
- `/setdefault` - Set default behavior for unconfigured domains

### 📝 Default Domain Settings
```json
{
  "tiktok.com": "proxy",
  "twitter.com": "proxy",
  "youtube.com": "proxy",
  "instagram.com": "clean",
  "facebook.com": "proxy",
  "reddit.com": "proxy",
  "amazon.com": "clean"
}
```

### 🔒 Privacy Frontends
The bot uses multiple instances for each privacy-respecting frontend:
- 📺 **Invidious** (YouTube): invidious.snopyta.org, yewtu.be, etc.
- 🐦 **Nitter** (Twitter): nitter.net, nitter.privacydev.net, etc.
- 🤖 **Libreddit** (Reddit): libreddit.kavin.rocks, libreddit.privacydev.net
- 📝 **Scribe** (Medium): scribe.rip, scribe.privacydev.net

### 📊 Monitoring & Logging
- `/setlogging` - Toggle safe logging (no personal data stored)
- `/showlogging` - View current logging status
- `/configsummary` - Display group's current configuration
- `/proxies` - Show count of active proxy frontends
- `/status` - Check bot and webhook health
- `/alerttest` - Test admin notifications

### 👥 Group-Specific Settings
Each Telegram group can have its own configuration:
- 🎯 Custom domain rules
- ⚙️ Different default behaviors
- 📝 Independent logging settings

All settings are stored in Firestore with no user data retention.
