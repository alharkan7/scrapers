#!/usr/bin/env python3
"""
Setup script for X/Twitter scraper
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✓ Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("X/Twitter Scraper Setup")
    print("=======================")

    # Check Python version
    print(f"Python version: {sys.version}")

    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("Failed to install dependencies. Please check your Python/pip setup.")
        return

    # Create output directory
    os.makedirs('output', exist_ok=True)
    print("✓ Created output directory")

    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Create accounts.txt file with your Twitter accounts")
    print("2. Run: twscrape add_accounts accounts.txt username:password:email:email_password")
    print("3. Run: twscrape login_accounts")
    print("4. Run: python scraper.py")

if __name__ == "__main__":
    main()
