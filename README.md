# Tools Collection

This repository contains various Python tools for different purposes.

## Mongabay Scraper

A Python script to scrape articles from Mongabay.co.id search results. Specifically designed to scrape articles about nickel mining from search queries, with support for "load more" functionality instead of traditional pagination.

### Features

- **Search-based scraping**: Scrapes articles from search results for specific queries
- **Load more functionality**: Uses Selenium to handle JavaScript "load more" buttons (not traditional pagination)
- **Article extraction**: Extracts title, URL, author, date, and image URL for each article
- **Duplicate prevention**: Automatically avoids scraping duplicate articles
- **Multiple output formats**: Save results as JSON, CSV, or both
- **Headless browser support**: Can run in headless mode for server environments

### Requirements

- Python 3.6+
- requests library
- beautifulsoup4 library
- lxml library
- selenium library
- Chrome/Chromium browser (for Selenium WebDriver)

### Installation

#### Additional Setup for Selenium

After installing Python dependencies, you need to install ChromeDriver for Selenium:

**macOS:**
```bash
# Install ChromeDriver via Homebrew
brew install chromedriver

# Or download manually from https://chromedriver.chromium.org/
```

**Ubuntu/Debian:**
```bash
sudo apt-get install chromium-chromedriver
```

**Windows:**
Download ChromeDriver from: https://chromedriver.chromium.org/

### Usage

#### Command Line Usage

**Basic usage (scrape nickel mining articles):**
```bash
python3 mongabay_scraper.py
```

**With custom query and page limit:**
```bash
python3 mongabay_scraper.py --query "tambang nikel" --max-pages 5
```

**Specify output options:**
```bash
python3 mongabay_scraper.py --output my_articles --format json --no-headless
```

**Run in visible browser mode (for debugging):**
```bash
python3 mongabay_scraper.py --no-headless
```

#### Python Usage

```python
from mongabay_scraper import scrape_mongabay_articles

# Basic usage
articles = scrape_mongabay_articles()

# With custom parameters
articles = scrape_mongabay_articles(
    query="tambang nikel",
    max_pages=10,
    output='nickel_mining_articles',
    output_format='both',
    headless=True
)

print(f"Total articles scraped: {len(articles)}")
```

### Output Format

The scraper extracts the following information for each article:
- **title**: Article headline
- **url**: Full URL to the article
- **author**: Article author
- **date**: Publication date
- **image_url**: URL to the article's featured image

### Notes

- This scraper uses Selenium because the site employs JavaScript-based "load more" functionality
- Articles are scraped until no new articles are found or max_pages limit is reached
- The scraper automatically handles duplicates and stops when no new content is available

## PDF Compressor

A Python script to compress PDF files with minimum text quality loss. This tool is particularly useful for large, image-heavy PDFs like scanned documents or books.

## Web Scraper

A Python script to scrape articles tagged with "Kesehatan" from NU Online (https://www.nu.or.id/kesehatan/). Extracts article titles, URLs, dates, times, and cover images from paginated content.

### Features

- **Filtered scraping**: Only scrapes articles that have the "Kesehatan" tag
- **Paginated scraping**: Scrape multiple pages by specifying start and end page numbers
- **Article extraction**: Extracts title, URL, date, time, and cover image URL for each article
- **Multiple output formats**: Save results as JSON, CSV, or both
- **Respectful scraping**: Includes delays between requests to avoid overwhelming the server
- **Error handling**: Gracefully handles network errors and missing data

### Requirements

- Python 3.6+
- requests library
- beautifulsoup4 library
- lxml library

### Installation

#### Virtual Environment Setup (Recommended)

To avoid conflicts with system packages, it's recommended to use a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Convenience Script:**
Alternatively, use the provided helper script:
```bash
# This will create venv if needed, activate it, and install requirements
./activate_and_run.sh pip install -r requirements.txt

# Or just activate the environment for interactive use
./activate_and_run.sh
```

#### Direct Installation

Alternatively, install dependencies directly:
```bash
pip install -r requirements.txt
```

### Usage

**Note:** If using a virtual environment, activate it first or use the convenience script:
```bash
source venv/bin/activate
# OR
./activate_and_run.sh
```

#### Command Line Usage

**Basic usage (scrape pages 1 to 5):**
```bash
python3 scraper.py 1 5
# OR using convenience script
./activate_and_run.sh python3 scraper.py 1 5
```

**Specify output filename:**
```bash
python3 scraper.py 1 10 --output my_articles
```

**Choose output format:**
```bash
python3 scraper.py 1 3 --format json     # Save as JSON only
python3 scraper.py 1 3 --format csv      # Save as CSV only
python3 scraper.py 1 3 --format both     # Save as both JSON and CSV (default)
```

#### Python Notebook Usage

For use in Jupyter notebooks or Python scripts, import and call the `scrape_articles` function directly:

```python
from scraper import scrape_articles

# Scrape pages 1 to 5
articles = scrape_articles(start_page=1, end_page=5)

# With custom output filename and format
articles = scrape_articles(
    start_page=1,
    end_page=10,
    output='health_articles',
    output_format='csv'
)

# Access the scraped data directly
print(f"Total articles: {len(articles)}")
for article in articles[:3]:  # Show first 3 articles
    print(f"- {article['title']}")
```

**Manual parameter setting in notebook:**
```python
# Set your desired page range here
START_PAGE = 1
END_PAGE = 5
OUTPUT_FILE = 'my_scraped_articles'
OUTPUT_FORMAT = 'both'  # 'json', 'csv', or 'both'

# Run the scraper
articles = scrape_articles(START_PAGE, END_PAGE, OUTPUT_FILE, OUTPUT_FORMAT)
```

### Output Format

The scraper extracts the following information for each article:
- **title**: Article headline
- **url**: Full URL to the article
- **date**: Publication date (e.g., "Rabu, 17 September 2025")
- **time**: Publication time (e.g., "21:00")
- **image_url**: URL to the article's cover image

### Example Output

**JSON format:**
```json
[
  {
    "title": "3 Sunnah Rasul Ini Bisa Mencegah Cacingan pada Anak",
    "url": "https://www.nu.or.id/kesehatan/3-sunnah-rasul-ini-bisa-mencegah-cacingan-pada-anak-r2Xny",
    "date": "Rabu, 17 September 2025",
    "time": "21:00",
    "image_url": "https://storage.nu.or.id/storage/post/4_3/thumb/sunnah-rasul-nu-online_1758114339.webp"
  }
]
```

**CSV format:**
```csv
title,url,date,time,image_url
"3 Sunnah Rasul Ini Bisa Mencegah Cacingan pada Anak","https://www.nu.or.id/kesehatan/3-sunnah-rasul-ini-bisa-mencegah-cacingan-pada-anak-r2Xny","Rabu, 17 September 2025","21:00","https://storage.nu.or.id/storage/post/4_3/thumb/sunnah-rasul-nu-online_1758114339.webp"
```

## PDF Compressor Features

- **Multiple compression methods**: Uses both pypdf and Ghostscript for optimal compression
- **Quality preservation**: Designed to maintain text readability while compressing images
- **Three quality levels**: high, medium, low compression options
- **Automatic method selection**: Tries the best method for your PDF automatically

## Requirements

- Python 3.6+
- pypdf library (automatically installed)
- Ghostscript (optional, but recommended for best results)

### Installing Ghostscript

**macOS:**
```bash
brew install ghostscript
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ghostscript
```

**Windows:**
Download from: https://www.ghostscript.com/download/gsdnld.html

## Installation

1. Clone or download the script
2. **Recommended:** Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

**Note:** If using a virtual environment, activate it first or use the convenience script:
```bash
source venv/bin/activate
# OR
./activate_and_run.sh
```

### Basic usage (automatic method selection):
```bash
python3 pdf_compressor.py input.pdf output.pdf
# OR using convenience script
./activate_and_run.sh python3 pdf_compressor.py input.pdf output.pdf
```

### Specify quality level:
```bash
python3 pdf_compressor.py input.pdf output.pdf --quality high
python3 pdf_compressor.py input.pdf output.pdf --quality medium  # default
python3 pdf_compressor.py input.pdf output.pdf --quality low
```

### Force specific compression method:
```bash
python3 pdf_compressor.py input.pdf output.pdf --method ghostscript
python3 pdf_compressor.py input.pdf output.pdf --method pypdf
```

## Quality Levels

- **high**: Minimal compression, maximum quality preservation (smaller size reduction)
- **medium**: Balanced compression (recommended for most cases)
- **low**: Aggressive compression (larger size reduction, some quality loss possible)

## Compression Methods

1. **Ghostscript** (recommended for image-heavy PDFs):
   - Downsamples images to appropriate resolutions
   - Uses JPEG compression for color/gray images
   - Preserves text and vector graphics
   - Best compression ratios for scanned documents

2. **pypdf** (fallback method):
   - Compresses PDF structure and removes redundant objects
   - Good for PDFs with embedded fonts and text
   - Faster processing

## Example Output

```
Original file size: 259.00 MB

Trying ghostscript compression...
Compressing Theories of Human Communication.pdf using Ghostscript...

Compression Results:
Compressed file size: 45.20 MB
Size reduction: 82.5%
```

## Troubleshooting

- **"Ghostscript not found"**: Install Ghostscript using the commands above
- **No size reduction**: The PDF might already be optimized, or try a lower quality setting
- **Poor text quality**: Use `--quality high` or switch to pypdf method

## For Your Specific File

For your 259MB PDF with 331 pages of photos, try:
```bash
python3 pdf_compressor.py "/Users/alharkan/Documents/Drive/Study/Perspektif Teori Komunikasi/Topik 9/Littlejohn/v3 Theories of Human Communication.pdf" compressed_output.pdf --quality medium
```

This should achieve significant compression (60-85% size reduction) while preserving text readability.
