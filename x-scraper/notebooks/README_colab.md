# X/Twitter Scraper - Colab Edition

This repository contains tools to scrape X (Twitter) data and convert the results to pandas DataFrames for analysis.

## Files Overview

- `scraper.py` - Original command-line scraper script
- `x_scraper_colab.ipynb` - Google Colab notebook version of the scraper
- `json_to_pandas.py` - Command-line tool to convert JSON output to pandas DataFrames
- `pandas_converter_colab.ipynb` - Colab notebook for data analysis and conversion
- `convert_json_to_csv.py` - Additional conversion utilities

## Quick Start with Google Colab

### 1. Scrape Data

1. Open [x_scraper_colab.ipynb](x_scraper_colab.ipynb) in Google Colab
2. Run the setup cell to install dependencies
3. Upload or create your `accounts.txt` file with Twitter credentials
4. Configure your scraping operation using the form widgets
5. Run the desired scraping cell
6. Download your results

### 2. Analyze Data

1. Open [pandas_converter_colab.ipynb](pandas_converter_colab.ipynb) in Google Colab
2. Upload your JSON files from the scraper
3. Run the conversion cells
4. Use the analysis tools to explore your data
5. Export to CSV if needed

## Account Setup

To scrape Twitter data, you need Twitter accounts configured. The format for `accounts.txt` is:

```
username1:password1:email1@email.com:email_password1
username2:password2:email2@email.com:email_password2
```

**⚠️ Important:** Use dedicated accounts and respect Twitter's terms of service.

## Usage Examples

### Command Line

```bash
# Convert all JSON files to pandas (with stats)
python3 json_to_pandas.py --stats

# Convert specific file to CSV
python3 json_to_pandas.py --file tweets_elonmusk.json --csv

# Interactive mode
python3 json_to_pandas.py --interactive
```

### In Colab Notebooks

The notebooks provide user-friendly interfaces with:
- Form widgets for easy configuration
- File upload/download capabilities
- Built-in data visualization
- One-click CSV export

## Data Types

The scraper produces different types of JSON data:

### Tweets Data (`search_*.json`, `tweets_*.json`)
- Tweet content, metadata, and engagement metrics
- User information for each tweet
- Media, links, hashtags, and mentions

### User Info (`user_*.json`)
- Detailed profile information
- Account statistics and settings
- Profile images and banner URLs

### Followers (`followers_*.json`)
- List of user followers
- Basic profile information for each follower

## Pandas DataFrames

The converter automatically enhances the data with:

- **Tweets**: Engagement scores, hashtag/mention counts, media detection
- **Users**: Account age, follower/following ratios
- **Followers**: Follower/following ratios

## Dependencies

- `twscrape` - Twitter scraping library
- `pandas` - Data manipulation and analysis
- `matplotlib` / `seaborn` - Data visualization (optional)

## Colab-Specific Features

- **Nested event loop support** with `nest_asyncio`
- **File upload/download** through Colab interface
- **Interactive widgets** for easy parameter configuration
- **Built-in data preview** and analysis tools

## Troubleshooting

### Account Issues
- Ensure accounts are properly logged in using `twscrape login_accounts`
- Try using fresh accounts not previously flagged
- Consider using VPN/proxy if Cloudflare blocks occur

### Rate Limiting
- The scraper includes automatic rate limiting
- Space out your requests
- Use multiple accounts for larger scrapes

### Colab Timeouts
- Long-running scrapes may timeout in Colab
- Consider breaking large tasks into smaller batches
- Use the command-line version for very large datasets

## Output Analysis

Use the pandas converter to:

1. **Explore data structure**: `df.info()`, `df.describe()`
2. **Find top content**: Sort by engagement metrics
3. **Analyze trends**: Group by date, user, or topic
4. **Export for further analysis**: Save to CSV/Excel

## Example Analysis Code

```python
import pandas as pd

# Load tweets data
df_tweets = pd.read_csv('search_AI_technology.csv')

# Find most engaging tweets
top_tweets = df_tweets.nlargest(10, 'engagement_score')

# Analyze hashtag usage
hashtag_counts = df_tweets['hashtags'].str.split(', ').explode().value_counts()

# Plot engagement over time
df_tweets['date'] = pd.to_datetime(df_tweets['date'])
df_tweets.set_index('date')['engagement_score'].plot()
```

## License

Please respect Twitter's terms of service and robots.txt when scraping. Use responsibly and ethically.
