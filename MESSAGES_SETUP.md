# Messages Integration Setup Guide

This guide walks you through setting up Apple Messages integration for your daily email reports.

## Architecture Overview

```
Mac (5:30 AM) → Upload stats to GitHub Gist → GitHub Actions (5:31 AM) → Combined Email Report
```

## Prerequisites

- macOS with Messages app
- Full Disk Access granted to VS Code (or Terminal)
- GitHub account

## Part 1: Grant Full Disk Access

### For VS Code Users:

1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Click the 🔒 lock icon (enter password)
3. Click the **+** button
4. Press **Command + Shift + G** and navigate to where VS Code is installed:
   - If in Applications: `/Applications/Visual Studio Code.app`
   - If in Downloads: `/Users/yourusername/Downloads/Visual Studio Code.app`
5. Select **Visual Studio Code.app** and click **Open**
6. Make sure the checkbox is **ON**
7. **Completely quit and restart VS Code** (Command + Q)

### For Terminal Users:

Same steps but select `/Applications/Utilities/Terminal.app`

## Part 2: Create GitHub Personal Access Token

1. Go to: **https://github.com/settings/tokens**

2. Click **"Generate new token (classic)"**

3. Give it a name: **"Email Counter Messages Client"**

4. Set expiration: **No expiration** (or 1 year)

5. Select **only this scope:**
   - ✅ **gist** - Create gists

6. Click **"Generate token"**

7. **IMPORTANT:** Copy the token immediately (you won't see it again!)

8. Add it to your `.env` file:
   ```bash
   cd /Users/jonathanmckay/email-counter
   nano .env
   ```
   
   Add this line:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```

## Part 3: Test the Messages Client

```bash
cd /Users/jonathanmckay/email-counter
source venv/bin/activate
python messages_client.py
```

You should see:
- Messages being analyzed
- Stats summary (24h, 7d, 28d)
- Gist created and URL displayed
- Success message

## Part 4: Schedule Daily Runs

The Messages client needs to run daily at 5:30 AM (1 minute before the email report).

Create the launchd plist:

```bash
python setup_messages_scheduler.py
```

Activate it:

```bash
launchctl load ~/Library/LaunchAgents/com.emailcounter.messages.plist
```

Test immediately:

```bash
launchctl start com.emailcounter.messages
```

Check logs:

```bash
tail -f ~/Library/Logs/emailcounter-messages.log
```

## Part 5: Update GitHub Actions

The GitHub Actions workflow will automatically download the Messages stats from your Gist and include them in the daily report.

You'll need to add one more secret:

1. Go to: https://github.com/jonathanmckay/email-counter/settings/secrets/actions

2. Add a new secret:
   - **Name:** `MESSAGES_GIST_ID`
   - **Value:** The gist ID from `.messages_gist_id` file

To get the gist ID:
```bash
cat .messages_gist_id
```

## Part 6: Test End-to-End

1. **Run Messages client manually** (or wait until 5:30 AM):
   ```bash
   python messages_client.py
   ```

2. **Check the gist was created:**
   - Go to: https://gist.github.com
   - You should see "Email Counter - Messages Stats"

3. **Trigger GitHub Actions** (or wait until 5:31 AM):
   - Go to: https://github.com/jonathanmckay/email-counter/actions
   - Run workflow manually

4. **Check your email!**
   - You should receive a report showing:
     - 📱 Messages stats
     - 📧 Gmail stats
     - 📧 Outlook stats (if enabled)

## Troubleshooting

### "authorization denied" Error

**Solution:** Make sure you've granted Full Disk Access and **completely restarted** the application (VS Code/Terminal).

### "GITHUB_TOKEN environment variable not set"

**Solution:** 
1. Make sure you added `GITHUB_TOKEN=...` to your `.env` file
2. The token should start with `ghp_`
3. Restart your terminal/VS Code after adding it

### "Failed to upload to gist"

**Possible causes:**
- Token expired or invalid
- Token doesn't have `gist` scope
- Network connectivity issue

**Solution:** Create a new token with the `gist` scope.

### Gist is private - is that okay?

**Yes!** The gist is intentionally private so only you (and GitHub Actions with your token) can access it.

### Can I see what's in the gist?

**Yes!** Go to https://gist.github.com and look for "Email Counter - Messages Stats". It contains only:
- Response counts
- Average/median times
- No message content (privacy protected)

## Security Notes

- ✅ Message content is NOT uploaded, only statistics
- ✅ Gist is private (only you can see it)
- ✅ GitHub token is stored locally in `.env` (gitignored)
- ✅ All processing happens on your Mac
- ✅ Messages database is only accessed locally

## Uninstalling

To remove Messages integration:

```bash
# Stop the scheduler
launchctl unload ~/Library/LaunchAgents/com.emailcounter.messages.plist

# Delete the plist
rm ~/Library/LaunchAgents/com.emailcounter.messages.plist

# Delete the gist (optional)
# Go to https://gist.github.com, find it, and delete

# Remove from .env
# Delete the GITHUB_TOKEN line
```

## What Gets Uploaded to Gist

Example of what's stored (no sensitive data):

```json
{
  "last_24h": {
    "total_responses": 25,
    "avg_response_time_seconds": 900,
    "avg_response_time_formatted": "15 minutes",
    "imessage_count": 23,
    "sms_count": 2
  },
  "last_7d": {...},
  "last_28d": {...},
  "generated_at": "2025-10-17T05:30:00Z"
}
```

No message content, no phone numbers, no contact names!

