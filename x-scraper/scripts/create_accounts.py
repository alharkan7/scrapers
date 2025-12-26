#!/usr/bin/env python3
"""
Helper script to create multiple Twitter accounts for scraping
"""

import random
import string

def generate_username(base="scraper"):
    """Generate a random username"""
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{base}_{suffix}"

def generate_password(length=12):
    """Generate a random password"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))

def generate_email(username):
    """Generate a corresponding email (you'll need to create these)"""
    domains = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com"]
    domain = random.choice(domains)
    return f"{username}@{domain}"

def create_accounts_file(num_accounts=3):
    """Create accounts.txt with multiple fresh accounts"""
    print(f"🎯 Creating {num_accounts} fresh Twitter accounts configuration")
    print("=" * 50)

    accounts = []

    for i in range(num_accounts):
        username = generate_username()
        password = generate_password()
        email = generate_email(username)
        email_password = "your_email_password_here"  # You'll need to set this

        account_line = f"{username}:{password}:{email}:{email_password}"
        accounts.append(account_line)

        print(f"\n📝 Account {i+1}:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        print(f"   ⚠️  You'll need to:")
        print(f"      1. Create this email account")
        print(f"      2. Create Twitter account with these credentials")
        print(f"      3. Replace '{email_password}' with actual email password")

    # Write to accounts.txt
    with open('accounts.txt', 'w') as f:
        f.write('\n'.join(accounts))
        f.write('\n')  # Add trailing newline

    print("
✅ Created accounts.txt with fresh accounts"    print(f"📁 Total accounts: {num_accounts}")
    print("\n⚠️  IMPORTANT: You must manually create these accounts on Twitter first!")
    print("   1. Create the email accounts")
    print("   2. Create Twitter accounts using those emails")
    print("   3. Update email passwords in accounts.txt")
    print("   4. Then run: twscrape add_accounts accounts.txt username:password:email:email_password")
    print("   5. Then run: twscrape login_accounts")

if __name__ == "__main__":
    print("🐦 Twitter Account Generator for Scraping")
    print("=" * 40)

    try:
        num = int(input("How many accounts to create? (default 3): ").strip() or "3")
        create_accounts_file(num)
    except ValueError:
        print("❌ Invalid number. Using default of 3 accounts.")
        create_accounts_file(3)
    except KeyboardInterrupt:
        print("\n❌ Cancelled.")
