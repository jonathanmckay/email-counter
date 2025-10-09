"""Configuration management for Email Counter."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration."""
    
    # Email settings
    REPORT_EMAIL = os.getenv('REPORT_EMAIL', '')
    GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS', '')
    
    # Analysis settings
    ANALYSIS_DAYS = int(os.getenv('ANALYSIS_DAYS', 30))
    
    # Report settings
    REPORT_TIME = os.getenv('REPORT_TIME', '05:30')
    
    # Gmail API settings
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    CREDENTIALS_FILE = 'credentials.json'
    TOKEN_FILE = 'token.json'
    
    # Outlook/Microsoft 365 settings
    OUTLOOK_ENABLED = os.getenv('OUTLOOK_ENABLED', 'false').lower() == 'true'
    OUTLOOK_CLIENT_ID = os.getenv('OUTLOOK_CLIENT_ID', '')
    OUTLOOK_TENANT_ID = os.getenv('OUTLOOK_TENANT_ID', 'common')
    OUTLOOK_SCOPES = ['Mail.Read']
    OUTLOOK_TOKEN_FILE = 'outlook_token.json'
    
    @classmethod
    def validate(cls):
        """Validate configuration."""
        if not cls.REPORT_EMAIL:
            raise ValueError("REPORT_EMAIL must be set in .env file")
        
        if not os.path.exists(cls.CREDENTIALS_FILE):
            raise ValueError(
                f"{cls.CREDENTIALS_FILE} not found. "
                "Please download OAuth credentials from Google Cloud Console."
            )
        
        # Validate Outlook settings if enabled
        if cls.OUTLOOK_ENABLED:
            if not cls.OUTLOOK_CLIENT_ID:
                raise ValueError(
                    "OUTLOOK_CLIENT_ID must be set in .env file when OUTLOOK_ENABLED=true"
                )
            if not cls.OUTLOOK_TENANT_ID:
                raise ValueError(
                    "OUTLOOK_TENANT_ID must be set in .env file when OUTLOOK_ENABLED=true"
                )
        
        return True

