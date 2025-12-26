# X/Twitter Scraper

A Python scraper for X (formerly Twitter) using the [twscrape](https://github.com/vladkens/twscrape) library.

## What You Need to Prepare

### 1. Twitter/X Accounts
You need at least one Twitter/X account to scrape data. The library supports multiple accounts for better rate limit handling.

**Important:** Use dedicated accounts for scraping, not your personal accounts, as they may get rate-limited or suspended.

### 2. Account Credentials Format
Create a file called `accounts.txt` with your account details in this format:
```
username:password:email:email_password
```

Example:
```
scraper_account1:my_password123:scraper1@gmail.com:email_pass123
scraper_account2:my_password456:scraper2@gmail.com:email_pass456
```

**Required fields:**
- `username`: Twitter username
- `password`: Twitter password
- `email`: Email address associated with the account
- `email_password`: Password for the email account (needed for verification codes)

**Optional fields:**
- `cookies`: Pre-existing cookies (if you have them)
- `user_agent`: Custom user agent string

### 3. Email Access
During account login, Twitter may send verification codes to your email. The library supports:
- **IMAP access**: Most email providers (Gmail, Yahoo, etc.)
- **Manual input**: For providers like ProtonMail that don't support IMAP

### 4. Common Issues & Solutions

#### Cloudflare Blocking
Twitter/X uses Cloudflare protection that may block automated logins. If you see:
```
Failed to login: 403 - Sorry, you have been blocked
```

**Solutions:**
1. **Use a different IP address** (VPN, proxy, different network)
2. **Use fresh accounts** that haven't been flagged
3. **Try manual login**: `twscrape login_accounts --manual`
4. **Wait and retry** later (blocks are usually temporary)
5. **Use residential proxies** for better success rates

#### Account Suspension
- Use dedicated accounts for scraping
- Avoid using personal accounts
- Create new accounts if old ones get suspended
- Space out account creation to avoid patterns

## Installation & Setup

1. **Clone/Download this project**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or run the setup script:
   ```bash
   python setup.py
   ```

3. **Add your accounts:**
   ```bash
   twscrape add_accounts accounts.txt username:password:email:email_password
   ```

4. **Login to accounts:**
   ```bash
   twscrape login_accounts
   ```
   Or for manual email verification:
   ```bash
   twscrape login_accounts --manual
   ```

5. **Check account status:**
   ```bash
   twscrape accounts
   ```

## Usage

Run the scraper:
```bash
python scraper.py
```

### Available Operations

1. **Search Tweets**: Search for tweets using Twitter's advanced search syntax
2. **Get User Info**: Get detailed information about a user profile
3. **Get User Tweets**: Get recent tweets from a specific user
4. **Get User Followers**: Get followers of a specific user

### Output

All scraped data is saved as JSON files in the `output/` directory.

## Twitter Search Syntax Examples

- Basic search: `elon musk`
- With language filter: `elon musk lang:en`
- Recent tweets: `elon musk since:2024-01-01`
- From specific user: `from:elonmusk crypto`
- Hashtags: `#bitcoin OR #ethereum`
- Exclude retweets: `elon musk -filter:replies`
- Minimum likes: `elon musk min_faves:1000`

## Rate Limits & Best Practices

- **Rate limits reset every 15 minutes** per endpoint
- Each account has separate limits for different operations
- Use multiple accounts to increase limits
- Add delays between requests if needed
- Respect Twitter's terms of service

## Troubleshooting

### No accounts configured
```
twscrape add_accounts accounts.txt username:password:email:email_password
twscrape login_accounts
```

### Login issues
- Ensure email credentials are correct
- Use `--manual` flag for email verification
- Check if accounts are not suspended/banned

### Rate limiting
- Wait 15 minutes between requests
- Use multiple accounts
- Reduce request frequency

### Proxy support
If you need proxies, you can:
- Add proxy per account when adding accounts
- Set global proxy: `export TWS_PROXY="http://user:pass@proxy.com:8080"`
- Use environment variable `TWS_PROXY`

## Legal & Ethical Considerations

- **Respect Twitter's Terms of Service**
- **Don't scrape for commercial purposes without permission**
- **Use dedicated accounts, not personal ones**
- **Be mindful of rate limits**
- **Consider privacy implications**

## Advanced Usage

### CLI Commands

```bash
# Search tweets
twscrape search "elon musk" --limit=100 > tweets.json

# Get user tweets
twscrape user_tweets 44196397 --limit=50

# Get followers
twscrape followers 44196397 --limit=100

# Raw API responses
twscrape search "python" --raw --limit=10
```

### Using Different Account Databases

```bash
# Use different account file
twscrape --db accounts2.db accounts
twscrape --db accounts2.db search "query"
```
