"""Apple Messages response time analyzer."""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz


class MessagesAnalyzer:
    """Analyzes Apple Messages for response times."""
    
    # Mac absolute time reference (seconds since 2001-01-01 00:00:00 UTC)
    MAC_EPOCH = datetime(2001, 1, 1, tzinfo=pytz.UTC)
    
    def __init__(self):
        """Initialize Messages analyzer."""
        self.db_path = os.path.expanduser("~/Library/Messages/chat.db")
        self.phone_number = None  # Will try to detect
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Messages database not found at {self.db_path}. "
                "Make sure you're running on macOS with Messages app."
            )
        
        print(f"✓ Found Messages database at {self.db_path}")
    
    @staticmethod
    def convert_mac_timestamp(mac_timestamp: float) -> datetime:
        """Convert Mac absolute time to datetime."""
        if mac_timestamp is None or mac_timestamp == 0:
            return None
        
        # Mac timestamps are in nanoseconds, convert to seconds
        timestamp_seconds = mac_timestamp / 1_000_000_000
        
        return MessagesAnalyzer.MAC_EPOCH + timedelta(seconds=timestamp_seconds)
    
    def get_messages_in_timeframe(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get all messages within a timeframe."""
        # Convert to Mac absolute time (nanoseconds)
        start_mac = int((start_date - self.MAC_EPOCH).total_seconds() * 1_000_000_000)
        end_mac = int((end_date - self.MAC_EPOCH).total_seconds() * 1_000_000_000)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Query messages with chat and handle information
        # Includes both text messages and reactions (associated_message_guid)
        query = """
        SELECT 
            m.ROWID,
            m.guid,
            m.text,
            m.date,
            m.date_read,
            m.is_from_me,
            m.cache_has_attachments,
            c.chat_identifier,
            c.service_name,
            h.id as handle_id,
            c.display_name,
            m.associated_message_guid,
            m.associated_message_type
        FROM message m
        JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
        JOIN chat c ON cmj.chat_id = c.ROWID
        LEFT JOIN handle h ON m.handle_id = h.ROWID
        WHERE m.date >= ? AND m.date <= ?
        AND m.date > 0
        ORDER BY c.chat_identifier, m.date ASC
        """
        
        cursor.execute(query, (start_mac, end_mac))
        
        messages = []
        for row in cursor.fetchall():
            msg_date = self.convert_mac_timestamp(row[3])
            
            # Check if this is a reaction
            is_reaction = row[11] is not None  # associated_message_guid
            reaction_type = row[12] if is_reaction else None
            
            # Determine message type for display
            if is_reaction:
                reaction_names = {
                    2000: 'Loved',
                    2001: 'Liked', 
                    2002: 'Disliked',
                    2003: 'Laughed',
                    2004: 'Emphasized',
                    2005: 'Questioned'
                }
                text = reaction_names.get(reaction_type, f'Reacted ({reaction_type})')
            else:
                text = row[2][:100] if row[2] else ''  # Truncate for privacy
            
            messages.append({
                'id': row[0],
                'guid': row[1],
                'text': text,
                'date': msg_date,
                'date_read': self.convert_mac_timestamp(row[4]),
                'is_from_me': bool(row[5]),
                'has_attachments': bool(row[6]),
                'chat_id': row[7],
                'service': row[8],  # iMessage or SMS
                'contact': row[9] or row[7],  # Handle ID or chat identifier
                'display_name': row[10],
                'is_reaction': is_reaction,
                'reaction_type': reaction_type
            })
        
        conn.close()
        
        return messages
    
    def analyze_response_times(self, days: int = 30, start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None) -> Dict:
        """Analyze message response times for the past N days or a specific date range."""
        
        # Calculate date range
        if end_date is None:
            end_date = datetime.now(pytz.UTC)
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        print(f"\nAnalyzing Messages...")
        print(f"Period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            # Get messages in timeframe (need wider range to catch full conversations)
            wider_start = start_date - timedelta(days=7)
            messages = self.get_messages_in_timeframe(wider_start, end_date)
            
            print(f"Found {len(messages)} messages")
            
            # Group messages by chat
            chats = {}
            for msg in messages:
                chat_id = msg['chat_id']
                if chat_id not in chats:
                    chats[chat_id] = []
                chats[chat_id].append(msg)
            
            print(f"Across {len(chats)} conversations")
            
            # Analyze response times
            response_times = []
            
            for chat_id, chat_messages in chats.items():
                # Sort by date
                chat_messages.sort(key=lambda m: m['date'])
                
                # Find response pairs: received message(s) followed by sent message(s)
                # We track the last received message and first sent message after it
                last_received = None
                
                for i, msg in enumerate(chat_messages):
                    if not msg['is_from_me']:
                        # This is a received message - update our "last received" marker
                        last_received = msg
                    elif msg['is_from_me'] and last_received:
                        # This is a sent message and we have a received message to respond to
                        # Only count if this is the FIRST sent message after received message(s)
                        # Check if previous message was from me (skip if so, already counted)
                        if i > 0 and chat_messages[i-1]['is_from_me']:
                            continue  # Skip - this is a follow-up message, not initial response
                        
                        # Only count if response was sent in our target date range
                        if start_date <= msg['date'] <= end_date:
                            response_time = msg['date'] - last_received['date']
                            
                            # Sanity check: ignore responses that seem unreasonably fast or slow
                            # (likely indicates conversation gaps, not actual responses)
                            response_seconds = response_time.total_seconds()
                            if response_seconds < 1:  # Less than 1 second - likely sync issue
                                continue
                            if response_seconds > 7 * 24 * 3600:  # More than 7 days - different conversation
                                continue
                            
                            response_times.append({
                                'received': last_received['date'],
                                'sent': msg['date'],
                                'response_time': response_time,
                                'contact': last_received['contact'],
                                'display_name': last_received['display_name'],
                                'service': last_received['service']
                            })
                        
                        # Clear last_received so we don't double-count
                        last_received = None
            
            print(f"Found {len(response_times)} responses")
            
            # Calculate statistics
            if response_times:
                total_seconds = sum(rt['response_time'].total_seconds() for rt in response_times)
                avg_seconds = total_seconds / len(response_times)
                
                # Calculate median
                sorted_times = sorted(rt['response_time'].total_seconds() for rt in response_times)
                median_seconds = sorted_times[len(sorted_times) // 2]
                
                # Count by service
                imessage_count = sum(1 for rt in response_times if rt['service'] == 'iMessage')
                sms_count = sum(1 for rt in response_times if rt['service'] == 'SMS')
                
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
                    'imessage_count': imessage_count,
                    'sms_count': sms_count,
                    'response_details': response_times,
                    'analysis_period_days': days,
                    'start_date': start_date,
                    'end_date': end_date,
                    'email_address': 'Messages',  # For compatibility with email analyzers
                    'generated_at': datetime.now(pytz.UTC)
                }
            else:
                return {
                    'total_responses': 0,
                    'message': 'No responses found in the specified period',
                    'analysis_period_days': days,
                    'start_date': start_date,
                    'end_date': end_date,
                    'email_address': 'Messages',
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
        """Analyze response times for previous calendar day (PT), 7d, and 28d periods."""
        now_utc = datetime.now(pytz.UTC)
        
        # Convert to Pacific Time to get the previous calendar day
        pacific = pytz.timezone('America/Los_Angeles')
        now_pt = now_utc.astimezone(pacific)
        
        # Previous calendar day in PT (yesterday 00:00:00 to 23:59:59 PT)
        yesterday_pt = now_pt - timedelta(days=1)
        stats_24h_start = yesterday_pt.replace(hour=0, minute=0, second=0, microsecond=0)
        stats_24h_end = yesterday_pt.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Convert back to UTC for the analysis
        stats_24h_start_utc = stats_24h_start.astimezone(pytz.UTC)
        stats_24h_end_utc = stats_24h_end.astimezone(pytz.UTC)
        
        stats_24h = self.analyze_response_times(start_date=stats_24h_start_utc, end_date=stats_24h_end_utc)
        stats_24h['period_name'] = f'Previous Day ({yesterday_pt.strftime("%Y-%m-%d")} PT)'
        
        # Last 7 days (rolling)
        stats_7d_start = now_utc - timedelta(days=7)
        stats_7d = self.analyze_response_times(start_date=stats_7d_start, end_date=now_utc)
        stats_7d['period_name'] = 'Last 7 Days'
        
        # Last 28 days (rolling)
        stats_28d_start = now_utc - timedelta(days=28)
        stats_28d = self.analyze_response_times(start_date=stats_28d_start, end_date=now_utc)
        stats_28d['period_name'] = 'Last 28 Days'
        
        return {
            'last_24h': stats_24h,
            'last_7d': stats_7d,
            'last_28d': stats_28d,
            'email_address': 'Messages',
            'generated_at': now
        }
    
    def print_report(self, stats: Dict):
        """Print analysis report to console."""
        print("\n" + "="*60)
        print("MESSAGES RESPONSE TIME ANALYSIS")
        print("="*60)
        
        if stats.get('total_responses', 0) == 0:
            print(f"\n{stats.get('message', 'No data available')}")
            return
        
        print(f"\nAnalysis Period: {stats['start_date'].strftime('%Y-%m-%d')} to {stats['end_date'].strftime('%Y-%m-%d')}")
        print(f"Total Responses: {stats['total_responses']}")
        print(f"  iMessage: {stats.get('imessage_count', 0)}")
        print(f"  SMS: {stats.get('sms_count', 0)}")
        print(f"\nAverage Response Time: {stats['avg_response_time_formatted']}")
        print(f"Median Response Time: {stats['median_response_time_formatted']}")
        print(f"Fastest Response: {self.format_duration(stats['fastest_response'])}")
        print(f"Slowest Response: {self.format_duration(stats['slowest_response'])}")
        
        print("\n" + "="*60)


def main():
    """Test the Messages analyzer."""
    try:
        print("Testing Messages Analyzer...")
        print("="*60)
        
        analyzer = MessagesAnalyzer()
        
        # Analyze last 7 days
        stats = analyzer.analyze_response_times(days=7)
        
        # Print report
        analyzer.print_report(stats)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nNote: You may need to grant Full Disk Access to Terminal:")
        print("1. System Preferences → Security & Privacy → Privacy")
        print("2. Select 'Full Disk Access'")
        print("3. Click the lock to make changes")
        print("4. Click '+' and add Terminal")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())



