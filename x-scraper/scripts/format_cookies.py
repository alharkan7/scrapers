#!/usr/bin/env python3
"""
Simple cookie formatter for Twitter
"""

import json

def format_manual_cookies():
    """Manually input cookies one by one"""
    print("🍪 Twitter Cookie Formatter")
    print("=" * 30)
    print("Enter cookie values from Chrome DevTools > Application > Cookies")
    print("(Press Enter to skip optional cookies)")
    print()

    cookies = {}

    # Required cookies
    auth_token = input("auth_token value: ").strip()
    if auth_token:
        cookies['auth_token'] = auth_token

    ct0 = input("ct0 value: ").strip()
    if ct0:
        cookies['ct0'] = ct0

    # Optional but helpful
    twid = input("twid value (optional): ").strip()
    if twid:
        cookies['twid'] = twid

    guest_id = input("guest_id value (optional): ").strip()
    if guest_id:
        cookies['guest_id'] = guest_id

    personalization_id = input("personalization_id value (optional): ").strip()
    if personalization_id:
        cookies['personalization_id'] = personalization_id

    if not cookies:
        print("❌ No cookies entered!")
        return

    # Format for twscrape
    cookie_json = json.dumps(cookies, separators=(',', ':'))

    print("\n✅ Formatted cookies:")
    print(cookie_json)
    print()

    username = input("Enter your Twitter username (without @): ").strip()
    if username:
        account_line = f"{username}:::{cookie_json}"
        print(f"\n📝 Add this to accounts.txt:")
        print(account_line)

        save = input("\nSave to accounts.txt? (y/n): ").strip().lower()
        if save == 'y':
            with open('accounts.txt', 'w') as f:
                f.write(account_line + '\n')
            print("✅ Saved to accounts.txt")
            print("\n🚀 Now run:")
            print("twscrape add_accounts accounts.txt username:::cookies")
    else:
        print("⚠️  Remember to add your username when creating accounts.txt")

if __name__ == "__main__":
    format_manual_cookies()
