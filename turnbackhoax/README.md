# Turn Back Hoax Scraper

A comprehensive Python scraper for [turnbackhoax.id](https://turnbackhoax.id) that can scrape headlines, full article content, and process scraped data.

## Features

1. **Scrape Headlines**: Extract article headlines, URLs, previews, images, dates, and authors from multiple pages
2. **Scrape Full Articles**: Download complete article content including categories from URLs listed in a Google Sheet
3. **Clean Data**: Process and clean scraped data with custom text formatting

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or if you're using Python 3:

```bash
pip3 install -r requirements.txt
```

## Configuration

Before running the scraper, edit the configuration variables at the top of `scraping_turn_back_hoax.py`:

```python
# Page range for scraping headlines
START_PAGE = 1
END_PAGE = 226

# Google Sheet configuration for article scraping
SHEET_ID = ""  # Your Google Sheet ID
SHEET_NAME = ""  # Your Google Sheet gid
```

## Usage

The scraper has three modes of operation:

### 1. Scrape Headlines

Scrape article headlines from multiple pages:

```bash
python3 scraping_turn_back_hoax.py headlines
```

With custom page range:

```bash
python3 scraping_turn_back_hoax.py headlines --start 1 --end 10
```

**Output**: `turnbackhoax_headlines_TIMESTAMP.csv`

### 2. Scrape Full Articles

Scrape full article content from URLs in a Google Sheet:

```bash
python3 scraping_turn_back_hoax.py articles
```

With custom Google Sheet:

```bash
python3 scraping_turn_back_hoax.py articles --sheet-id YOUR_SHEET_ID --sheet-name YOUR_SHEET_NAME
```

**Requirements**:
- Column C (index 2): Article URLs
- Column H (index 7): Boolean flag (True = scrape this article)

**Output**: `turnbackhoax_articles_TIMESTAMP.csv`

### 3. Clean Data

Process and clean data from Google Sheet:

```bash
python3 scraping_turn_back_hoax.py clean
```

**Output**: 
- `processed_sheet_TIMESTAMP.csv`
- `processed_column_g_TIMESTAMP.txt`

## Command-Line Arguments

- `mode`: Required. Choose from `headlines`, `articles`, or `clean`
- `--start`: Starting page number (for headlines mode)
- `--end`: Ending page number (for headlines mode)
- `--sheet-id`: Google Sheet ID (overrides config)
- `--sheet-name`: Google Sheet name/gid (overrides config)

## Examples

```bash
# Scrape headlines from pages 1-50
python3 scraping_turn_back_hoax.py headlines --start 1 --end 50

# Scrape articles from specific Google Sheet
python3 scraping_turn_back_hoax.py articles --sheet-id "1abc..." --sheet-name "0"

# Clean data
python3 scraping_turn_back_hoax.py clean
```

## Output Files

All output files are saved with timestamps to avoid overwriting:

- Headlines: `turnbackhoax_headlines_YYYYMMDD_HHMMSS.csv`
- Articles: `turnbackhoax_articles_YYYYMMDD_HHMMSS.csv`
- Cleaned data: `processed_sheet_YYYYMMDD_HHMMSS.csv` and `processed_column_g_YYYYMMDD_HHMMSS.txt`

## Rate Limiting

The scraper includes a 1-second delay between requests to be respectful to the server. Do not modify this unless you have permission from the site owner.

## Original Source

This script is a Python conversion of the original Jupyter notebook: `Scraping_Turn_Back_Hoax.ipynb`

## Dependencies

- `requests`: HTTP library for making web requests
- `beautifulsoup4`: HTML parsing library
- `pandas`: Data manipulation and CSV handling
- `tqdm`: Progress bar display
- `lxml`: XML/HTML parser (optional but recommended for better performance)

## License

Please respect the website's robots.txt and terms of service when scraping.
