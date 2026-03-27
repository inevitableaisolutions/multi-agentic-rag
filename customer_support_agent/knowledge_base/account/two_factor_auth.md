# Two-Factor Authentication (2FA)

## Overview

Two-factor authentication adds an extra layer of security to your CloudSync Pro account. When enabled, you must provide both your password and a time-based one-time code (TOTP) to log in.

## Setting Up 2FA

1. Go to **Settings > Account > Security > Two-Factor Authentication**
2. Click **Enable 2FA**
3. Choose your method:
   - **Authenticator App** (recommended): Scan the QR code with Google Authenticator, Authy, 1Password, or any TOTP-compatible app
   - **SMS** (less secure): Enter your phone number to receive codes via text message
4. Enter the 6-digit verification code from your chosen method
5. Click **Verify and Enable**
6. **Save your backup codes** -- you will be shown 10 one-time backup codes. Store them in a secure location (password manager or printed in a safe place). Each code can only be used once.

## Using 2FA to Log In

1. Enter your email and password as usual
2. When prompted, enter the 6-digit code from your authenticator app
3. The code refreshes every 30 seconds. If the code is rejected, wait for a new one and try again.
4. Optionally, check **Trust this device for 30 days** to skip 2FA on subsequent logins from the same browser

## Backup Codes

Backup codes are for emergencies when you cannot access your authenticator app or phone:

- Each backup code is a 10-character alphanumeric string (format: `XXXXX-XXXXX`)
- Each code can be used exactly once
- You receive 10 codes when you first enable 2FA
- To generate new backup codes: Settings > Account > Security > 2FA > Regenerate Backup Codes (this invalidates all previous codes)

## Recovery When Locked Out

If you have lost access to your authenticator app and have no backup codes:

1. Go to the login page and click **Can't access your 2FA device?**
2. Enter your account email address
3. You will be asked to verify your identity through an email-based recovery process
4. Upload a government-issued photo ID for manual verification (processed within 24-48 hours)
5. Once verified, 2FA is temporarily disabled so you can log in and reconfigure it

For faster resolution, Enterprise customers can contact their workspace admin to reset 2FA on their behalf.

## Enforcing 2FA for Your Workspace

Admins on Pro and Enterprise plans can require 2FA for all workspace members:

1. Go to **Settings > Security > Authentication Policies**
2. Toggle **Require 2FA for all members**
3. Set a grace period (7, 14, or 30 days) for existing users to set up 2FA
4. Users without 2FA after the grace period are locked out until they enable it
