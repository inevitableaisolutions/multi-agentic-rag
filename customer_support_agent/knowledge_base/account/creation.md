# Account Creation

## Creating a New Account

To create a CloudSync Pro account:

1. Visit **app.cloudsyncpro.com/signup**
2. Enter your full name, work email address, and choose a password
3. Password requirements: minimum 12 characters, at least one uppercase letter, one number, and one special character
4. Click **Create Account**
5. Verify your email by clicking the link in the confirmation email (sent within 2 minutes)
6. After verification, you will be guided through workspace setup

You can also sign up using **Google**, **Microsoft**, or **GitHub** OAuth. Click the corresponding button on the signup page to authenticate with your existing account.

## Creating a Workspace

Every CloudSync Pro account belongs to at least one workspace. When you first sign up, you will create your primary workspace:

- **Workspace Name**: Your company or team name (can be changed later)
- **Workspace URL**: A unique subdomain like `yourcompany.cloudsyncpro.com` (cannot be changed after creation)
- **Workspace Type**: Choose "Business" or "Personal" to set default settings

You can create additional workspaces from **Settings > Workspaces > Create New**.

## Team Invitations

Admins can invite team members in several ways:

1. **Email invitation**: Settings > Members > Invite. Enter email addresses and assign roles.
2. **Invite link**: Generate a shareable link at Settings > Members > Invite Link. Anyone with the link can join with a default role (configurable). Links can be set to expire after 7, 14, or 30 days.
3. **Domain auto-join**: Enable at Settings > Security > Domain Auto-Join. Anyone with a verified `@yourcompany.com` email can join the workspace automatically.

## Single Sign-On (SSO) Setup

SSO is available on Enterprise plans:

1. Go to **Settings > Security > SSO Configuration**
2. Select your identity provider: Okta, Azure AD, Google Workspace, OneLogin, or Custom SAML 2.0
3. Enter your IdP metadata URL or upload the metadata XML file
4. Configure attribute mappings (email, first name, last name, role)
5. Test the SSO connection with **Test SSO Login**
6. Enable SSO enforcement to require all users to authenticate via SSO

SSO support contact: sso-support@cloudsyncpro.com
