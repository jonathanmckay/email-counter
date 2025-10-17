"""Messages client - uploads stats to GitHub Gist."""

import json
import os
from datetime import datetime
import requests
from messages_analyzer import MessagesAnalyzer


class MessagesClient:
    """Client to analyze Messages and upload stats to GitHub Gist."""
    
    def __init__(self, github_token: str, gist_id: str = None):
        """Initialize the client.
        
        Args:
            github_token: GitHub personal access token with gist scope
            gist_id: Existing gist ID to update (optional, will create new if None)
        """
        self.github_token = github_token
        self.gist_id = gist_id
        self.analyzer = MessagesAnalyzer()
    
    def analyze_and_format_stats(self) -> dict:
        """Analyze Messages and format for upload."""
        print("Analyzing Messages...")
        multi_stats = self.analyzer.analyze_multi_period()
        
        # Format for JSON serialization (convert datetime objects)
        def serialize_stats(stats):
            serialized = {}
            for key, value in stats.items():
                if key == 'response_details':
                    # Don't upload full message details for privacy
                    continue
                elif key in ['start_date', 'end_date', 'generated_at']:
                    serialized[key] = value.isoformat() if value else None
                elif isinstance(value, dict):
                    serialized[key] = serialize_stats(value)
                else:
                    serialized[key] = value
            return serialized
        
        formatted = {
            'last_24h': serialize_stats(multi_stats['last_24h']),
            'last_7d': serialize_stats(multi_stats['last_7d']),
            'last_28d': serialize_stats(multi_stats['last_28d']),
            'email_address': 'Messages',
            'generated_at': multi_stats['generated_at'].isoformat(),
            'client_version': '1.0.0'
        }
        
        return formatted
    
    def upload_to_gist(self, stats: dict) -> str:
        """Upload stats to GitHub Gist.
        
        Returns:
            gist_id: The ID of the gist (for future updates)
        """
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        gist_content = {
            'description': 'Email Counter - Messages Stats',
            'public': False,  # Private gist
            'files': {
                'messages_stats.json': {
                    'content': json.dumps(stats, indent=2)
                }
            }
        }
        
        if self.gist_id:
            # Update existing gist
            url = f'https://api.github.com/gists/{self.gist_id}'
            print(f"Updating existing gist: {self.gist_id}")
            response = requests.patch(url, headers=headers, json=gist_content)
        else:
            # Create new gist
            url = 'https://api.github.com/gists'
            print("Creating new gist...")
            response = requests.post(url, headers=headers, json=gist_content)
        
        if response.status_code in [200, 201]:
            gist_data = response.json()
            gist_id = gist_data['id']
            gist_url = gist_data['html_url']
            print(f"✓ Successfully uploaded to gist: {gist_id}")
            print(f"  URL: {gist_url}")
            return gist_id
        else:
            raise Exception(f"Failed to upload to gist: {response.status_code} - {response.text}")
    
    def run(self):
        """Run the client: analyze and upload."""
        print("="*60)
        print("MESSAGES CLIENT - UPLOAD TO GITHUB GIST")
        print("="*60)
        print()
        
        try:
            # Analyze messages
            stats = self.analyze_and_format_stats()
            
            # Print summary
            print()
            print("Summary:")
            print(f"  24h: {stats['last_24h']['total_responses']} responses")
            print(f"  7d:  {stats['last_7d']['total_responses']} responses")
            print(f"  28d: {stats['last_28d']['total_responses']} responses")
            print()
            
            # Upload to gist
            gist_id = self.upload_to_gist(stats)
            
            # Save gist ID for future updates
            with open('.messages_gist_id', 'w') as f:
                f.write(gist_id)
            
            print()
            print("✓ Client run complete!")
            print(f"  Gist ID saved to: .messages_gist_id")
            print()
            
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    # Get GitHub token from environment
    github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print()
        print("To create a GitHub token:")
        print("1. Go to: https://github.com/settings/tokens")
        print("2. Click 'Generate new token (classic)'")
        print("3. Give it a name: 'Email Counter Messages Client'")
        print("4. Select scope: 'gist'")
        print("5. Click 'Generate token'")
        print("6. Copy the token and add to your .env file:")
        print("   GITHUB_TOKEN=your_token_here")
        print()
        return 1
    
    # Check for existing gist ID
    gist_id = None
    if os.path.exists('.messages_gist_id'):
        with open('.messages_gist_id', 'r') as f:
            gist_id = f.read().strip()
        print(f"Found existing gist ID: {gist_id}")
        print()
    
    # Run client
    client = MessagesClient(github_token, gist_id)
    success = client.run()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())

