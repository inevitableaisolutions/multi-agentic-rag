# Mobile App

## Overview

CloudSync Pro offers native mobile apps for iOS (version 15.0+) and Android (version 10+). Download from the Apple App Store or Google Play Store by searching "CloudSync Pro."

## Installation and Login

1. Download the app from your device's app store
2. Open the app and tap **Sign In**
3. Enter your workspace URL (e.g., `yourcompany.cloudsyncpro.com`)
4. Log in with your email/password or SSO credentials
5. If 2FA is enabled, enter your authentication code

Enterprise SSO users: Tap **Sign in with SSO** and enter your organization's SSO domain.

## Sync Issues

If data is not syncing between mobile and web:

1. **Check internet connection**: The app requires an active internet connection. Offline mode caches recent data but does not sync until reconnected.
2. **Force sync**: Pull down on any project or task list to trigger a manual sync
3. **Check app version**: Go to Settings > About in the app. Ensure you are running version 4.2.0 or later. Older versions have known sync bugs.
4. **Clear app cache**: Go to device Settings > Apps > CloudSync Pro > Storage > Clear Cache (Android) or delete and reinstall the app (iOS)
5. **Log out and log back in**: This forces a full data re-sync from the server

### Known Sync Issues
- **Task attachments**: Files attached on mobile may take up to 60 seconds to appear on web during high server load
- **Offline edits**: If two users edit the same task offline, the last sync wins. A conflict notification appears in the activity log.

## Push Notifications

To enable push notifications:

1. Open the CloudSync Pro app
2. Go to **Settings > Notifications**
3. Toggle on the notification categories you want: task assignments, comments, mentions, due date reminders
4. Ensure system-level notifications are enabled: device Settings > Notifications > CloudSync Pro > Allow Notifications

**Not receiving notifications?**
- Verify Do Not Disturb is off
- Check that battery optimization is not killing the app in the background (Android: Settings > Battery > CloudSync Pro > Unrestricted)
- Ensure you are not muted in the specific project's notification settings

## Troubleshooting Crashes

If the app crashes repeatedly:
1. Update to the latest version from the app store
2. Restart your device
3. Reinstall the app (your data is stored server-side and will not be lost)
4. Report persistent crashes to support@cloudsyncpro.com with your device model and OS version
