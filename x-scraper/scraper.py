#!/usr/bin/env python3
"""
X/Twitter Scraper using twscrape library
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from contextlib import aclosing

from twscrape import API, gather
from twscrape.logger import set_log_level


class TwitterScraper:
    def __init__(self):
        self.api = API()

    async def search_tweets(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search for tweets using a query"""
        tweets = []
        try:
            async with aclosing(self.api.search(query, limit=limit)) as gen:
                async for tweet in gen:
                    tweet_data = {
                        'id': tweet.id,
                        'url': tweet.url,
                        'date': tweet.date.isoformat() if tweet.date else None,
                        'content': tweet.rawContent,
                        'username': tweet.user.username,
                        'display_name': tweet.user.displayname,
                        'user_id': tweet.user.id,
                        'verified': getattr(tweet.user, 'verified', False),
                        'followers_count': getattr(tweet.user, 'followersCount', 0),
                        'following_count': getattr(tweet.user, 'followingCount', getattr(tweet.user, 'friendsCount', 0)),
                        'reply_count': getattr(tweet, 'replyCount', 0),
                        'retweet_count': getattr(tweet, 'retweetCount', 0),
                        'like_count': getattr(tweet, 'likeCount', 0),
                        'quote_count': getattr(tweet, 'quoteCount', 0),
                        'view_count': getattr(tweet, 'viewCount', 0),
                        'lang': getattr(tweet, 'lang', ''),
                        'source': getattr(tweet, 'sourceLabel', ''),
                        'hashtags': [getattr(tag, 'text', str(tag)) for tag in getattr(tweet, 'hashtags', []) or []],
                        'mentioned_users': [user.username for user in getattr(tweet, 'mentionedUsers', []) or []],
                        'links': [{
                            'text': getattr(link, 'text', ''),
                            'url': getattr(link, 'url', ''),
                            'type': getattr(link, 'type', 'unknown')
                        } for link in getattr(tweet, 'links', []) or []],
                        'media': [{
                            'type': getattr(media, 'type', 'unknown'),
                            'url': getattr(media, 'url', ''),
                            'alt': getattr(media, 'alt', '')
                        } for media in (tweet.media if isinstance(tweet.media, list) else [tweet.media] if tweet.media else [])]
                    }
                    tweets.append(tweet_data)
                    print(f"Collected tweet {len(tweets)}/{limit}: {tweet.id}")
        except Exception as e:
            print(f"Error searching tweets: {e}")

        return tweets

    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get detailed user information"""
        try:
            user = await self.api.user_by_login(username)
            return {
                'id': user.id,
                'username': user.username,
                'display_name': user.displayname,
                'description': getattr(user, 'rawDescription', ''),
                'verified': getattr(user, 'verified', False),
                'protected': getattr(user, 'protected', False),
                'followers_count': getattr(user, 'followersCount', 0),
                'following_count': getattr(user, 'followingCount', getattr(user, 'friendsCount', 0)),
                'statuses_count': getattr(user, 'statusesCount', 0),
                'favourites_count': getattr(user, 'favouritesCount', 0),
                'listed_count': getattr(user, 'listedCount', 0),
                'media_count': getattr(user, 'mediaCount', 0),
                'location': getattr(user, 'location', ''),
                'url': getattr(user, 'url', ''),
                'joined_date': user.created.isoformat() if getattr(user, 'created', None) else None,
                'profile_banner_url': getattr(user, 'profileBannerUrl', ''),
                'profile_image_url': getattr(user, 'profileImageUrl', '')
            }
        except Exception as e:
            print(f"Error getting user info for {username}: {e}")
            return {}

    async def get_user_tweets(self, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent tweets from a user"""
        try:
            user = await self.api.user_by_login(username)
            tweets = await gather(self.api.user_tweets(user.id, limit=limit))
            return [{
                'id': tweet.id,
                'url': tweet.url,
                'date': tweet.date.isoformat() if tweet.date else None,
                'content': tweet.rawContent,
                'reply_count': tweet.replyCount,
                'retweet_count': tweet.retweetCount,
                'like_count': tweet.likeCount,
                'view_count': tweet.viewCount
            } for tweet in tweets]
        except Exception as e:
            print(f"Error getting tweets for {username}: {e}")
            return []

    async def get_followers(self, username: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get followers of a user"""
        try:
            user = await self.api.user_by_login(username)
            followers = await gather(self.api.followers(user.id, limit=limit))
            return [{
                'id': follower.id,
                'username': follower.username,
                'display_name': follower.displayname,
                'verified': getattr(follower, 'verified', False),
                'followers_count': getattr(follower, 'followersCount', 0),
                'following_count': getattr(follower, 'followingCount', getattr(follower, 'friendsCount', 0)),
                'description': getattr(follower, 'rawDescription', '')
            } for follower in followers]
        except Exception as e:
            print(f"Error getting followers for {username}: {e}")
            return []

    def save_to_json(self, data: Any, filename: str):
        """Save data to JSON file"""
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Data saved to {filepath}")


async def main():
    # Disable debug logging for cleaner output
    set_log_level("INFO")

    scraper = TwitterScraper()

    print("X/Twitter Scraper")
    print("=================")

    # Check if accounts are configured
    try:
        accounts = await scraper.api.pool.get_all()
        if not accounts:
            print("No accounts configured!")
            print("Please add Twitter accounts first using the CLI:")
            print("twscrape add_accounts accounts.txt username:password:email:email_password")
            print("Then login: twscrape login_accounts")
            return

        active_accounts = [acc for acc in accounts if acc.active]
        inactive_accounts = [acc for acc in accounts if not acc.active]

        print(f"Found {len(accounts)} total accounts")
        print(f"- {len(active_accounts)} active accounts")
        print(f"- {len(inactive_accounts)} inactive accounts")

        if not active_accounts:
            print("\n❌ No active accounts found!")
            print("\nTo fix this:")
            print("1. Run: twscrape login_accounts")
            print("2. If login fails due to Cloudflare:")
            print("   - Use a different IP/proxy")
            print("   - Try manual login: twscrape login_accounts --manual")
            print("   - Use fresh accounts not previously flagged")
            print("\nAlternatively, you can try basic scraping without login (limited functionality)")
            try:
                choice = input("\nTry basic scraping without login? (y/n): ").strip().lower()
                if choice != 'y':
                    return
            except EOFError:
                print("\n⚠️  Non-interactive mode detected.")
                print("To run interactively: python3 scraper.py")
                print("For CLI usage: twscrape search \"query\" --limit=100")
                return
            print("⚠️  Note: Some features may not work without logged-in accounts")
        else:
            print("✅ Ready to scrape!")

    except Exception as e:
        print(f"Error checking accounts: {e}")
        print("Please ensure accounts are properly configured.")
        return

    print("\nAvailable operations:")
    print("1. Search tweets")
    print("2. Get user information")
    print("3. Get user tweets")
    print("4. Get user followers")
    print("5. Exit")

    while True:
        try:
            choice = input("\nSelect operation (1-5): ").strip()

            if choice == '1':
                query = input("Enter search query: ").strip()
                limit = int(input("Enter limit (default 100): ").strip() or "100")
                print(f"Searching for '{query}' with limit {limit}...")

                tweets = await scraper.search_tweets(query, limit)
                scraper.save_to_json(tweets, f"search_{query.replace(' ', '_')}.json")
                print(f"Collected {len(tweets)} tweets")

            elif choice == '2':
                username = input("Enter username (without @): ").strip()
                print(f"Getting info for @{username}...")

                user_info = await scraper.get_user_info(username)
                if user_info:
                    scraper.save_to_json(user_info, f"user_{username}.json")
                    print(f"User info saved for @{username}")
                else:
                    print("User not found or error occurred")

            elif choice == '3':
                username = input("Enter username (without @): ").strip()
                limit = int(input("Enter limit (default 50): ").strip() or "50")
                print(f"Getting tweets for @{username} with limit {limit}...")

                tweets = await scraper.get_user_tweets(username, limit)
                scraper.save_to_json(tweets, f"tweets_{username}.json")
                print(f"Collected {len(tweets)} tweets")

            elif choice == '4':
                username = input("Enter username (without @): ").strip()
                limit = int(input("Enter limit (default 100): ").strip() or "100")
                print(f"Getting followers for @{username} with limit {limit}...")

                followers = await scraper.get_followers(username, limit)
                scraper.save_to_json(followers, f"followers_{username}.json")
                print(f"Collected {len(followers)} followers")

            elif choice == '5':
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Please select 1-5.")

        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            break
        except ValueError as e:
            print(f"Invalid input: {e}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
