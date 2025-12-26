#!/bin/bash

echo "X/Twitter Scraper Setup & Run Script"
echo "===================================="

# Check if accounts.txt exists
if [ ! -f "accounts.txt" ]; then
    echo ""
    echo "❌ accounts.txt not found!"
    echo "Please create accounts.txt with your Twitter account details."
    echo "See accounts.txt.example for the format."
    echo ""
    echo "Required format:"
    echo "username:password:email:email_password"
    echo ""
    exit 1
fi

echo "✅ Found accounts.txt"

# Check if accounts are configured
echo ""
echo "Checking configured accounts..."
if ! twscrape accounts > /dev/null 2>&1; then
    echo "No accounts configured. Adding accounts..."
    twscrape add_accounts accounts.txt username:password:email:email_password

    if [ $? -ne 0 ]; then
        echo "❌ Failed to add accounts. Please check your accounts.txt format."
        exit 1
    fi
fi

echo "✅ Accounts configured"

# Check login status
echo ""
echo "Checking account login status..."
LOGIN_STATUS=$(twscrape accounts | grep -E "(True|False)" | head -1)

if echo "$LOGIN_STATUS" | grep -q "False"; then
    echo "Some accounts are not logged in. Starting login process..."
    echo "Note: You may need to enter email verification codes."
    echo "Use Ctrl+C if you prefer manual verification later."

    twscrape login_accounts --manual
else
    echo "✅ All accounts appear to be logged in"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Available commands:"
echo "- Run interactive scraper: python scraper.py"
echo "- List accounts: twscrape accounts"
echo "- Search tweets: twscrape search \"query\" --limit=100"
echo "- Get user info: twscrape user_by_login username"
echo ""
echo "Happy scraping! Remember to respect Twitter's terms of service."
