#!/bin/bash
# Script to run the Google Docs downloader

echo "Google Docs to Markdown Downloader"
echo "=================================="

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Warning: No virtual environment found. Using system Python."
fi

# Check if credentials file exists (either credentials.json or client_secret_*.json)
if [ ! -f "google_docs/credentials.json" ] && [ ! -f "google_docs/client_secret_*.json" ]; then
    # Check if any client_secret_*.json files exist
    client_secret_count=$(ls google_docs/client_secret_*.json 2>/dev/null | wc -l)
    if [ "$client_secret_count" -eq 0 ]; then
        echo ""
        echo "ERROR: Credentials file not found!"
        echo ""
        echo "Please follow these steps:"
        echo "1. Go to https://console.cloud.google.com/"
        echo "2. Create a new project or select existing one"
        echo "3. Enable the Google Docs API"
        echo "4. Create OAuth 2.0 credentials (Desktop application)"
        echo "5. Download the credentials file (usually client_secret_*.json) and place it in google_docs/ folder"
        echo ""
        exit 1
    fi
fi

# Run the downloader
echo "Starting download process..."
echo ""

python3 google_docs/google_docs_downloader.py docs_url.csv

echo ""
echo "Download complete!"
echo "Check the 'downloads' folder for your markdown files."
