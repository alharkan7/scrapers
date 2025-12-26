#!/usr/bin/env python3
"""
Test different proxy/VPN configurations for Twitter scraping
"""

import asyncio
import subprocess
import sys
from contextlib import aclosing
from twscrape import API
from twscrape.logger import set_log_level

async def test_connection(proxy=None):
    """Test connection to Twitter with optional proxy"""
    print(f"\n🧪 Testing connection{' with proxy' if proxy else ''}...")

    if proxy:
        api = API(proxy=proxy)
        print(f"   Using proxy: {proxy}")
    else:
        api = API()
        print("   Using direct connection")

    try:
        # Try a simple search (should work without login for basic connectivity)
        async with aclosing(api.search("test", limit=1)) as gen:
            tweet = await gen.__anext__()
            print("✅ Connection successful!")
            print(f"   Found tweet: {tweet.id}")
            print(f"   Content: {tweet.rawContent[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def main():
    print("🌐 Twitter Connection Test")
    print("=" * 30)

    # Test 1: Direct connection
    direct_ok = await test_connection()

    if direct_ok:
        print("\n🎉 Direct connection works! You can proceed with scraping.")
        return

    print("\n❌ Direct connection blocked. Trying proxy options...")

    # Common proxy services (you'll need to configure these)
    proxy_options = [
        # Residential proxies (recommended for Twitter)
        # "http://username:password@proxy.residential-proxy.com:8080",

        # SOCKS5 proxies
        # "socks5://username:password@proxy.socks5.com:1080",

        # Free proxies (not recommended for production)
        # "http://free-proxy-list.net:8080",
    ]

    if not proxy_options or proxy_options[0].startswith("#"):
        print("\n📝 No proxies configured. Here's how to add them:")
        print("1. Get residential proxies from:")
        print("   - Bright Data (luminati.io)")
        print("   - Smart Proxy (smartproxy.com)")
        print("   - Oxylabs (oxylabs.io)")
        print("2. Or use VPN services:")
        print("   - ExpressVPN, NordVPN, ProtonVPN")
        print("3. Add proxy to proxy_options list in this script")

        print("\n🔧 Manual testing commands:")
        print("# Test with VPN enabled:")
        print("python3 proxy_test.py")
        print("\n# Test specific proxy:")
        print('API(proxy="http://user:pass@proxy.com:8080")')

    else:
        # Test configured proxies
        for i, proxy in enumerate(proxy_options, 1):
            print(f"\n🔄 Testing proxy {i}/{len(proxy_options)}...")
            await test_connection(proxy)

    print("\n" + "=" * 30)
    print("💡 Recommendations:")
    print("1. Use residential proxies (not datacenter)")
    print("2. Rotate IP addresses frequently")
    print("3. Use clean accounts not previously flagged")
    print("4. Consider VPN services for development")

if __name__ == "__main__":
    asyncio.run(main())
