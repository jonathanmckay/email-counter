# Email Counter

A tool to track email response times and generate daily reports.

## Features

- Tracks average email response time for emails you've responded to
- Sends daily reports via email
- Currently supports:
  - Gmail (personal accounts)
- Planned support:
  - Outlook
  - Work-managed Gmail accounts

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

### 5. Schedule Daily Reports

To run daily reports automatically, add to your crontab:

```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/email-counter && ./venv/bin/python email_reporter.py
```

Or use the system scheduler on your OS (Task Scheduler on Windows, launchd on macOS).

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
