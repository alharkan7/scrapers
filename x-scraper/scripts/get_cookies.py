#!/usr/bin/env python3
"""
Cookie extractor and formatter for Twitter scraping
"""

import json
import base64
from urllib.parse import unquote

def format_cookies_for_twscrape(cookie_data):
    """
    Format Chrome cookie export for twscrape
    Supports multiple input formats
    """
    try:
        # Try to parse as JSON first (from EditThisCookie)
        if isinstance(cookie_data, str):
            if cookie_data.strip().startswith('{'):
                cookies = json.loads(cookie_data)
            elif cookie_data.strip().startswith('['):
                cookies = json.loads(cookie_data)
            else:
                # Try base64 decode
                try:
                    decoded = base64.b64decode(cookie_data).decode('utf-8')
                    cookies = json.loads(decoded)
                except:
                    print("❌ Invalid cookie format. Please check the format.")
                    return None
        else:
            cookies = cookie_data

        # Handle different cookie formats
        if isinstance(cookies, dict):
            # Single cookie object
            cookies = [cookies]
        elif not isinstance(cookies, list):
            print("❌ Cookies must be a list or single cookie object")
            return None

        # Extract Twitter/X relevant cookies
        twitter_cookies = {}
        for cookie in cookies:
            name = cookie.get('name', cookie.get('key', ''))
            value = cookie.get('value', '')

            # Twitter/X important cookies
            important_cookies = [
                'auth_token', 'ct0', 'twid', 'session_id',
                'lang', 'dnt', 'guest_id', 'personalization_id'
            ]

            if name in important_cookies or name.startswith('_twitter_') or name.startswith('twid'):
                twitter_cookies[name] = value

        if not twitter_cookies:
            print("⚠️  No Twitter cookies found. Make sure you're logged into twitter.com")
            return None

        # Format for twscrape (JSON string)
        cookie_string = json.dumps(twitter_cookies, separators=(',', ':'))

        print("✅ Extracted Twitter cookies:")
        for name, value in twitter_cookies.items():
            print(f"   {name}: {value[:20]}{'...' if len(value) > 20 else ''}")

        print(f"\n📋 Formatted cookie string ({len(cookie_string)} chars):")
        print(cookie_string)

        return cookie_string

    except Exception as e:
        print(f"❌ Error processing cookies: {e}")
        return None

def create_accounts_with_cookies():
    """Help create accounts.txt with cookies"""
    print("🍪 Twitter Cookie Setup for twscrape")
    print("=" * 40)

    username = input("Enter Twitter username (without @): ").strip()
    if not username:
        print("❌ Username required")
        return

    print("\n📋 Paste your cookie data below (from Chrome DevTools or EditThisCookie):")
    print("   Press Enter twice when done, or Ctrl+D to finish")
    print()

    cookie_lines = []
    try:
        while True:
            line = input()
            if line.strip() == "":
                break
            cookie_lines.append(line)
    except EOFError:
        pass

    cookie_data = '\n'.join(cookie_lines)

    if not cookie_data.strip():
        print("❌ No cookie data provided")
        return

    # Process cookies
    formatted_cookies = format_cookies_for_twscrape(cookie_data)

    if formatted_cookies:
        # Create accounts.txt entry
        account_line = f"{username}:::{formatted_cookies}"

        print("\n📝 Add this line to your accounts.txt:")
        print(account_line)

        # Offer to update accounts.txt
        update_file = input("\nUpdate accounts.txt automatically? (y/n): ").strip().lower()
        if update_file == 'y':
            try:
                with open('accounts.txt', 'w') as f:
                    f.write(account_line + '\n')
                print("✅ Updated accounts.txt")
                print("\n🚀 Now run:")
                print("   twscrape add_accounts accounts.txt username:::cookies")
                print("   python3 scraper.py")
            except Exception as e:
                print(f"❌ Error updating file: {e}")
        else:
            print("\n📋 Manual steps:")
            print("1. Add the line above to accounts.txt")
            print("2. Run: twscrape add_accounts accounts.txt username:::cookies")
            print("3. Run: python3 scraper.py")

def test_cookie_login():
    """Test if cookies work"""
    print("🧪 Testing Cookie-Based Login")
    print("=" * 30)

    try:
        import asyncio
        from twscrape import API

        async def test():
            api = API()
            accounts = await api.pool.get_all()

            if not accounts:
                print("❌ No accounts configured")
                return

            print(f"Found {len(accounts)} account(s):")
            for acc in accounts:
                status = "✅ Active" if acc.active else "❌ Inactive"
                login_status = "✅ Logged in" if acc.logged_in else "❌ Not logged in"
                print(f"  {acc.username}: {status}, {login_status}")

                if acc.active and acc.logged_in:
                    print("🎉 Account ready for scraping!")
                    return True

            print("⚠️  No active logged-in accounts found")
            return False

        return asyncio.run(test())

    except Exception as e:
        print(f"❌ Error testing accounts: {e}")
        return False

if __name__ == "__main__":
    print("🍪 Twitter Cookie Extractor & Setup")
    print("=" * 40)

    print("Choose an option:")
    print("1. Extract and format cookies")
    print("2. Test current cookie-based accounts")
    print("3. Get cookie extraction instructions")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == '1':
        create_accounts_with_cookies()
    elif choice == '2':
        test_cookie_login()
    elif choice == '3':
        print("""
📖 COOKIE EXTRACTION INSTRUCTIONS:
==================================

Method 1: Chrome DevTools (Recommended)
--------------------------------------
1. Open Chrome and go to https://twitter.com
2. Login to your account
3. Press F12 or right-click → Inspect
4. Go to Application tab → Cookies → https://twitter.com
5. Copy all cookie data as JSON

Method 2: EditThisCookie Extension
----------------------------------
1. Install extension: https://chromewebstore.google.com/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg
2. Go to twitter.com (logged in)
3. Click extension icon → Export → As JSON
4. Copy the entire JSON

Method 3: Manual Copy-Paste
---------------------------
1. Login to twitter.com
2. Open DevTools → Console
3. Run: copy(document.cookie)
4. Paste the result

Then run: python3 get_cookies.py
Choose option 1 and paste your cookies
        """)
    else:
        print("❌ Invalid choice")
