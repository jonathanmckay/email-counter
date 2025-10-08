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
    
    def generate_html_report(self, stats: dict) -> str:
        """Generate HTML email report."""
        if stats.get('total_responses', 0) == 0:
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>📧 Email Response Time Report</h2>
                <p><strong>Email Account:</strong> {stats.get('email_address', 'N/A')}</p>
                <p><strong>Period:</strong> Last {stats.get('analysis_period_days', 30)} days</p>
                <p style="color: #666;">{stats.get('message', 'No data available')}</p>
                <hr>
                <p style="font-size: 12px; color: #999;">
                    Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
            </html>
            """
        
        # Calculate response time distribution
        response_times = stats.get('response_details', [])
        under_1h = sum(1 for rt in response_times if rt['response_time'].total_seconds() < 3600)
        under_24h = sum(1 for rt in response_times if rt['response_time'].total_seconds() < 86400)
        over_24h = sum(1 for rt in response_times if rt['response_time'].total_seconds() >= 86400)
        
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
                <h2>📧 Email Response Time Report</h2>
                
                <div style="margin: 20px 0;">
                    <p><strong>Email Account:</strong> {stats['email_address']}</p>
                    <p><strong>Analysis Period:</strong> Last {stats['analysis_period_days']} days</p>
                    <p><strong>Total Responses:</strong> {stats['total_responses']}</p>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Average Response Time</div>
                    <div class="metric-value">{stats['avg_response_time_formatted']}</div>
                </div>
                
                <div class="stats">
                    <div class="stat-row">
                        <span class="stat-label">Median Response Time</span>
                        <span class="stat-value">{stats['median_response_time_formatted']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Fastest Response</span>
                        <span class="stat-value">{GmailAnalyzer.format_duration(stats['fastest_response'])}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Slowest Response</span>
                        <span class="stat-value">{GmailAnalyzer.format_duration(stats['slowest_response'])}</span>
                    </div>
                </div>
                
                <div class="distribution">
                    <h3 style="margin-top: 0;">Response Time Distribution</h3>
                    <div class="stat-row">
                        <span class="stat-label">Under 1 hour</span>
                        <span class="stat-value">{under_1h} ({under_1h*100//stats['total_responses']}%)</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">1-24 hours</span>
                        <span class="stat-value">{under_24h - under_1h} ({(under_24h - under_1h)*100//stats['total_responses']}%)</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Over 24 hours</span>
                        <span class="stat-value">{over_24h} ({over_24h*100//stats['total_responses']}%)</span>
                    </div>
                </div>
                
                <div class="footer">
                    Generated on {stats['generated_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                    Email Counter - Automated Response Time Tracking
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_report_via_gmail(self, stats: dict):
        """Send report using Gmail API (sends from authenticated account)."""
        import base64
        from email.mime.text import MIMEText
        
        # Create message
        subject = f"📊 Daily Email Response Report - {datetime.now().strftime('%Y-%m-%d')}"
        html_body = self.generate_html_report(stats)
        
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
        
        # Analyze emails
        stats = self.analyzer.analyze_response_times(days=Config.ANALYSIS_DAYS)
        
        if not stats:
            print("✗ Failed to analyze emails")
            return False
        
        # Print to console
        self.analyzer.print_report(stats)
        
        # Send via email
        return self.send_report_via_gmail(stats)


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

