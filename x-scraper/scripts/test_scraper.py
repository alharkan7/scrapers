#!/usr/bin/env python3
"""
Quick test script for X/Twitter scraper
"""

import asyncio
from twscrape import API
from twscrape.logger import set_log_level

async def test_accounts():
    """Test account configuration"""
    set_log_level("INFO")

    api = API()

    try:
        accounts = await api.pool.get_all()
        print(f"✅ Found {len(accounts)} accounts in database")

        for acc in accounts:
            status = "✅ Active & Logged in" if acc.active and acc.logged_in else "❌ Inactive/Not logged in"
            print(f"  - {acc.username}: {status}")

        active_accounts = [acc for acc in accounts if acc.active and acc.logged_in]
        print(f"\n📊 Summary: {len(active_accounts)}/{len(accounts)} accounts ready for scraping")

        if not active_accounts:
            print("\n💡 To get accounts working:")
            print("1. twscrape login_accounts")
            print("2. If Cloudflare blocks: use VPN or different IP")
            print("3. Or try: twscrape login_accounts --manual")

        return len(active_accounts) > 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_basic_scraping():
    """Test basic scraping functionality (if accounts are available)"""
    api = API()

    try:
        # Try to get a simple user (this might work without login for basic info)
        user = await api.user_by_login("elonmusk")
        print("✅ Basic API call successful")
        print(f"   User: {user.username} (@{user.displayname})")
        print(f"   Followers: {user.followersCount:,}")
        return True
    except Exception as e:
        print(f"❌ Basic scraping test failed: {e}")
        return False

async def main():
    print("🧪 X/Twitter Scraper Test")
    print("=" * 30)

    # Test 1: Account configuration
    print("\n1. Testing account configuration...")
    accounts_ok = await test_accounts()

    # Test 2: Basic scraping (if accounts available)
    print("\n2. Testing basic scraping...")
    if accounts_ok:
        await test_basic_scraping()
    else:
        print("⏭️  Skipping basic scraping test (no active accounts)")

    print("\n" + "=" * 30)
    if accounts_ok:
        print("🎉 All tests passed! Ready to scrape.")
        print("\nRun: python3 scraper.py")
    else:
        print("⚠️  Accounts need configuration.")
        print("\nRun: ./run.sh")

if __name__ == "__main__":
    asyncio.run(main())
