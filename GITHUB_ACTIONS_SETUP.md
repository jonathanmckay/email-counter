# GitHub Actions Setup Guide

This guide will help you set up GitHub Actions to run your email counter automatically in the cloud (for free!).

## Prerequisites

- Your email-counter repository on GitHub
- Gmail authentication already working locally (you've run it successfully once)

## Step-by-Step Setup

### 1. Generate Tokens Locally (One Time)

First, make sure you have valid tokens by running the script locally:

```bash
cd /Users/jonathanmckay/email-counter
source venv/bin/activate
python email_reporter.py
```

This will create:
- `credentials.json` (Gmail OAuth credentials)
- `token.json` (Gmail access token)
- `outlook_token.json` (if Outlook is enabled)

### 2. Prepare Token Contents

Get the contents of your token files:

```bash
# Gmail credentials (from Google Cloud Console)
cat credentials.json | pbcopy
# This is now in your clipboard - save it somewhere temporarily

# Gmail token
cat token.json | pbcopy
# Save this too

# Outlook token (if using Outlook)
cat outlook_token.json | pbcopy
# Save this as well
```

### 3. Add GitHub Secrets

1. Go to your repository on GitHub: https://github.com/jonathanmckay/email-counter
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** for each of the following:

#### Required Secrets:

| Secret Name | Value | How to Get It |
|-------------|-------|---------------|
| `GMAIL_CREDENTIALS` | Contents of `credentials.json` | Copy entire JSON file contents |
| `GMAIL_TOKEN` | Contents of `token.json` | Copy entire JSON file contents |
| `REPORT_EMAIL` | Your email address | Example: `mckay@m5c7.com` |
| `GMAIL_ADDRESS` | Your Gmail address (or leave blank) | Leave blank to use authenticated account |
| `OUTLOOK_ENABLED` | `false` or `true` | Set to `false` for Gmail only |

#### Optional (for Outlook):

| Secret Name | Value |
|-------------|-------|
| `OUTLOOK_TOKEN` | Contents of `outlook_token.json` |
| `OUTLOOK_CLIENT_ID` | Your Azure AD Client ID |
| `OUTLOOK_TENANT_ID` | Your Azure AD Tenant ID |

### 4. Adjust Timezone (Optional)

The workflow runs at 5:30 AM **UTC** by default. To adjust for your timezone:

1. Calculate the UTC time for your desired local time
   - Example: 5:30 AM EST = 10:30 AM UTC
   - Example: 5:30 AM PST = 1:30 PM UTC (13:30)

2. Edit `.github/workflows/daily-report.yml`:
   ```yaml
   schedule:
     - cron: '30 10 * * *'  # 10:30 UTC = 5:30 AM EST
   ```

3. Commit and push the change

### 5. Test the Workflow

Before waiting for the scheduled run, test it manually:

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click **Daily Email Report** in the left sidebar
4. Click **Run workflow** button (top right)
5. Click the green **Run workflow** button

You should see:
- A new workflow run appear
- It completes successfully (green checkmark)
- You receive an email report!

### 6. Verify Scheduled Runs

The workflow will now run automatically every day at the scheduled time. To verify:

1. Go to **Actions** tab on GitHub
2. Check the **Daily Email Report** workflow runs
3. You'll receive an email every day at 5:30 AM (UTC)

## Troubleshooting

### "Error: Invalid credentials"

**Solution:** Re-generate your tokens locally and update the GitHub Secrets:
```bash
rm token.json
python email_reporter.py  # Re-authenticate
cat token.json | pbcopy   # Copy new token
# Update GMAIL_TOKEN secret on GitHub
```

### "No email received"

**Check:**
1. Go to **Actions** tab and look for errors
2. Verify `REPORT_EMAIL` secret is correct
3. Check your spam folder
4. Look at the workflow logs for error messages

### "Workflow didn't run at scheduled time"

**Note:** GitHub Actions scheduled workflows can be delayed by up to 15-30 minutes during high load periods. This is normal.

### Token Expiration

Gmail tokens can last for a long time (months/years) but may eventually expire. If this happens:

1. Run the script locally to re-authenticate
2. Copy the new `token.json` contents
3. Update the `GMAIL_TOKEN` secret on GitHub

## Cost

**GitHub Actions is FREE** for public repositories and includes:
- 2,000 minutes/month for private repos (more than enough for this)
- This script uses ~1 minute per day = ~30 minutes/month

## Security Notes

- Your tokens are stored as encrypted GitHub Secrets
- Only repository admins can see/edit secrets
- Secrets are not visible in workflow logs
- Consider using a private repository for extra security

## Disabling the Workflow

To temporarily stop the daily reports:

1. Go to **Actions** tab
2. Click **Daily Email Report** 
3. Click the **⋮** menu (top right)
4. Click **Disable workflow**

To re-enable, repeat and click **Enable workflow**.

## Advanced: Manual Token Refresh

If you want to handle token refresh automatically, you could:
1. Set up a separate workflow to refresh tokens
2. Use GitHub API to update secrets programmatically
3. Store tokens in a cloud key management service

But for most users, manually updating tokens every few months is simpler.

## Switching Back to Local Execution

If you want to switch back to running on your Mac:

1. Disable the GitHub Actions workflow (see above)
2. Re-enable the launchd scheduler:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.emailcounter.dailyreport.plist
   ```

