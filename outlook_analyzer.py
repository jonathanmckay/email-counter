"""Outlook email response time analyzer using Microsoft Graph API."""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz

import msal
from msgraph import GraphServiceClient
from msgraph.generated.models.message import Message
from msgraph.generated.users.item.messages.messages_request_builder import MessagesRequestBuilder
from azure.identity import DeviceCodeCredential
from kiota_abstractions.base_request_configuration import RequestConfiguration

from config import Config


class OutlookAnalyzer:
    """Analyzes Outlook for email response times using Microsoft Graph API."""
    
    def __init__(self):
        """Initialize Outlook analyzer."""
        self.client = None
        self.email_address = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Microsoft Graph API using device code flow."""
        # Load existing token if available
        cache = msal.SerializableTokenCache()
        if os.path.exists(Config.OUTLOOK_TOKEN_FILE):
            with open(Config.OUTLOOK_TOKEN_FILE, 'r') as f:
                cache.deserialize(f.read())
        
        # Create MSAL app
        app = msal.PublicClientApplication(
            Config.OUTLOOK_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{Config.OUTLOOK_TENANT_ID}",
            token_cache=cache
        )
        
        # Try to get token silently first
        accounts = app.get_accounts()
        result = None
        
        if accounts:
            result = app.acquire_token_silent(Config.OUTLOOK_SCOPES, account=accounts[0])
        
        # If no cached token, use device code flow
        if not result:
            flow = app.initiate_device_flow(scopes=Config.OUTLOOK_SCOPES)
            
            if "user_code" not in flow:
                raise ValueError("Failed to create device flow")
            
            print("\n" + "="*60)
            print("MICROSOFT OUTLOOK AUTHENTICATION")
            print("="*60)
            print(f"\n{flow['message']}")
            print("\nWaiting for authentication...")
            
            result = app.acquire_token_by_device_flow(flow)
        
        if "access_token" not in result:
            raise ValueError(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
        
        # Save token cache
        if cache.has_state_changed:
            with open(Config.OUTLOOK_TOKEN_FILE, 'w') as f:
                f.write(cache.serialize())
        
        # Store access token and user info
        self.access_token = result['access_token']
        self.email_address = result.get('id_token_claims', {}).get('preferred_username', 'Unknown')
        
        print(f"✓ Successfully authenticated with Outlook: {self.email_address}")
    
    def _get_messages(self, start_date: datetime, end_date: datetime, filter_query: str) -> List[Dict]:
        """Get messages using Microsoft Graph API."""
        import requests
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Format dates for OData filter
        start_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Build filter with date range
        full_filter = f"{filter_query} and sentDateTime ge {start_str} and sentDateTime le {end_str}"
        
        url = 'https://graph.microsoft.com/v1.0/me/messages'
        params = {
            '$filter': full_filter,
            '$select': 'id,conversationId,subject,from,toRecipients,sentDateTime,receivedDateTime,isRead,isDraft',
            '$top': 500,
            '$orderby': 'sentDateTime desc'
        }
        
        messages = []
        while url:
            response = requests.get(url, headers=headers, params=params if url == 'https://graph.microsoft.com/v1.0/me/messages' else None)
            
            if response.status_code != 200:
                print(f"Error fetching messages: {response.status_code} - {response.text}")
                break
            
            data = response.json()
            messages.extend(data.get('value', []))
            
            # Get next page if available
            url = data.get('@odata.nextLink')
            params = None  # Next link includes all params
        
        return messages
    
    def _get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages in a conversation."""
        import requests
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = 'https://graph.microsoft.com/v1.0/me/messages'
        params = {
            '$filter': f"conversationId eq '{conversation_id}'",
            '$select': 'id,conversationId,subject,from,toRecipients,sentDateTime,receivedDateTime,isRead,isDraft',
            '$orderby': 'receivedDateTime asc',
            '$top': 100
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        return data.get('value', [])
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse ISO 8601 date string from Graph API."""
        try:
            # Graph API returns dates in ISO 8601 format
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.astimezone(pytz.UTC)
        except (ValueError, AttributeError):
            return None
    
    def _is_sent_by_me(self, message: Dict) -> bool:
        """Check if message was sent by the authenticated user."""
        from_addr = message.get('from', {}).get('emailAddress', {}).get('address', '').lower()
        return from_addr == self.email_address.lower()
    
    def analyze_response_times(self, days: int = 30, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Analyze email response times for the past N days or a specific date range."""
        if not self.email_address:
            return {}
        
        # Calculate date range
        if end_date is None:
            end_date = datetime.now(pytz.UTC)
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        print(f"\nAnalyzing Outlook emails for: {self.email_address}")
        print(f"Period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            # Get sent messages in the date range (need wider range to catch conversations)
            wider_start = start_date - timedelta(days=30)
            sent_filter = "isDraft eq false"
            sent_messages = self._get_messages(wider_start, end_date, sent_filter)
            
            # Filter to only messages sent by me
            my_sent_messages = [msg for msg in sent_messages if self._is_sent_by_me(msg)]
            
            print(f"Found {len(my_sent_messages)} sent messages")
            
            response_times = []
            analyzed_conversations = set()
            
            for sent_msg in my_sent_messages:
                sent_date = self._parse_date(sent_msg.get('sentDateTime', ''))
                if not sent_date or sent_date < start_date or sent_date > end_date:
                    continue
                
                conversation_id = sent_msg.get('conversationId')
                if not conversation_id or conversation_id in analyzed_conversations:
                    continue
                
                analyzed_conversations.add(conversation_id)
                
                # Get all messages in this conversation
                conversation_msgs = self._get_conversation_messages(conversation_id)
                
                if len(conversation_msgs) < 2:
                    continue
                
                # Sort by received date
                conversation_msgs.sort(key=lambda m: self._parse_date(m.get('receivedDateTime', '')) or datetime.min.replace(tzinfo=pytz.UTC))
                
                # Find response pairs: received message followed by sent message
                for i in range(len(conversation_msgs) - 1):
                    current_msg = conversation_msgs[i]
                    next_msg = conversation_msgs[i + 1]
                    
                    current_is_received = not self._is_sent_by_me(current_msg)
                    next_is_sent = self._is_sent_by_me(next_msg)
                    
                    if current_is_received and next_is_sent:
                        received_date = self._parse_date(current_msg.get('receivedDateTime', ''))
                        sent_response_date = self._parse_date(next_msg.get('sentDateTime', ''))
                        
                        if received_date and sent_response_date:
                            # Only include if the response was sent in our target date range
                            if start_date <= sent_response_date <= end_date:
                                response_time = sent_response_date - received_date
                                
                                response_times.append({
                                    'received': received_date,
                                    'sent': sent_response_date,
                                    'response_time': response_time,
                                    'subject': current_msg.get('subject', 'No subject'),
                                    'from': current_msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                                })
            
            print(f"Analyzed {len(analyzed_conversations)} email conversations")
            print(f"Found {len(response_times)} responses")
            
            # Calculate statistics
            if response_times:
                total_seconds = sum(rt['response_time'].total_seconds() for rt in response_times)
                avg_seconds = total_seconds / len(response_times)
                
                # Calculate median
                sorted_times = sorted(rt['response_time'].total_seconds() for rt in response_times)
                median_seconds = sorted_times[len(sorted_times) // 2]
                
                return {
                    'total_responses': len(response_times),
                    'avg_response_time_seconds': avg_seconds,
                    'avg_response_time_hours': avg_seconds / 3600,
                    'avg_response_time_formatted': self.format_duration(avg_seconds),
                    'median_response_time_seconds': median_seconds,
                    'median_response_time_hours': median_seconds / 3600,
                    'median_response_time_formatted': self.format_duration(median_seconds),
                    'fastest_response': min(rt['response_time'].total_seconds() for rt in response_times),
                    'slowest_response': max(rt['response_time'].total_seconds() for rt in response_times),
                    'response_details': response_times,
                    'analysis_period_days': days,
                    'start_date': start_date,
                    'end_date': end_date,
                    'email_address': self.email_address,
                    'generated_at': datetime.now(pytz.UTC)
                }
            else:
                return {
                    'total_responses': 0,
                    'message': 'No responses found in the specified period',
                    'analysis_period_days': days,
                    'start_date': start_date,
                    'end_date': end_date,
                    'email_address': self.email_address,
                    'generated_at': datetime.now(pytz.UTC)
                }
        
        except Exception as error:
            print(f"An error occurred: {error}")
            import traceback
            traceback.print_exc()
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
    
    def analyze_multi_period(self) -> Dict:
        """Analyze response times for 24h, 7d, and 28d periods."""
        now = datetime.now(pytz.UTC)
        
        # Last 24 hours
        stats_24h_start = now - timedelta(hours=24)
        stats_24h = self.analyze_response_times(start_date=stats_24h_start, end_date=now)
        stats_24h['period_name'] = 'Last 24 Hours'
        
        # Last 7 days
        stats_7d_start = now - timedelta(days=7)
        stats_7d = self.analyze_response_times(start_date=stats_7d_start, end_date=now)
        stats_7d['period_name'] = 'Last 7 Days'
        
        # Last 28 days
        stats_28d_start = now - timedelta(days=28)
        stats_28d = self.analyze_response_times(start_date=stats_28d_start, end_date=now)
        stats_28d['period_name'] = 'Last 28 Days'
        
        return {
            'last_24h': stats_24h,
            'last_7d': stats_7d,
            'last_28d': stats_28d,
            'email_address': stats_24h.get('email_address', ''),
            'generated_at': now
        }

