"""Daily email reporter - generates and sends email reports."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz

from gmail_analyzer import GmailAnalyzer
from config import Config


class EmailReporter:
    """Generates and sends email reports."""
    
    def __init__(self):
        """Initialize email reporter."""
        self.analyzer = GmailAnalyzer()
    
    def generate_html_report(self, multi_stats: dict) -> str:
        """Generate HTML email report with 24h focus and rolling averages."""
        stats_24h = multi_stats.get('last_24h', {})
        stats_7d = multi_stats.get('last_7d', {})
        stats_28d = multi_stats.get('last_28d', {})
        
        if stats_24h.get('total_responses', 0) == 0:
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>📧 Email Response Time Report</h2>
                <p><strong>Email Account:</strong> {multi_stats.get('email_address', 'N/A')}</p>
                <p><strong>Period:</strong> Last 24 Hours</p>
                <p style="color: #666;">{stats_24h.get('message', 'No responses in the last 24 hours')}</p>
                <hr>
                <p style="font-size: 12px; color: #999;">
                    Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
            </html>
            """
        
        # Calculate response time distribution for 24h
        response_times_24h = stats_24h.get('response_details', [])
        under_1h = sum(1 for rt in response_times_24h if rt['response_time'].total_seconds() < 3600)
        under_24h = sum(1 for rt in response_times_24h if rt['response_time'].total_seconds() < 86400)
        over_24h = sum(1 for rt in response_times_24h if rt['response_time'].total_seconds() >= 86400)
        
        # Format period display
        period_start = stats_24h.get('start_date')
        period_end = stats_24h.get('end_date')
        period_display = f"{period_start.strftime('%b %d, %Y %I:%M %p')} - {period_end.strftime('%b %d, %I:%M %p UTC')}" if period_start and period_end else "Last 24 Hours"
        
        # Build rolling averages section
        rolling_averages_html = ""
        if stats_7d.get('total_responses', 0) > 0 or stats_28d.get('total_responses', 0) > 0:
            rolling_averages_html = '<div class="addendum"><h3>📊 Rolling Averages</h3>'
            
            if stats_7d.get('total_responses', 0) > 0:
                rolling_averages_html += f'''
                <div class="rolling-period">
                    <div class="period-header">Last 7 Days</div>
                    <div class="stat-row">
                        <span class="stat-label">Total Responses</span>
                        <span class="stat-value">{stats_7d['total_responses']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Average Response Time</span>
                        <span class="stat-value">{stats_7d['avg_response_time_formatted']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Median Response Time</span>
                        <span class="stat-value">{stats_7d['median_response_time_formatted']}</span>
                    </div>
                </div>
                '''
            
            if stats_28d.get('total_responses', 0) > 0:
                rolling_averages_html += f'''
                <div class="rolling-period">
                    <div class="period-header">Last 28 Days</div>
                    <div class="stat-row">
                        <span class="stat-label">Total Responses</span>
                        <span class="stat-value">{stats_28d['total_responses']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Average Response Time</span>
                        <span class="stat-value">{stats_28d['avg_response_time_formatted']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Median Response Time</span>
                        <span class="stat-value">{stats_28d['median_response_time_formatted']}</span>
                    </div>
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
                <h2>📧 Daily Email Response Report</h2>
                <div class="subtitle">{period_display}</div>
                
                <div style="margin: 20px 0;">
                    <p><strong>Email Account:</strong> {multi_stats['email_address']}</p>
                    <p><strong>Responses Sent:</strong> {stats_24h['total_responses']}</p>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Average Response Time (24h)</div>
                    <div class="metric-value">{stats_24h['avg_response_time_formatted']}</div>
                </div>
                
                <div class="stats">
                    <div class="stat-row">
                        <span class="stat-label">Median Response Time</span>
                        <span class="stat-value">{stats_24h['median_response_time_formatted']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Fastest Response</span>
                        <span class="stat-value">{GmailAnalyzer.format_duration(stats_24h['fastest_response'])}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Slowest Response</span>
                        <span class="stat-value">{GmailAnalyzer.format_duration(stats_24h['slowest_response'])}</span>
                    </div>
                </div>
                
                <div class="distribution">
                    <h3 style="margin-top: 0;">Response Time Distribution</h3>
                    <div class="stat-row">
                        <span class="stat-label">Under 1 hour</span>
                        <span class="stat-value">{under_1h} ({under_1h*100//stats_24h['total_responses'] if stats_24h['total_responses'] > 0 else 0}%)</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">1-24 hours</span>
                        <span class="stat-value">{under_24h - under_1h} ({(under_24h - under_1h)*100//stats_24h['total_responses'] if stats_24h['total_responses'] > 0 else 0}%)</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Over 24 hours</span>
                        <span class="stat-value">{over_24h} ({over_24h*100//stats_24h['total_responses'] if stats_24h['total_responses'] > 0 else 0}%)</span>
                    </div>
                </div>
                
                {rolling_averages_html}
                
                <div class="footer">
                    Generated on {multi_stats['generated_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                    Email Counter - Automated Response Time Tracking
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_report_via_gmail(self, multi_stats: dict):
        """Send report using Gmail API (sends from authenticated account)."""
        import base64
        from email.mime.text import MIMEText
        
        # Create message
        subject = f"📊 Daily Email Response Report - {datetime.now().strftime('%Y-%m-%d')}"
        html_body = self.generate_html_report(multi_stats)
        
        message = MIMEText(html_body, 'html')
        message['to'] = Config.REPORT_EMAIL
        message['subject'] = subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        try:
            sent_message = self.analyzer.service.users().messages().send(
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
        print(f"Generating daily email report...")
        print(f"Report will be sent to: {Config.REPORT_EMAIL}")
        
        # Analyze emails for multiple periods
        multi_stats = self.analyzer.analyze_multi_period()
        
        if not multi_stats:
            print("✗ Failed to analyze emails")
            return False
        
        # Print summary to console
        stats_24h = multi_stats.get('last_24h', {})
        if stats_24h.get('total_responses', 0) > 0:
            print(f"\n24h Summary: {stats_24h['total_responses']} responses, avg {stats_24h['avg_response_time_formatted']}")
        
        stats_7d = multi_stats.get('last_7d', {})
        if stats_7d.get('total_responses', 0) > 0:
            print(f"7d Rolling: {stats_7d['total_responses']} responses, avg {stats_7d['avg_response_time_formatted']}")
        
        stats_28d = multi_stats.get('last_28d', {})
        if stats_28d.get('total_responses', 0) > 0:
            print(f"28d Rolling: {stats_28d['total_responses']} responses, avg {stats_28d['avg_response_time_formatted']}")
        
        # Send via email
        return self.send_report_via_gmail(multi_stats)


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

