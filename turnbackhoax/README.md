# Turn Back Hoax Scraper

A comprehensive Python scraper for [turnbackhoax.id](https://turnbackhoax.id) that can scrape headlines, full article content, and process/clean scraped data.

## Directory Structure

```
turnbackhoax/
├── scripts/                  # Python scripts for scraping and analysis
│   ├── scrape_by_id.py              # Main scraper by article ID
│   ├── scraping_turn_back_hoax.py   # Alternative scraper (Google Sheets)
│   ├── scraping_turnbackhoax_v1.py  # Version 1 scraper
│   ├── process_data/                # Data processing and investigation scripts
│   │   ├── deep_investigate.py      # Investigates patterns for programmatic data filling
│   │   ├── investigate_unparsed.py  # Scans for missing/unparsed data across columns
│   │   ├── transform_data.py        # Extracts sources (e.g., social media mentions) from text
│   │   └── verify_transformation.py # Compares raw vs processed data to ensure integrity
│   └── tools/                       # Cleaning & utility scripts
│       ├── analyze_date_outliers.py # Finds date anomalies in scraped data
│       ├── clean_data.py            # Cleans HTML/JS, normalizes fonts, standardizes quotes
│       ├── combine_csv.py           # Combines different CSVs and removes URL duplicates
│       ├── find_skipped_ids.py      # Re-checks skipped URLs (404s)
│       ├── fix_multiline_csv.py     # Fixes broken CSV formatting (newlines inside fields)
│       └── merge_turnbackhoax.py    # Merges and standardizes current data with older datasets
├── data/                     # CSV files and scraped data
│   ├── turnbackhoax_articles_by_id.csv          # Main dataset
│   ├── turnbackhoax_articles_by_id_fixed.csv    # Multi-line fixed dataset
│   ├── turnbackhoax_articles_fixed_processed.csv# Processed and transformed data
│   ├── merged_turnbackhoax_data.csv             # Data merged with older 2024 dataset
│   ├── date_outliers.csv                        # Date outlier analysis
│   └── skipped_article_ids.csv                  # Missing IDs list (404s)
├── reports/                  # Documentation and analysis reports
│   ├── DATE_OUTLIERS_REPORT.md
│   ├── OUTLIERS_QUICK_REF.md
│   └── MISSING_PAGES_REPORT.md
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Features

1. **Scrape Full Articles**: Incrementally scrape complete article content, categories, text blocks, and images by iterating through article IDs.
2. **Process Data**: Investigate scraped data for unparsed text and programmatically extract primary source platforms from text.
3. **Clean Data**: Standardize formatting, repair broken multi-line CSV rows, and merge older datasets while removing duplicates.

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

*(Or use `pip3 install -r requirements.txt` depending on your environment)*

## Usage

All scripts are located in the `scripts/` directory.

### 1. Scrape Articles by ID (Recommended)

The main scraper that iterates through article IDs. This script automatically skips already-scraped IDs to resume safely.

```bash
cd scripts
python3 scrape_by_id.py
```

Edit the top of `scrape_by_id.py` to configure:
- `START_ARTICLE_ID` and `END_ARTICLE_ID`
- `MAX_CONSECUTIVE_MISSES` (stop threshold for 404s)

**Outputs**: 
- `data/turnbackhoax_articles_by_id.csv`
- `data/skipped_article_ids.csv`

### 2. Data Processing & Investigation

These scripts analyze the extracted CSVs and transform raw text into structured data. Run these from the `scripts/` directory:

```bash
# Clean up multi-line CSV breaking issues first
python3 tools/fix_multiline_csv.py

# Investigate what data is missing/unparsed
python3 process_data/investigate_unparsed.py
python3 process_data/deep_investigate.py

# Transform text (e.g., extracting social media sources)
python3 process_data/transform_data.py

# Verify that transformations didn't lose data
python3 process_data/verify_transformation.py
```

### 3. Data Cleaning & Merging Tools

Utility scripts are located in `scripts/tools/` to clean and merge datasets:

```bash
# Comprehensive data cleaning (removes HTML, ad text, normalizes quotes)
python3 tools/clean_data.py

# Merge with older 2024 dataset
python3 tools/merge_turnbackhoax.py

# Re-check your skipped 404 URLs to see if they are actually online
python3 tools/find_skipped_ids.py
```

### 4. Legacy Scrapers

*(See `scraping_turn_back_hoax.py` if you need to scrape URLs directly from a Google Sheet).*

## Rate Limiting

The main scraper includes a built-in 1-second delay between requests to be respectful to the server. Do not modify this unless you have permission from the site owner.

## Dependencies

- `requests`: HTTP library for making web requests
- `beautifulsoup4`: HTML parsing library
- `pandas`: Data manipulation and CSV handling
- `tqdm`: Progress bar display
- `lxml`: XML/HTML parser (optional but recommended)

## License

Please respect the website's `robots.txt` and terms of service when scraping.
