#!/bin/bash

# Test script to simulate GitHub Actions environment locally
# This helps verify the workflow will work before pushing

set -e

echo "======================================================================"
echo "SIMULATING GITHUB ACTIONS ENVIRONMENT"
echo "======================================================================"
echo ""

# Set CI environment variables to simulate GitHub Actions
export CI=true
export GITHUB_ACTIONS=true

# Check if secrets are available
if [ ! -f "credentials.json" ]; then
    echo "❌ ERROR: credentials.json not found"
    exit 1
fi

if [ ! -f "token.json" ]; then
    echo "❌ ERROR: token.json not found"
    exit 1
fi

echo "✓ credentials.json found"
echo "✓ token.json found"
echo ""

# Create a temporary directory for testing
TEST_DIR=$(mktemp -d)
echo "Using temp directory: $TEST_DIR"
echo ""

# Copy files to temp directory
cp credentials.json "$TEST_DIR/"
cp token.json "$TEST_DIR/"
cp -r venv "$TEST_DIR/" 2>/dev/null || true
cp *.py "$TEST_DIR/"
cp .env "$TEST_DIR/"
cp requirements.txt "$TEST_DIR/"

cd "$TEST_DIR"

# Convert token.json to JSON format if it's pickle
if [ -f "../venv/bin/python" ]; then
    PYTHON_CMD="../venv/bin/python"
else
    PYTHON_CMD="python3"
fi

echo "Converting token to JSON format (if needed)..."
$PYTHON_CMD -c "
import pickle
import json
import os

try:
    # Try to load as pickle
    with open('token.json', 'rb') as f:
        creds = pickle.load(f)
    
    # Convert to JSON
    token_dict = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': list(creds.scopes),
    }
    
    # Write as JSON
    with open('token.json', 'w') as f:
        json.dump(token_dict, f, indent=2)
    
    print('✓ Token converted to JSON format')
except Exception as e:
    print(f'Note: {e}')
    print('Token may already be in JSON format')
" || echo "Warning: Token conversion failed, continuing anyway..."

echo ""
echo "======================================================================"
echo "TESTING EMAIL REPORTER"
echo "======================================================================"
echo ""

# Add parent venv to path if it exists
if [ -d "../venv" ]; then
    export PATH="../venv/bin:$PATH"
fi

# Run the email reporter
$PYTHON_CMD email_reporter.py

EXIT_CODE=$?

echo ""
echo "======================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ SUCCESS! The workflow should work on GitHub Actions"
    echo ""
    echo "Next steps:"
    echo "1. Update GMAIL_TOKEN secret on GitHub with JSON format"
    echo "2. Run the workflow on GitHub Actions"
else
    echo "❌ FAILED! Exit code: $EXIT_CODE"
    echo ""
    echo "Please fix the issues above before running on GitHub Actions"
fi
echo "======================================================================"

# Cleanup
cd -
rm -rf "$TEST_DIR"

exit $EXIT_CODE



