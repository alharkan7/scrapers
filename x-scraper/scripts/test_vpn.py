#!/usr/bin/env python3
"""
Quick VPN connection test for Twitter scraping
"""

import subprocess
import json

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "Error"

def test_vpn():
    """Test VPN connection and Twitter access"""
    print("🧪 VPN & Twitter Access Test")
    print("=" * 35)

    # Test 1: IP and location
    print("\n1. 🌐 Network Status:")
    ip = run_cmd("curl -s ifconfig.me")
    country = run_cmd("curl -s ipinfo.io/country")
    print(f"   IP: {ip}")
    print(f"   Country: {country}")

    # Test 2: Twitter API access
    print("\n2. 🐦 Twitter API Access:")
    api_test = run_cmd('curl -s -o /dev/null -w "%{http_code}" "https://api.twitter.com/2/users/by/username/elonmusk" -H "Authorization: Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"')
    status = "✅ Working" if api_test == "200" else "❌ Blocked"
    print(f"   API Status: {api_test} ({status})")

    # Test 3: Account status
    print("\n3. 👤 Account Status:")
    try:
        result = subprocess.run("twscrape accounts", shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and "username" in result.stdout:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                print(f"   Accounts configured: {len(lines) - 1}")
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            username = parts[0]
                            logged_in = parts[1]
                            active = parts[2]
                            status_icon = "✅" if logged_in == "1" and active == "1" else "❌"
                            print(f"   {status_icon} {username}: logged_in={logged_in}, active={active}")
            else:
                print("   No accounts configured")
        else:
            print("   Error checking accounts")
    except:
        print("   Could not check accounts")

    # Summary
    print("\n" + "=" * 35)
    if country == "US" and api_test == "200":
        print("🎉 VPN WORKING! Ready to scrape.")
        print("Run: twscrape login_accounts")
    elif country == "US":
        print("⚠️  VPN connected but Twitter still blocked.")
        print("Try different US server or paid VPN.")
    else:
        print("❌ VPN not working system-wide.")
        print("Install proper VPN app (not Chrome extension).")
        print("Run: ./setup_vpn.sh")

if __name__ == "__main__":
    test_vpn()
