"""Daily email reporter - generates and sends email reports."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz

from gmail_analyzer import GmailAnalyzer
from config import Config
import requests
import json

# Conditionally import OutlookAnalyzer
if Config.OUTLOOK_ENABLED:
    from outlook_analyzer import OutlookAnalyzer

# Conditionally import TodoistAnalyzer
if Config.TODOIST_ENABLED:
    from todoist_analyzer import TodoistAnalyzer


class EmailReporter:
    """Generates and sends email reports."""
    
    def __init__(self):
        """Initialize email reporter."""
        # Work Gmail (m5c7.com)
        self.gmail_analyzer = GmailAnalyzer(account_name="Work Gmail (m5c7.com)")
        
        # Personal Gmail (if enabled)
        self.personal_gmail_analyzer = None
        if Config.PERSONAL_GMAIL_ENABLED:
            self.personal_gmail_analyzer = GmailAnalyzer(
                credentials_file=Config.PERSONAL_GMAIL_CREDENTIALS_FILE,
                token_file=Config.PERSONAL_GMAIL_TOKEN_FILE,
                account_name="Personal Gmail"
            )
        
        # Outlook (if enabled)
        self.outlook_analyzer = OutlookAnalyzer() if Config.OUTLOOK_ENABLED else None
        
        # Todoist (if enabled)
        self.todoist_analyzer = TodoistAnalyzer() if Config.TODOIST_ENABLED else None
        
        # Messages (if gist ID exists)
        self.messages_gist_id = self._load_messages_gist_id()
    
    def _load_messages_gist_id(self) -> str:
        """Load Messages gist ID from file."""
        import os
        gist_id_file = '.messages_gist_id'
        if os.path.exists(gist_id_file):
            with open(gist_id_file, 'r') as f:
                return f.read().strip()
        return None
    
    def download_messages_stats(self) -> dict:
        """Download Messages stats from GitHub Gist."""
        if not self.messages_gist_id:
            print("⚠ No Messages gist ID found - skipping Messages stats")
            return None
        
        try:
            url = f'https://api.github.com/gists/{self.messages_gist_id}'
            response = requests.get(url)
            
            if response.status_code == 200:
                gist_data = response.json()
                files = gist_data.get('files', {})
                
                if 'messages_stats.json' in files:
                    content = files['messages_stats.json']['content']
                    stats = json.loads(content)
                    print("✓ Downloaded Messages stats from Gist")
                    return stats
                else:
                    print("⚠ messages_stats.json not found in Gist")
                    return None
            else:
                print(f"⚠ Failed to download Gist: {response.status_code}")
                return None
        
        except Exception as e:
            print(f"⚠ Error downloading Messages stats: {e}")
            return None
    
    def generate_html_report(self, gmail_stats: dict, personal_gmail_stats: dict = None, outlook_stats: dict = None, messages_stats: dict = None, todoist_stats: dict = None) -> str:
        """Generate HTML email report with 24h focus and rolling averages.
        
        Combines Work Gmail, Personal Gmail, Outlook, Messages, and Todoist stats with breakouts.
        """
        # Extract Gmail stats
        gmail_24h = gmail_stats.get('last_24h', {})
        gmail_7d = gmail_stats.get('last_7d', {})
        gmail_28d = gmail_stats.get('last_28d', {})
        
        # Extract Outlook stats if available
        outlook_24h = outlook_stats.get('last_24h', {}) if outlook_stats else {}
        outlook_7d = outlook_stats.get('last_7d', {}) if outlook_stats else {}
        outlook_28d = outlook_stats.get('last_28d', {}) if outlook_stats else {}
        
        # Extract Messages stats if available
        messages_24h = messages_stats.get('last_24h', {}) if messages_stats else {}
        messages_7d = messages_stats.get('last_7d', {}) if messages_stats else {}
        messages_28d = messages_stats.get('last_28d', {}) if messages_stats else {}
        
        # Calculate combined totals
        combined_24h_total = (gmail_24h.get('total_responses', 0) + 
                             outlook_24h.get('total_responses', 0) + 
                             messages_24h.get('total_responses', 0))
        combined_7d_total = (gmail_7d.get('total_responses', 0) + 
                            outlook_7d.get('total_responses', 0) + 
                            messages_7d.get('total_responses', 0))
        combined_28d_total = (gmail_28d.get('total_responses', 0) + 
                             outlook_28d.get('total_responses', 0) + 
                             messages_28d.get('total_responses', 0))
        
        if combined_24h_total == 0:
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>📧 Email Response Time Report</h2>
                <p><strong>Period:</strong> Last 24 Hours</p>
                <p style="color: #666;">No responses in the last 24 hours</p>
                <hr>
                <p style="font-size: 12px; color: #999;">
                    Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
            </html>
            """
        
        # Calculate combined response time distribution for 24h
        gmail_response_times_24h = gmail_24h.get('response_details', [])
        outlook_response_times_24h = outlook_24h.get('response_details', [])
        messages_response_times_24h = messages_24h.get('response_details', [])
        all_response_times_24h = gmail_response_times_24h + outlook_response_times_24h + messages_response_times_24h
        
        combined_under_1h = sum(1 for rt in all_response_times_24h if rt['response_time'].total_seconds() < 3600)
        combined_under_24h = sum(1 for rt in all_response_times_24h if rt['response_time'].total_seconds() < 86400)
        combined_over_24h = sum(1 for rt in all_response_times_24h if rt['response_time'].total_seconds() >= 86400)
        
        # Calculate combined average for 24h
        if all_response_times_24h:
            combined_24h_avg_seconds = sum(rt['response_time'].total_seconds() for rt in all_response_times_24h) / len(all_response_times_24h)
            combined_24h_avg_formatted = GmailAnalyzer.format_duration(combined_24h_avg_seconds)
        else:
            combined_24h_avg_formatted = "N/A"
        
        # Format period display - convert to Pacific Time for display
        pacific = pytz.timezone('America/Los_Angeles')
        period_start = gmail_24h.get('start_date') or outlook_24h.get('start_date') or messages_24h.get('start_date')
        period_end = gmail_24h.get('end_date') or outlook_24h.get('end_date') or messages_24h.get('end_date')
        
        if period_start and period_end:
            # Convert to PT for display
            period_start_pt = period_start.astimezone(pacific)
            period_end_pt = period_end.astimezone(pacific)
            period_display = f"{period_start_pt.strftime('%A, %B %d, %Y')} (Pacific Time)"
        else:
            period_display = "Previous Day"
        
        # Helper function to create account breakout HTML
        def create_account_breakout(gmail_data, outlook_data, messages_data, title):
            html = f'<div class="account-breakouts"><h4>{title}</h4>'
            
            # Messages section (show first since it's usually fastest)
            if messages_data and messages_data.get('total_responses', 0) > 0:
                imessage_count = messages_data.get('imessage_count', 0)
                sms_count = messages_data.get('sms_count', 0)
                service_breakdown = f" ({imessage_count} iMessage, {sms_count} SMS)" if (imessage_count or sms_count) else ""
                html += f'''
                <div class="account-section">
                    <div class="account-header">📱 Messages{service_breakdown}</div>
                    <div class="stat-row-small">
                        <span class="stat-label">Responses</span>
                        <span class="stat-value">{messages_data['total_responses']}</span>
                    </div>
                    <div class="stat-row-small">
                        <span class="stat-label">Average</span>
                        <span class="stat-value">{messages_data['avg_response_time_formatted']}</span>
                    </div>
                </div>
                '''
            
            # Gmail section
            if gmail_data.get('total_responses', 0) > 0:
                domain = gmail_data.get('email_address', 'Gmail').split('@')[1] if '@' in gmail_data.get('email_address', '') else 'Gmail'
                html += f'''
                <div class="account-section">
                    <div class="account-header">📧 {domain}</div>
                    <div class="stat-row-small">
                        <span class="stat-label">Responses</span>
                        <span class="stat-value">{gmail_data['total_responses']}</span>
                    </div>
                    <div class="stat-row-small">
                        <span class="stat-label">Average</span>
                        <span class="stat-value">{gmail_data['avg_response_time_formatted']}</span>
                    </div>
                </div>
                '''
            
            # Outlook section
            if outlook_data and outlook_data.get('total_responses', 0) > 0:
                domain = outlook_data.get('email_address', 'Outlook').split('@')[1] if '@' in outlook_data.get('email_address', '') else 'Outlook'
                html += f'''
                <div class="account-section">
                    <div class="account-header">📧 {domain}</div>
                    <div class="stat-row-small">
                        <span class="stat-label">Responses</span>
                        <span class="stat-value">{outlook_data['total_responses']}</span>
                    </div>
                    <div class="stat-row-small">
                        <span class="stat-label">Average</span>
                        <span class="stat-value">{outlook_data['avg_response_time_formatted']}</span>
                    </div>
                </div>
                '''
            
            html += '</div>'
            return html
        
        # Build previous day breakout
        breakout_24h_html = create_account_breakout(gmail_24h, outlook_24h, messages_24h, "Previous Day Breakout")
        
        # Build rolling averages section
        rolling_averages_html = ""
        if combined_7d_total > 0 or combined_28d_total > 0:
            rolling_averages_html = '<div class="addendum"><h3>📊 Rolling Averages</h3>'
            
            # 7-day rolling
            if combined_7d_total > 0:
                # Calculate combined 7d average
                gmail_7d_responses = gmail_7d.get('response_details', [])
                outlook_7d_responses = outlook_7d.get('response_details', [])
                messages_7d_responses = messages_7d.get('response_details', [])
                all_7d_responses = gmail_7d_responses + outlook_7d_responses + messages_7d_responses
                if all_7d_responses:
                    combined_7d_avg_seconds = sum(rt['response_time'].total_seconds() for rt in all_7d_responses) / len(all_7d_responses)
                    combined_7d_avg_formatted = GmailAnalyzer.format_duration(combined_7d_avg_seconds)
                else:
                    combined_7d_avg_formatted = "N/A"
                
                rolling_averages_html += f'''
                <div class="rolling-period">
                    <div class="period-header">Last 7 Days</div>
                    <div class="stat-row">
                        <span class="stat-label">Total Responses</span>
                        <span class="stat-value">{combined_7d_total}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Combined Average</span>
                        <span class="stat-value">{combined_7d_avg_formatted}</span>
                    </div>
                    {create_account_breakout(gmail_7d, outlook_7d, messages_7d, "")}
                </div>
                '''
            
            # 28-day rolling
            if combined_28d_total > 0:
                # Calculate combined 28d average
                gmail_28d_responses = gmail_28d.get('response_details', [])
                outlook_28d_responses = outlook_28d.get('response_details', [])
                messages_28d_responses = messages_28d.get('response_details', [])
                all_28d_responses = gmail_28d_responses + outlook_28d_responses + messages_28d_responses
                if all_28d_responses:
                    combined_28d_avg_seconds = sum(rt['response_time'].total_seconds() for rt in all_28d_responses) / len(all_28d_responses)
                    combined_28d_avg_formatted = GmailAnalyzer.format_duration(combined_28d_avg_seconds)
                else:
                    combined_28d_avg_formatted = "N/A"
                
                rolling_averages_html += f'''
                <div class="rolling-period">
                    <div class="period-header">Last 28 Days</div>
                    <div class="stat-row">
                        <span class="stat-label">Total Responses</span>
                        <span class="stat-value">{combined_28d_total}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Combined Average</span>
                        <span class="stat-value">{combined_28d_avg_formatted}</span>
                    </div>
                    {create_account_breakout(gmail_28d, outlook_28d, messages_28d, "")}
                </div>
                '''
            
            rolling_averages_html += '</div>'
        
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h2 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                    margin-bottom: 5px;
                }}
                .subtitle {{
                    color: #7f8c8d;
                    font-size: 14px;
                    margin-bottom: 20px;
                }}
                .metric {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border-left: 4px solid #3498db;
                }}
                .metric-label {{
                    color: #7f8c8d;
                    font-size: 14px;
                    margin-bottom: 5px;
                }}
                .metric-value {{
                    color: #2c3e50;
                    font-size: 24px;
                    font-weight: bold;
                }}
                .stats {{
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    margin-top: 20px;
                }}
                .stat-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }}
                .stat-label {{
                    color: #555;
                }}
                .stat-value {{
                    color: #2c3e50;
                    font-weight: bold;
                }}
                .distribution {{
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #e8f4f8;
                    border-radius: 5px;
                }}
                .addendum {{
                    margin-top: 30px;
                    padding: 20px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                    border-top: 2px solid #ddd;
                }}
                .addendum h3 {{
                    color: #555;
                    font-size: 18px;
                    margin-top: 0;
                    margin-bottom: 15px;
                }}
                .rolling-period {{
                    margin-bottom: 20px;
                    padding: 15px;
                    background-color: white;
                    border-radius: 5px;
                    border-left: 3px solid #95a5a6;
                }}
                .period-header {{
                    font-weight: bold;
                    color: #555;
                    margin-bottom: 10px;
                    font-size: 16px;
                }}
                .account-breakouts {{
                    margin-top: 15px;
                    padding: 10px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }}
                .account-breakouts h4 {{
                    margin: 0 0 10px 0;
                    font-size: 14px;
                    color: #7f8c8d;
                }}
                .account-section {{
                    margin-bottom: 10px;
                    padding: 10px;
                    background-color: white;
                    border-radius: 4px;
                    border-left: 3px solid #3498db;
                }}
                .account-header {{
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 8px;
                    font-size: 14px;
                }}
                .stat-row-small {{
                    display: flex;
                    justify-content: space-between;
                    padding: 5px 0;
                    font-size: 13px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #999;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📧 Daily Response Report</h2>
                <div class="subtitle">{period_display}</div>
                
                <div style="margin: 20px 0;">
                    <p><strong>Total Responses:</strong> {combined_24h_total}</p>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Combined Average Response Time</div>
                    <div class="metric-value">{combined_24h_avg_formatted}</div>
                </div>
                
                {breakout_24h_html}
                
                <div class="distribution">
                    <h3 style="margin-top: 0;">Response Time Distribution (Combined)</h3>
                    <div class="stat-row">
                        <span class="stat-label">Under 1 hour</span>
                        <span class="stat-value">{combined_under_1h} ({combined_under_1h*100//combined_24h_total if combined_24h_total > 0 else 0}%)</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">1-24 hours</span>
                        <span class="stat-value">{combined_under_24h - combined_under_1h} ({(combined_under_24h - combined_under_1h)*100//combined_24h_total if combined_24h_total > 0 else 0}%)</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Over 24 hours</span>
                        <span class="stat-value">{combined_over_24h} ({combined_over_24h*100//combined_24h_total if combined_24h_total > 0 else 0}%)</span>
                    </div>
                </div>
                
                {rolling_averages_html}
                
                <div class="footer">
                    Generated on {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                    Email Counter - Automated Response Time Tracking
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_report_via_gmail(self, gmail_stats: dict, personal_gmail_stats: dict = None, outlook_stats: dict = None, messages_stats: dict = None, todoist_stats: dict = None):
        """Send report using Gmail API (sends from authenticated account)."""
        import base64
        from email.mime.text import MIMEText
        
        # Create message with previous day's date in PT
        pacific = pytz.timezone('America/Los_Angeles')
        now_pt = datetime.now(pytz.UTC).astimezone(pacific)
        yesterday_pt = now_pt - timedelta(days=1)
        
        subject = f"📊 Daily Response Report - {yesterday_pt.strftime('%A, %b %d, %Y')}"
        html_body = self.generate_html_report(gmail_stats, personal_gmail_stats, outlook_stats, messages_stats, todoist_stats)
        
        message = MIMEText(html_body, 'html')
        message['to'] = Config.REPORT_EMAIL
        message['subject'] = subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        try:
            sent_message = self.gmail_analyzer.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"✓ Report sent successfully to {Config.REPORT_EMAIL}")
            print(f"  Message ID: {sent_message['id']}")
            return True
            
        except Exception as e:
            print(f"✗ Error sending report: {e}")
            return False
    
    def generate_and_send_report(self):
        """Generate analysis and send report."""
        print(f"Generating daily report...")
        print(f"Report will be sent to: {Config.REPORT_EMAIL}")
        
        # Analyze Work Gmail
        print("\n--- Analyzing Work Gmail (m5c7.com) ---")
        gmail_stats = self.gmail_analyzer.analyze_multi_period()
        
        if not gmail_stats:
            print("✗ Failed to analyze work Gmail")
            return False
        
        # Analyze Personal Gmail if enabled
        personal_gmail_stats = None
        if Config.PERSONAL_GMAIL_ENABLED and self.personal_gmail_analyzer:
            print("\n--- Analyzing Personal Gmail ---")
            try:
                personal_gmail_stats = self.personal_gmail_analyzer.analyze_multi_period()
            except Exception as e:
                print(f"⚠ Warning: Failed to analyze personal Gmail: {e}")
        
        # Analyze Outlook emails if enabled
        outlook_stats = None
        if Config.OUTLOOK_ENABLED and self.outlook_analyzer:
            print("\n--- Analyzing Outlook ---")
            outlook_stats = self.outlook_analyzer.analyze_multi_period()
            if not outlook_stats:
                print("⚠ Warning: Failed to analyze Outlook emails")
        
        # Download Messages stats from Gist
        messages_stats = None
        if self.messages_gist_id:
            print("\n--- Downloading Messages Stats ---")
            messages_stats = self.download_messages_stats()
            if not messages_stats:
                print("⚠ Warning: Failed to download Messages stats")
        
        # Analyze Todoist if enabled
        todoist_stats = None
        if Config.TODOIST_ENABLED and self.todoist_analyzer:
            print("\n--- Analyzing Todoist Tasks ---")
            try:
                todoist_stats = self.todoist_analyzer.analyze_multi_period()
            except Exception as e:
                print(f"⚠ Warning: Failed to analyze Todoist: {e}")
        
        # Print summary to console
        print("\n" + "="*60)
        print("COMBINED SUMMARY")
        print("="*60)
        
        # Get the date we're reporting on in PT
        pacific = pytz.timezone('America/Los_Angeles')
        yesterday_pt = datetime.now(pytz.UTC).astimezone(pacific) - timedelta(days=1)
        date_str = yesterday_pt.strftime('%A, %b %d, %Y')
        
        # Extract 24h stats
        gmail_24h = gmail_stats.get('last_24h', {})
        personal_gmail_24h = personal_gmail_stats.get('last_24h', {}) if personal_gmail_stats else {}
        outlook_24h = outlook_stats.get('last_24h', {}) if outlook_stats else {}
        messages_24h = messages_stats.get('last_24h', {}) if messages_stats else {}
        todoist_24h = todoist_stats.get('last_24h', {}) if todoist_stats else {}
        
        # Count responses
        gmail_count = gmail_24h.get('total_responses', 0)
        personal_gmail_count = personal_gmail_24h.get('total_responses', 0)
        outlook_count = outlook_24h.get('total_responses', 0)
        messages_count = messages_24h.get('total_responses', 0)
        total_count = gmail_count + personal_gmail_count + outlook_count + messages_count
        
        print(f"\n📧 COMMUNICATION RESPONSES - Previous Day ({date_str}): {total_count} total")
        if messages_count > 0:
            print(f"  📱 Messages: {messages_count} responses, avg {messages_24h['avg_response_time_formatted']}")
        if gmail_count > 0:
            print(f"  📧 Work Gmail: {gmail_count} responses, avg {gmail_24h['avg_response_time_formatted']}")
        if personal_gmail_count > 0:
            print(f"  📧 Personal Gmail: {personal_gmail_count} responses, avg {personal_gmail_24h['avg_response_time_formatted']}")
        if outlook_count > 0:
            print(f"  📧 Outlook: {outlook_count} responses, avg {outlook_24h['avg_response_time_formatted']}")
        
        # Todoist tasks
        if todoist_24h.get('total_completed', 0) > 0:
            tasks_completed = todoist_24h['total_completed']
            avg_latency = todoist_24h.get('avg_latency_formatted', 'N/A')
            print(f"\n✅ TODOIST TASKS:")
            print(f"  Completed: {tasks_completed} tasks")
            if avg_latency != 'N/A':
                print(f"  Avg Completion Time: {avg_latency}")
        
        # Send via email
        return self.send_report_via_gmail(gmail_stats, personal_gmail_stats, outlook_stats, messages_stats, todoist_stats)


def main():
    """Main entry point."""
    try:
        # Validate configuration
        Config.validate()
        
        # Create reporter and send
        reporter = EmailReporter()
        success = reporter.generate_and_send_report()
        
        return 0 if success else 1
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())

