"""Todoist task completion analyzer."""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz
from config import Config


class TodoistAnalyzer:
    """Analyzes Todoist task completion times and latency."""
    
    def __init__(self):
        """Initialize Todoist analyzer."""
        self.api_token = Config.TODOIST_API_TOKEN
        if not self.api_token:
            raise ValueError("TODOIST_API_TOKEN not set in environment")
        
        self.base_url = "https://api.todoist.com/sync/v9"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
    
    def get_completed_tasks(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get completed tasks within a date range."""
        # Todoist API uses UTC timestamps
        since = start_date.isoformat()
        until = end_date.isoformat()
        
        # Use the sync API to get completed items
        url = f"{self.base_url}/completed/get_all"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params={
                    "since": since,
                    "until": until
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get('items', [])
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Todoist data: {e}")
            return []
    
    def analyze_completion_times(self, days: int = 1, start_date: Optional[datetime] = None, 
                                 end_date: Optional[datetime] = None) -> Dict:
        """Analyze task completion times and latency."""
        
        if end_date is None:
            end_date = datetime.now(pytz.UTC)
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        print(f"\nAnalyzing Todoist tasks...")
        print(f"Period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
        # Get completed tasks
        completed_tasks = self.get_completed_tasks(start_date, end_date)
        
        if not completed_tasks:
            return {
                'total_completed': 0,
                'message': 'No completed tasks in the specified period',
                'start_date': start_date,
                'end_date': end_date,
                'generated_at': datetime.now(pytz.UTC)
            }
        
        print(f"Found {len(completed_tasks)} completed tasks")
        
        # Calculate latency for tasks (time from creation to completion)
        task_details = []
        total_latency_seconds = 0
        tasks_with_latency = 0
        
        for task in completed_tasks:
            # Parse completion time
            completed_at_str = task.get('completed_at') or task.get('completed_date')
            if not completed_at_str:
                continue
            
            try:
                completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))
            except:
                continue
            
            # Get task content
            task_content = task.get('content', 'Unnamed task')
            
            # Try to get creation date from task metadata
            # Note: Todoist API might not always provide this in completed items
            added_at_str = task.get('added_at') or task.get('date_added')
            
            if added_at_str:
                try:
                    added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                    latency = completed_at - added_at
                    latency_seconds = latency.total_seconds()
                    
                    # Only count positive latencies (completed after created)
                    if latency_seconds > 0:
                        task_details.append({
                            'content': task_content[:50],  # Truncate for privacy
                            'completed_at': completed_at,
                            'created_at': added_at,
                            'latency': latency,
                            'latency_seconds': latency_seconds
                        })
                        total_latency_seconds += latency_seconds
                        tasks_with_latency += 1
                except:
                    pass
        
        # Calculate statistics
        stats = {
            'total_completed': len(completed_tasks),
            'tasks_with_latency': tasks_with_latency,
            'start_date': start_date,
            'end_date': end_date,
            'generated_at': datetime.now(pytz.UTC)
        }
        
        if tasks_with_latency > 0:
            avg_latency_seconds = total_latency_seconds / tasks_with_latency
            
            # Calculate median
            sorted_latencies = sorted(t['latency_seconds'] for t in task_details)
            median_latency_seconds = sorted_latencies[len(sorted_latencies) // 2]
            
            stats.update({
                'avg_latency_seconds': avg_latency_seconds,
                'avg_latency_hours': avg_latency_seconds / 3600,
                'avg_latency_formatted': self.format_duration(avg_latency_seconds),
                'median_latency_seconds': median_latency_seconds,
                'median_latency_formatted': self.format_duration(median_latency_seconds),
                'fastest_completion': min(t['latency_seconds'] for t in task_details),
                'slowest_completion': max(t['latency_seconds'] for t in task_details),
                'task_details': task_details
            })
        else:
            # Even if we don't have latency data, we know tasks were completed
            stats['message'] = f'{len(completed_tasks)} tasks completed (latency data not available)'
        
        return stats
    
    def analyze_multi_period(self) -> Dict:
        """Analyze task completions for previous calendar day (PT), 7d, and 28d periods."""
        now_utc = datetime.now(pytz.UTC)
        
        # Convert to Pacific Time to get the previous calendar day
        pacific = pytz.timezone('America/Los_Angeles')
        now_pt = now_utc.astimezone(pacific)
        
        # Previous calendar day in PT (yesterday 00:00:00 to 23:59:59 PT)
        yesterday_pt = now_pt - timedelta(days=1)
        stats_24h_start = yesterday_pt.replace(hour=0, minute=0, second=0, microsecond=0)
        stats_24h_end = yesterday_pt.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Convert back to UTC for the API calls
        stats_24h_start_utc = stats_24h_start.astimezone(pytz.UTC)
        stats_24h_end_utc = stats_24h_end.astimezone(pytz.UTC)
        
        stats_24h = self.analyze_completion_times(start_date=stats_24h_start_utc, end_date=stats_24h_end_utc)
        stats_24h['period_name'] = f'Previous Day ({yesterday_pt.strftime("%Y-%m-%d")} PT)'
        
        # Last 7 days (rolling)
        stats_7d_start = now_utc - timedelta(days=7)
        stats_7d = self.analyze_completion_times(start_date=stats_7d_start, end_date=now_utc)
        stats_7d['period_name'] = 'Last 7 Days'
        
        # Last 28 days (rolling)
        stats_28d_start = now_utc - timedelta(days=28)
        stats_28d = self.analyze_completion_times(start_date=stats_28d_start, end_date=now_utc)
        stats_28d['period_name'] = 'Last 28 Days'
        
        return {
            'last_24h': stats_24h,
            'last_7d': stats_7d,
            'last_28d': stats_28d,
            'generated_at': now_utc
        }
    
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


if __name__ == '__main__':
    """Test the Todoist analyzer."""
    try:
        analyzer = TodoistAnalyzer()
        stats = analyzer.analyze_multi_period()
        
        print("\n" + "="*60)
        print("TODOIST TASK COMPLETION SUMMARY")
        print("="*60)
        
        for period in ['last_24h', 'last_7d', 'last_28d']:
            period_stats = stats[period]
            print(f"\n{period_stats['period_name']}:")
            print(f"  Completed: {period_stats['total_completed']} tasks")
            
            if period_stats.get('avg_latency_formatted'):
                print(f"  Avg Completion Time: {period_stats['avg_latency_formatted']}")
                print(f"  Median Completion Time: {period_stats['median_latency_formatted']}")
        
        print("\n" + "="*60)
        
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

