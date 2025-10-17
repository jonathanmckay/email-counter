# Email Counter

A tool to track email response times and generate daily reports.

## Features

- Tracks average response time for messages you've responded to
- Sends daily reports via email
- Runs automatically in the cloud (GitHub Actions) with hybrid Mac client
- Currently supports:
  - **Gmail** (personal accounts)
  - **Microsoft 365 / Outlook** (work accounts)
  - **Apple Messages** (iMessage & SMS via Mac client)
- Combined reports showing breakouts by platform (Messages, Gmail, Outlook)

## Setup

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download the credentials JSON file and save it as `credentials.json` in this directory

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

Edit `.env` with your email address for receiving reports.

### 4. First Run

```bash
python gmail_analyzer.py
```

On first run, you'll be prompted to authorize the application in your browser.

### 5. Apple Messages Setup (Optional)

To include iMessage/SMS response times in your reports:

1. See [MESSAGES_SETUP.md](MESSAGES_SETUP.md) for detailed setup instructions
2. The Mac client runs locally and uploads stats to a private GitHub Gist
3. The GitHub Actions server downloads and combines with email stats
4. Requires:
   - Mac with Full Disk Access for Terminal/VS Code
   - GitHub Personal Access Token (with `gist` scope)
   - launchd scheduler to run daily

### 6. Outlook/M365 Setup (Optional)

To include Microsoft 365/Outlook response times:

1. See [OUTLOOK_SETUP.md](OUTLOOK_SETUP.md) for Azure AD app registration
2. Requires IT assistance for Service Tree ID
3. Set environment variables:
   - `OUTLOOK_ENABLED=true`
   - `OUTLOOK_CLIENT_ID=your_client_id`
   - `OUTLOOK_TENANT_ID=your_tenant_id`

### 7. Schedule Daily Reports

#### Option A: GitHub Actions (Recommended - Free Cloud Execution)

Run automatically in the cloud for free using GitHub Actions:

1. See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for detailed instructions
2. Set up GitHub Secrets with your tokens
3. The workflow runs daily at 5:30 AM UTC
4. No need to keep your computer on!

#### Option B: Local Execution (macOS)

To run on your Mac using launchd:

```bash
python setup_scheduler.py
launchctl load ~/Library/LaunchAgents/com.emailcounter.dailyreport.plist
```

See documentation for other platforms (cron on Linux, Task Scheduler on Windows).

## Usage

### Analyze Email Response Times

```bash
python gmail_analyzer.py
```

This will analyze your emails and display average response times.

### Send Daily Report

```bash
python email_reporter.py
```

This will generate a report and email it to the configured address.

## Files

- `gmail_analyzer.py` - Gmail integration and analysis
- `email_reporter.py` - Daily report generation and sending
- `config.py` - Configuration management
- `credentials.json` - Gmail API credentials (you must create this)
- `.env` - Environment variables (create from `.env.example`)

## How It Works

1. Connects to Gmail API using OAuth 2.0
2. Fetches sent emails from your account
3. For each sent email, finds the original email it was replying to
4. Calculates the time difference between receiving and responding
5. Computes average response time across all responded emails
6. Generates a report and sends it to your email

## Privacy & Security

- Your credentials are stored locally and never shared
- The app only reads your email metadata (sender, timestamp, subject)
- Email content is not analyzed or stored
- All processing happens locally on your machine

