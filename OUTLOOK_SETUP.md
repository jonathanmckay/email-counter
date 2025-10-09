# Outlook / Microsoft 365 Setup Guide

This guide will help you set up Outlook integration with the Email Counter app using Microsoft Graph API.

## Prerequisites

- A Microsoft 365 (work/school) or Outlook.com account
- Access to Azure AD Portal (for M365 work accounts)
- Admin consent may be required for work accounts

## Step-by-Step Setup

### 1. Register Application in Azure AD

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **+ New registration**

### 2. Configure Application

**Application Name:**
- Name: `Email Counter` (or any name you prefer)

**Supported account types:**
- For M365 work account: Select "Accounts in this organizational directory only"
- For personal Outlook.com: Select "Accounts in any organizational directory and personal Microsoft accounts"

**Redirect URI:**
- Platform: Select "Public client/native (mobile & desktop)"
- Redirect URI: `http://localhost`


-URL is Here: https://ms.portal.azure.com/#view/Microsoft_AAD_RegisteredApps/CreateApplicationBlade/quickStartType~/null/isMSAApp~/false -- **Need to work with Microsoft IT in order to get a Service TRee ID**


Click **Register**






### 3. Note Your Application IDs

After registration, you'll see the application overview page. Copy these values:

- **Application (client) ID** - You'll need this for `OUTLOOK_CLIENT_ID`
- **Directory (tenant) ID** - You'll need this for `OUTLOOK_TENANT_ID`

### 4. Configure API Permissions

1. In your app registration, go to **API permissions** (left sidebar)
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Select **Delegated permissions**
5. Search for and add these permissions:
   - `Mail.Read` - Read user mail
6. Click **Add permissions**

### 5. Grant Admin Consent (Work Accounts Only)

If you're using a work/school M365 account:

1. In the **API permissions** page, click **Grant admin consent for [Your Organization]**
2. Click **Yes** to confirm
3. The status should change to show a green checkmark

> **Note:** If you don't have admin rights, ask your IT administrator to grant consent.

### 6. Update Configuration

Edit your `.env` file in the email-counter directory:

```bash
# Enable Outlook integration
OUTLOOK_ENABLED=true

# Application (client) ID from step 3
OUTLOOK_CLIENT_ID=your-client-id-here

# Directory (tenant) ID from step 3
OUTLOOK_TENANT_ID=your-tenant-id-here
```

For personal Outlook.com accounts, use:
```bash
OUTLOOK_TENANT_ID=common
```

### 7. Install Updated Dependencies

```bash
cd /Users/jonathanmckay/email-counter
source venv/bin/activate
pip install -r requirements.txt
```

### 8. Test Authentication

Run the email reporter to test:

```bash
python email_reporter.py
```

On first run:
1. You'll see a message with a device code and URL
2. Open the URL in your browser
3. Enter the device code shown in the terminal
4. Sign in with your Microsoft account
5. Grant the requested permissions
6. The app will save your token for future use

### 9. Verify Combined Report

Check your email (`REPORT_EMAIL` in `.env`) for a combined report showing:
- Gmail (m5c7.com) response times
- Outlook (Microsoft domain) response times
- Combined totals and breakouts

## Troubleshooting

### "AADSTS65001: The user or administrator has not consented"

**Solution:** Grant admin consent in Azure AD (Step 5) or have an admin do it.

### "AADSTS50076: Due to a configuration change made by your administrator..."

**Solution:** Your organization requires MFA. The device code flow supports MFA - just follow the authentication prompts.

### "Invalid client secret" or "Invalid client"

**Solution:** Double-check your `OUTLOOK_CLIENT_ID` and `OUTLOOK_TENANT_ID` in `.env` file.

### Authentication works but no emails found

**Possible causes:**
- You haven't sent any response emails in the analyzed period
- Check that you're analyzing the correct date range
- Verify the account has sent/received emails

### Token expired errors

**Solution:** Delete `outlook_token.json` and re-authenticate:
```bash
rm outlook_token.json
python email_reporter.py
```

## Security Notes

- The app only requests `Mail.Read` permission (read-only access)
- No email content is read or stored, only metadata (dates, senders, subjects)
- Authentication tokens are stored locally in `outlook_token.json`
- Tokens are excluded from git via `.gitignore`
- All processing happens on your local machine

## Permissions Requested

| Permission | Type | Reason |
|------------|------|--------|
| Mail.Read | Delegated | Read your mailbox to analyze sent/received message timing |

The app **does not** request:
- Mail.ReadWrite (no modifications to your mail)
- Mail.Send (cannot send emails on your behalf)
- Contacts or Calendar access

## Disabling Outlook Integration

To disable Outlook and only use Gmail:

1. Edit `.env` file:
   ```bash
   OUTLOOK_ENABLED=false
   ```

2. Reports will only show Gmail statistics

## Additional Resources

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/overview)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [Azure AD App Registration](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)

