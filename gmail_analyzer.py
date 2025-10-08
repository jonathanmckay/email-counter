"""Gmail email response time analyzer."""

import os
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import Config


class GmailAnalyzer:
    """Analyzes Gmail for email response times."""
    
    def __init__(self):
        """Initialize Gmail analyzer."""
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        # Load existing token
        if os.path.exists(Config.TOKEN_FILE):
            with open(Config.TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.CREDENTIALS_FILE, Config.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(Config.TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✓ Successfully authenticated with Gmail")
    
    def get_email_address(self) -> str:
        """Get the authenticated user's email address."""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile['emailAddress']
        except HttpError as error:
            print(f"Error getting profile: {error}")
            return ""
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse email date header."""
        try:
            # Gmail internal date is in milliseconds since epoch
            timestamp = int(date_str) / 1000
            return datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        except (ValueError, TypeError):
            return None
    
    def get_thread_messages(self, thread_id: str) -> List[Dict]:
        """Get all messages in a thread, sorted by date."""
        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id,
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date', 'In-Reply-To', 'Message-ID']
            ).execute()
            
            messages = thread.get('messages', [])
            
            # Parse and sort by internal date
            parsed_messages = []
            for msg in messages:
                date = self.parse_date(msg['internalDate'])
                if date:
                    parsed_messages.append({
                        'id': msg['id'],
                        'date': date,
                        'headers': {h['name']: h['value'] for h in msg['payload']['headers']},
                        'labelIds': msg.get('labelIds', [])
                    })
            
            parsed_messages.sort(key=lambda x: x['date'])
            return parsed_messages
            
        except HttpError as error:
            print(f"Error fetching thread {thread_id}: {error}")
            return []
    
    def analyze_response_times(self, days: int = 30) -> Dict:
        """Analyze email response times for the past N days."""
        email_address = self.get_email_address()
        if not email_address:
            return {}
        
        print(f"\nAnalyzing emails for: {email_address}")
        print(f"Looking back {days} days...")
        
        # Calculate date range
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=days)
        
        # Query for sent emails
        query = f'from:me after:{start_date.strftime("%Y/%m/%d")}'
        
        response_times = []
        analyzed_threads = set()
        
        try:
            # Get sent messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=500
            ).execute()
            
            messages = results.get('messages', [])
            print(f"Found {len(messages)} sent messages")
            
            for msg_ref in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=msg_ref['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject']
                ).execute()
                
                thread_id = msg['threadId']
                
                # Skip if we already analyzed this thread
                if thread_id in analyzed_threads:
                    continue
                
                analyzed_threads.add(thread_id)
                
                # Get all messages in thread
                thread_messages = self.get_thread_messages(thread_id)
                
                if len(thread_messages) < 2:
                    continue
                
                # Find response pairs: incoming message followed by our sent message
                for i in range(len(thread_messages) - 1):
                    current_msg = thread_messages[i]
                    next_msg = thread_messages[i + 1]
                    
                    # Check if current is received and next is sent
                    current_is_received = 'SENT' not in current_msg['labelIds']
                    next_is_sent = 'SENT' in next_msg['labelIds']
                    
                    if current_is_received and next_is_sent:
                        # Calculate response time
                        response_time = next_msg['date'] - current_msg['date']
                        response_times.append({
                            'received': current_msg['date'],
                            'sent': next_msg['date'],
                            'response_time': response_time,
                            'subject': current_msg['headers'].get('Subject', 'No subject'),
                            'from': current_msg['headers'].get('From', 'Unknown')
                        })
            
            print(f"Analyzed {len(analyzed_threads)} email threads")
            print(f"Found {len(response_times)} responses")
            
            # Calculate statistics
            if response_times:
                total_seconds = sum(rt['response_time'].total_seconds() for rt in response_times)
                avg_seconds = total_seconds / len(response_times)
                
                # Convert to hours and minutes
                avg_hours = avg_seconds / 3600
                avg_minutes = (avg_seconds % 3600) / 60
                
                # Calculate median
                sorted_times = sorted(rt['response_time'].total_seconds() for rt in response_times)
                median_seconds = sorted_times[len(sorted_times) // 2]
                median_hours = median_seconds / 3600
                
                return {
                    'total_responses': len(response_times),
                    'avg_response_time_seconds': avg_seconds,
                    'avg_response_time_hours': avg_hours,
                    'avg_response_time_formatted': self.format_duration(avg_seconds),
                    'median_response_time_seconds': median_seconds,
                    'median_response_time_hours': median_hours,
                    'median_response_time_formatted': self.format_duration(median_seconds),
                    'fastest_response': min(rt['response_time'].total_seconds() for rt in response_times),
                    'slowest_response': max(rt['response_time'].total_seconds() for rt in response_times),
                    'response_details': response_times,
                    'analysis_period_days': days,
                    'email_address': email_address,
                    'generated_at': datetime.now(pytz.UTC)
                }
            else:
                return {
                    'total_responses': 0,
                    'message': 'No responses found in the specified period',
                    'analysis_period_days': days,
                    'email_address': email_address,
                    'generated_at': datetime.now(pytz.UTC)
                }
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return {}
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} min"
        else:
            days = int(seconds / 86400)
            hours = int((seconds % 86400) / 3600)
            return f"{days} day{'s' if days != 1 else ''} {hours} hour{'s' if hours != 1 else ''}"
    
    def print_report(self, stats: Dict):
        """Print analysis report to console."""
        print("\n" + "="*60)
        print("EMAIL RESPONSE TIME ANALYSIS")
        print("="*60)
        
        if stats.get('total_responses', 0) == 0:
            print(f"\n{stats.get('message', 'No data available')}")
            return
        
        print(f"\nEmail Account: {stats['email_address']}")
        print(f"Analysis Period: Last {stats['analysis_period_days']} days")
        print(f"Total Responses: {stats['total_responses']}")
        print(f"\nAverage Response Time: {stats['avg_response_time_formatted']}")
        print(f"Median Response Time: {stats['median_response_time_formatted']}")
        print(f"Fastest Response: {self.format_duration(stats['fastest_response'])}")
        print(f"Slowest Response: {self.format_duration(stats['slowest_response'])}")
        
        print("\n" + "="*60)


def main():
    """Main entry point."""
    try:
        # Validate configuration
        Config.validate()
        
        # Create analyzer
        analyzer = GmailAnalyzer()
        
        # Analyze emails
        stats = analyzer.analyze_response_times(days=Config.ANALYSIS_DAYS)
        
        # Print report
        analyzer.print_report(stats)
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

