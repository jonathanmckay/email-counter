# Quick Start Guide

## 1. Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Name it "Email Counter"
   - Download the JSON file
   - Rename it to `credentials.json` and place it in this directory

## 2. Install Dependencies

```bash
cd /Users/jonathanmckay/email-counter

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or on Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your email address
nano .env  # or use your preferred editor
```

Update these values in `.env`:
- `REPORT_EMAIL`: Your email address where you want to receive daily reports
- `ANALYSIS_DAYS`: Number of days to analyze (default: 30)

## 4. First Run - Test It Out

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the analyzer (this will prompt you to authorize the app)
python gmail_analyzer.py
```

On first run:
1. A browser window will open
2. Sign in with your Google account
3. Grant the requested permissions (read-only access to Gmail)
4. The app will save your credentials locally

You should see a report with your email response statistics!

## 5. Send Test Report

```bash
python email_reporter.py
```

This will:
1. Analyze your emails
2. Generate an HTML report
3. Send it to the email address in your `.env` file

## 6. Schedule Daily Reports (Optional)

### macOS (using launchd):

```bash
python setup_scheduler.py

# Then activate it:
launchctl load ~/Library/LaunchAgents/com.emailcounter.dailyreport.plist

# Test it immediately:
launchctl start com.emailcounter.dailyreport
```

### Linux (using cron):

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM):
0 9 * * * cd /Users/jonathanmckay/email-counter && ./venv/bin/python email_reporter.py >> emailcounter.log 2>&1
```

### Windows (using Task Scheduler):

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 9:00 AM
4. Action: Start a program
   - Program: `C:\path\to\email-counter\venv\Scripts\python.exe`
   - Arguments: `email_reporter.py`
   - Start in: `C:\path\to\email-counter`

## Troubleshooting

### "credentials.json not found"
- Make sure you downloaded the OAuth credentials from Google Cloud Console
- Rename the file to exactly `credentials.json`
- Place it in the email-counter directory

### "REPORT_EMAIL must be set"
- Edit the `.env` file and set your email address
- Make sure there's no `.env.example` being read instead

### "Permission denied" errors
- Make sure your virtual environment is activated
- Check file permissions: `chmod +x gmail_analyzer.py email_reporter.py`

### No emails found
- Try increasing `ANALYSIS_DAYS` in `.env`
- Make sure you've actually responded to emails in that period
- Check that you're analyzing the correct Gmail account

## What Gets Tracked?

The analyzer looks for:
- Emails you sent that were replies to received emails
- Calculates the time between when you received an email and when you sent your response
- Only counts emails you actually responded to (ignores emails you never replied to)
- Provides average, median, fastest, and slowest response times

## Privacy & Security

- Your credentials are stored locally in `token.json`
- The app only reads email metadata (dates, senders, subjects)
- Email content is NOT read or stored
- All analysis happens on your computer
- No data is sent to external servers (except Google's Gmail API)


