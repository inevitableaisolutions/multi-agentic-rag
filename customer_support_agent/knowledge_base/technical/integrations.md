# Integrations

## Overview

CloudSync Pro integrates with popular tools to streamline your workflow. Integrations are available on Pro and Enterprise plans. Configure them at **Settings > Integrations**.

## Slack Integration

### Setup
1. Go to **Settings > Integrations > Slack**
2. Click **Connect to Slack** and authorize CloudSync Pro in your Slack workspace
3. Select a default channel for notifications or configure per-project channels

### Features
- Receive task assignments, comments, and status changes in Slack channels
- Create tasks from Slack messages using the `/cloudsync create` command
- Update task status with `/cloudsync update [task-id] status:[status]`
- Link Slack threads to CloudSync Pro tasks for context

### Troubleshooting
- **"Slack integration disconnected"**: Re-authorize at Settings > Integrations > Slack > Reconnect. This happens when Slack tokens expire or workspace permissions change.
- **Missing notifications**: Verify the bot is invited to the target channel (`/invite @CloudSync Pro`)
- **Error `SLACK_CHANNEL_NOT_FOUND`**: The configured channel was deleted or renamed. Update the channel mapping in integration settings.

## Jira Integration

### Setup
1. Go to **Settings > Integrations > Jira**
2. Enter your Jira instance URL (e.g., `yourcompany.atlassian.net`)
3. Authenticate with your Atlassian account
4. Map Jira projects to CloudSync Pro projects

### Features
- Two-way sync: Changes in either platform reflect in the other within 2 minutes
- Map Jira issue types to CloudSync Pro task types
- Sync status, assignee, priority, and custom fields
- Import existing Jira issues into CloudSync Pro

### Troubleshooting
- **Sync delay over 5 minutes**: Check **Settings > Integrations > Jira > Sync Log** for errors
- **Error `JIRA_AUTH_EXPIRED`**: Re-authenticate your Atlassian account
- **Field mapping issues**: Ensure custom fields exist in both platforms with compatible types

## GitHub Integration

### Setup
1. Go to **Settings > Integrations > GitHub**
2. Click **Connect to GitHub** and authorize the CloudSync Pro GitHub App
3. Select repositories to link

### Features
- Link pull requests and commits to tasks using task IDs in branch names or commit messages (format: `CSP-1234`)
- Automatic task status updates when PRs are opened, merged, or closed
- View commit history and PR status directly on task cards

### Troubleshooting
- **Commits not linking**: Ensure the task ID format `CSP-XXXX` appears in the commit message or branch name
- **Error `GH_WEBHOOK_FAILED`**: Check that the webhook URL is accessible. Go to your GitHub repo Settings > Webhooks and verify the CloudSync Pro webhook shows a green checkmark.
