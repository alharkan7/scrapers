#!/usr/bin/env python3
"""
Debug script to check User object attributes
"""

import asyncio
from contextlib import aclosing
from twscrape import API

async def debug_user_attributes():
    """Check what attributes are available on User objects"""
    print("🔍 Debugging User object attributes")
    print("=" * 40)

    api = API()

    try:
        # Try to search for a few tweets to get user objects
        async with aclosing(api.search("test", limit=3)) as gen:
            async for tweet in gen:
                print(f"\n📝 Tweet ID: {tweet.id}")
                print(f"   Content: {tweet.rawContent[:50]}...")

                user = tweet.user
                print(f"\n👤 User: {user.username} (@{user.displayname})")

                # Check available attributes
                print("   Available attributes:")
                attrs = [attr for attr in dir(user) if not attr.startswith('_')]
                for attr in sorted(attrs):
                    try:
                        value = getattr(user, attr)
                        if not callable(value):
                            print(f"     {attr}: {value}")
                    except:
                        print(f"     {attr}: <error accessing>")

                # Specifically check following-related attributes
                print("\n   Following-related attributes:")
                following_attrs = [attr for attr in attrs if 'follow' in attr.lower()]
                for attr in following_attrs:
                    try:
                        value = getattr(user, attr)
                        if not callable(value):
                            print(f"     {attr}: {value}")
                    except Exception as e:
                        print(f"     {attr}: <error: {e}>")

                break  # Just check the first tweet

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_user_attributes())
