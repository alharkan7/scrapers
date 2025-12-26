#!/usr/bin/env python3
"""
Fix accounts configuration for X/Twitter scraper
Run this script when you get "No accounts configured" error
"""

import subprocess
import os
import sys

def check_accounts_file():
    """Check if accounts.txt exists and has content"""
    if not os.path.exists('accounts.txt'):
        print("❌ accounts.txt not found!")
        print("Please create an accounts.txt file with your Twitter credentials.")
        print("Format: username:password:email:email_password")
        return False

    with open('accounts.txt', 'r') as f:
        content = f.read().strip()

    if not content:
        print("❌ accounts.txt is empty!")
        return False

    lines = content.split('\n')
    print(f"✅ Found accounts.txt with {len(lines)} account(s)")

    for i, line in enumerate(lines, 1):
        if line.strip():
            parts = line.split(':')
            if len(parts) != 4:
                print(f"⚠️ Line {i}: Invalid format (expected 4 parts separated by ':')")
                print(f"   Line: {line}")
            else:
                username, password, email, email_password = parts
                print(f"   Account {i}: {username} ({email})")

    return True

def setup_accounts():
    """Setup accounts using twscrape commands"""
    print("\n🔧 Setting up accounts...")

    try:
        # Check if twscrape is available
        result = subprocess.run(['twscrape', '--version'],
                              capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            print("❌ twscrape command not found!")
            print("Make sure twscrape is installed and available in PATH")
            return False

        print("✅ twscrape found")

        # Add accounts from file
        print("📝 Adding accounts from accounts.txt...")
        result = subprocess.run(
            ['twscrape', 'add_accounts', 'accounts.txt', 'username:password:email:email_password'],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            print(f"❌ Failed to add accounts: {result.stderr}")
            return False

        print("✅ Accounts added successfully")

        # Login to accounts
        print("🔑 Logging into accounts...")
        result = subprocess.run(
            ['twscrape', 'login_accounts'],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode != 0:
            print(f"⚠️ Login failed: {result.stderr}")
            print("💡 Try manual login: twscrape login_accounts --manual")
            return False

        print("✅ Login successful!")

        # Check accounts
        print("🔍 Checking account status...")
        result = subprocess.run(
            ['twscrape', 'accounts'],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            print("📋 Account status:")
            print(result.stdout)

        return True

    except subprocess.TimeoutExpired:
        print("❌ Operation timed out. Please try again.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🐦 X/Twitter Account Setup Fixer")
    print("=" * 40)

    if not check_accounts_file():
        sys.exit(1)

    print("\n" + "=" * 40)

    if setup_accounts():
        print("\n🎉 Setup complete! Your accounts should now be configured.")
        print("Go back to your notebook and run the scraper.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure your accounts.txt has the correct format")
        print("2. Try manual login: twscrape login_accounts --manual")
        print("3. Use fresh accounts if existing ones are flagged")
        print("4. Check your internet connection")

if __name__ == "__main__":
    main()
