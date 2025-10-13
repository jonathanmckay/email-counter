#!/bin/bash

# Script to prepare GitHub Secrets from local files
# Run this script to get all the values you need to paste into GitHub Secrets

echo "======================================================================"
echo "GITHUB SECRETS SETUP"
echo "======================================================================"
echo ""
echo "Copy each value below and add it as a GitHub Secret:"
echo "Go to: https://github.com/jonathanmckay/email-counter/settings/secrets/actions"
echo ""
echo "----------------------------------------------------------------------"

# Check if credentials.json exists
if [ -f "credentials.json" ]; then
    echo "Secret Name: GMAIL_CREDENTIALS"
    echo "Value:"
    cat credentials.json
    echo ""
    echo "----------------------------------------------------------------------"
else
    echo "⚠️  WARNING: credentials.json not found!"
    echo "   Please download OAuth credentials from Google Cloud Console first."
    echo ""
    echo "----------------------------------------------------------------------"
fi

# Check if token.json exists
if [ -f "token.json" ]; then
    echo "Secret Name: GMAIL_TOKEN"
    echo "Value:"
    cat token.json
    echo ""
    echo "----------------------------------------------------------------------"
else
    echo "⚠️  WARNING: token.json not found!"
    echo "   Run 'python email_reporter.py' first to authenticate."
    echo ""
    echo "----------------------------------------------------------------------"
fi

# Check .env for REPORT_EMAIL
if [ -f ".env" ]; then
    REPORT_EMAIL=$(grep REPORT_EMAIL .env | cut -d'=' -f2)
    echo "Secret Name: REPORT_EMAIL"
    echo "Value: $REPORT_EMAIL"
    echo ""
    echo "----------------------------------------------------------------------"
    
    GMAIL_ADDRESS=$(grep GMAIL_ADDRESS .env | cut -d'=' -f2)
    echo "Secret Name: GMAIL_ADDRESS"
    echo "Value: $GMAIL_ADDRESS"
    echo ""
    echo "----------------------------------------------------------------------"
    
    OUTLOOK_ENABLED=$(grep OUTLOOK_ENABLED .env | cut -d'=' -f2)
    echo "Secret Name: OUTLOOK_ENABLED"
    echo "Value: $OUTLOOK_ENABLED"
    echo ""
    echo "----------------------------------------------------------------------"
else
    echo "⚠️  WARNING: .env file not found!"
    echo ""
fi

# Check if outlook_token.json exists
if [ -f "outlook_token.json" ]; then
    echo "Secret Name: OUTLOOK_TOKEN"
    echo "Value:"
    cat outlook_token.json
    echo ""
    echo "----------------------------------------------------------------------"
    
    if [ -f ".env" ]; then
        OUTLOOK_CLIENT_ID=$(grep OUTLOOK_CLIENT_ID .env | cut -d'=' -f2)
        echo "Secret Name: OUTLOOK_CLIENT_ID"
        echo "Value: $OUTLOOK_CLIENT_ID"
        echo ""
        echo "----------------------------------------------------------------------"
        
        OUTLOOK_TENANT_ID=$(grep OUTLOOK_TENANT_ID .env | cut -d'=' -f2)
        echo "Secret Name: OUTLOOK_TENANT_ID"
        echo "Value: $OUTLOOK_TENANT_ID"
        echo ""
        echo "----------------------------------------------------------------------"
    fi
fi

echo ""
echo "======================================================================"
echo "NEXT STEPS:"
echo "======================================================================"
echo "1. Go to: https://github.com/jonathanmckay/email-counter/settings/secrets/actions"
echo "2. Click 'New repository secret' for each secret above"
echo "3. Copy/paste the Name and Value"
echo "4. Test the workflow: Actions tab → Daily Email Report → Run workflow"
echo ""
echo "IMPORTANT: Store these values securely! They grant access to your email."
echo "======================================================================"

