# Triggering GitHub Actions Deploy from the Web

This guide explains how to manually trigger a GitHub Actions workflow for deploying the Dirty Launderer bot.

## 🚀 Steps to Trigger a Deployment

1. **Navigate to the Repository**:
   - Go to the GitHub repository: [https://github.com/your-repo](https://github.com/your-repo).

2. **Access the Actions Tab**:
   - Click on the `Actions` tab in the repository.

3. **Select the Deployment Workflow**:
   - Look for the workflow named `Deploy` (or the relevant workflow for deployment).
   - Click on it to view the workflow details.

4. **Trigger the Workflow**:
   - Click the `Run workflow` button on the right-hand side.
   - If the workflow requires input parameters (e.g., environment or branch), fill them in.
   - Click `Run workflow` to start the deployment.

5. **Monitor the Workflow**:
   - Once triggered, you can monitor the progress of the workflow in the `Actions` tab.
   - Check the logs for any errors or issues.

## 🛠 Troubleshooting

- **Workflow Not Visible**:
  - Ensure you have the necessary permissions to view and trigger workflows in the repository.
  - Check if the workflow file (`.github/workflows/deploy.yml`) exists in the repository.

- **Failed Deployment**:
  - Review the logs in the `Actions` tab to identify the issue.
  - Ensure all required secrets (e.g., `TELEGRAM_TOKEN`, `GITHUB_TOKEN`) are configured in the repository settings.

## 🔐 Required Permissions

To trigger a deployment, you need:
- Write access to the repository.
- Permissions to trigger GitHub Actions workflows.

## 📄 Related Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Managing Secrets in GitHub](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

Let me know if you'd like to customize this further or add specific details about your deployment workflow! 🚀
