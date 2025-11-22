#!/usr/bin/env python3
"""
Test script to verify credentials file detection.
"""

import os
import glob

def find_credentials_file():
    """Test the credentials file detection logic."""
    # Change to google_docs directory if not already there
    if not os.path.basename(os.getcwd()) == 'google_docs':
        os.chdir('google_docs')

    if os.path.exists('credentials.json'):
        return 'credentials.json'
    else:
        # Look for client_secret_*.json files
        client_secret_files = glob.glob('client_secret_*.json')
        if client_secret_files:
            return client_secret_files[0]  # Use the first one found
        else:
            return None

if __name__ == "__main__":
    print("Testing credentials file detection...")
    credentials_file = find_credentials_file()
    if credentials_file:
        print(f"✓ Found credentials file: {credentials_file}")
    else:
        print("✗ No credentials file found")
        print("Expected: credentials.json or client_secret_*.json")
