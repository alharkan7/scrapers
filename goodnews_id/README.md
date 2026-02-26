# Good News from Indonesia Scraper

Web scrapers for extracting article URLs and detailed content from Good News from Indonesia (goodnewsfromindonesia.id).

## Features

### URL Scraper (`scraper_url.py`)
- Scrape article URLs from multiple topics
- Date range filtering (inclusive)
- Incremental pagination until no more content or specified end page
- Export to CSV
- Skip already-scraped URLs
- Write to CSV after each page for immediate results
- Configurable via command-line arguments or config file

### Detailed Scraper (`scraper_detailed.py`)
- Scrape full article content from URLs in a CSV file
- Extract: date/time, full title, reading length, content, cover image, caption, and tags
- Skip already-scraped articles by comparing input and output files
- Write to JSON Lines format immediately after each article
- Resumable - can be stopped and restarted without losing progress

## Installation

Required dependencies:
```bash
pip install requests beautifulsoup4 lxml
```

## URL Scraper

### Configuration

Edit `scraper_url_config.py` to set default values:

```python
TOPIC = ["ekonomi", "humaniora", "internasional", "iptek", "legenda", "nasional", "olahraga", "opini", "sejarah", "sosial-budaya", "wisata"]
DATE_START = "2026-01-01"  # YYYY-MM-DD format (earliest date to include)
DATE_END = "2026-12-31"    # YYYY-MM-DD format (latest date to include)
PAGE_START = 1
PAGE_END = 0               # 0 = scrape until no more content
```

### Pagination Logic

The URL scraper uses date-aware pagination:
- Pages are sorted from newest to oldest (page 1 has latest articles)
- DATE_END is the latest date we want to include
- DATE_START is the earliest date we want to include
- Skips pages where all articles are newer than DATE_END
- Starts scraping when we find articles on or before DATE_END
- Stops when all articles on a page are older than DATE_START

### Usage

#### Basic Usage (using config file)

```bash
python scraper_url.py
```

#### Override with Command-Line Arguments

```bash
# Scrape specific topics
python scraper_url.py --topics wisata ekonomi

# Set custom date range
python scraper_url.py --date-start 2026-01-01 --date-end 2026-02-07

# Set page range (0 = infinite)
python scraper_url.py --page-start 1 --page-end 5

# Custom output filename
python scraper_url.py --output my_urls

# Combine options
python scraper_url.py --topics wisata --date-start 2026-01-01 --date-end 2026-02-07 --output wisata_urls
```

#### Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--topics` | `-t` | List of topics to scrape | From config |
| `--date-start` | `-ds` | Start date (YYYY-MM-DD) - earliest date to include | From config |
| `--date-end` | `-de` | End date (YYYY-MM-DD) - latest date to include | From config |
| `--page-start` | `-ps` | Starting page number | From config |
| `--page-end` | `-pe` | Ending page number (0 = infinite) | From config |
| `--output` | `-o` | Output CSV filename (without extension) | `goodnews_id_urls` |

#### Output

The scraper creates/updates `data/goodnews_id_urls.csv` with the following fields:
- `url`: Full article URL
- `topic`: Topic/category
- `title`: Article title
- `author`: Author name
- `date`: Date in YYYY-MM-DD format
- `date_raw`: Original date string (e.g., "2 Feb 2026")
- `image_url`: URL of the article thumbnail image

## Detailed Scraper

### Output Format

The detailed scraper uses **JSON Lines** format (`.jsonl` extension). Each line in the file is a complete JSON object representing one article. This format is chosen because:

- Handles multi-line content naturally (no CSV escaping issues)
- Preserves text structure and formatting
- Easy to parse and validate
- Supports incremental writing (one line per article)
- More human-readable than complex CSV escaping

### JSON Lines Format Example

```json
{"url": "https://www.goodnewsfromindonesia.id/2025/12/08/5-provinsi-yang-tidak-punya-kota-semuanya-di-indonesia-timur", "topic": "Nasional", "author": "Firda Aulia Rachmasari", "date_time": "8 Desember 2025 08.00 WIB • 2 menit", "full_title": "5 Provinsi yang Tidak Punya Kota: Semuanya di Indonesia Timur", "reading_length": "2 menit", "cover_image_url": "https://ik.imagekit.io/goodid/gnfi/uploads/articles/large-5-provinsi-yang-tidak-punya-kota-semuanya-di-indonesia-timur-1nVQvI5K0j.jpg?tr=w-730,h-486,fo-center", "cover_image_caption": "5 Provinsi yang Tidak Punya Kota: Semuanya di Indonesia Timur", "full_article_content": "Tahukah Kawan GNFI jika tidak semua provinsi di Indonesia memiliki kota?...\n\nPada tahun 2025, terdapat 93 kota otonom dan lima kota administrasi di Indonesia...", "tags": ["Kabar Baik Indonesia", "Good News From Indonesia", "Provinsi di Indonesia"]}
```

### Usage

```bash
# Use default input (data/goodnews_id_urls.csv) and output (goodnews_id_details.jsonl)
python scraper_detailed.py

# Specify custom input and output files
python scraper_detailed.py --input data/my_urls.csv --output my_details.jsonl

# Specify just output filename (output goes to data/ directory)
python scraper_detailed.py --output wisata_details.jsonl
```

#### Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input` | `-i` | Input CSV file with URLs | `data/goodnews_id_urls.csv` |
| `--output` | `-o` | Output JSON Lines file (without extension) | `goodnews_id_details.jsonl` |

#### Output Fields

The detailed scraper creates/updates `data/goodnews_id_details.jsonl` with the following fields for each article:
- `url`: Full article URL
- `topic`: Topic/category
- `author`: Author name
- `date_time`: Full date time string (e.g., "8 Desember 2025 08.00 WIB • 2 menit")
- `full_title`: Complete article title
- `reading_length`: Reading time (e.g., "2 menit", "1 jam 30 menit")
- `cover_image_url`: URL of the main article image
- `cover_image_caption`: Caption text for the cover image
- `full_article_content`: Complete article text content
- `tags`: Array of article tags (e.g., ["Kabar Baik Indonesia", "Provinsi di Indonesia"])

#### Reading JSON Lines Files

You can read JSON Lines files in various ways:

**Python:**
```python
import json

with open('data/goodnews_id_details.jsonl', 'r', encoding='utf-8') as f:
    articles = [json.loads(line) for line in f]

for article in articles:
    print(article['full_title'])
```

**Command line (jq):**
```bash
# Count articles
wc -l data/goodnews_id_details.jsonl

# Get specific field
jq '.full_title' data/goodnews_id_details.jsonl

# Filter by topic
jq 'select(.topic == "Wisata")' data/goodnews_id_details.jsonl
```

**Pandas:**
```python
import pandas as pd

df = pd.read_json('data/goodnews_id_details.jsonl', lines=True)
print(df.head())
```

## Available Topics

- ekonomi
- humaniora
- internasional
- iptek
- legenda
- nasional
- olahraga
- opini
- sejarah
- sosial-budaya
- wisata

## Complete Workflow

### Step 1: Scrape URLs
```bash
# Scrape tourism articles from January 2026
python scraper_url.py --topics wisata --date-start 2026-01-01 --date-end 2026-01-31 --output wisata_urls
```

This creates `data/wisata_urls.csv` with all article URLs.

### Step 2: Scrape Detailed Content
```bash
# Scrape full content from URLs
python scraper_detailed.py --input data/wisata_urls.csv --output wisata_details.jsonl
```

This creates `data/wisata_details.jsonl` with complete article details.

## Resumable Scraping

Both scrapers are resumable:

- **URL Scraper**: Checks existing output file and skips already-scraped URLs. Can be stopped and restarted.

- **Detailed Scraper**: Compares input and output files at startup. Skips articles that are already in the output JSON Lines file. Writes results immediately after each article as a new line.

## Examples

### Example 1: Scrape multiple topics for 2026
```bash
python scraper_url.py --topics ekonomi humaniora --date-start 2026-01-01 --date-end 2026-12-31
```

### Example 2: Scrape specific date range with custom output
```bash
python scraper_url.py --topics wisata --date-start 2026-01-01 --date-end 2026-02-28 --output wisata_jan_feb_2026
python scraper_detailed.py --input data/wisata_jan_feb_2026.csv --output wisata_jan_feb_2026_details.jsonl
```

### Example 3: Scrape first 5 pages of a topic
```bash
python scraper_url.py --topics nasional --page-start 1 --page-end 5
```

### Example 4: Resume interrupted scraping
If the scraper was interrupted, simply run the same command again:

```bash
# Will skip already-scraped URLs and continue where it left off
python scraper_url.py --topics wisata
```

```bash
# Will skip already-scraped articles and continue with the rest
python scraper_detailed.py --input data/wisata_urls.csv
```

### Example 5: Convert JSON Lines to JSON array
If you prefer a single JSON array instead of JSON Lines:

```bash
# Using jq
jq -s . data/goodnews_id_details.jsonl > data/goodnews_id_details.json

# Or in Python
import json

with open('data/goodnews_id_details.jsonl', 'r', encoding='utf-8') as f:
    articles = [json.loads(line) for line in f]

with open('data/goodnews_id_details.json', 'w', encoding='utf-8') as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)
```
