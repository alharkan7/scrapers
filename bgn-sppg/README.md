# BGN SPPG Scraper

Scrapes operational SPPG (Satuan Pelayanan Pemenuhan Gizi) data from https://www.bgn.go.id/operasional-sppg

## Features

- **Pagination support**: Handles thousands of pages automatically
- **Resume capability**: Can resume from where it left off if interrupted
- **Duplicate detection**: Uses "Nama SPPG" as unique ID to avoid duplicates
- **Multiple output formats**: JSON and CSV
- **Progress tracking**: Saves progress checkpoint every N pages
- **Error handling**: Retry logic for failed requests

## Requirements

- Python 3.6+
- Required packages (install from parent directory):
  ```bash
  pip install requests beautifulsoup4 lxml
  ```

## Usage

### Test mode (scrape 3 pages)
```bash
python3 scraper.py --test
```

### Scrape all pages (resumable)
```bash
python3 scraper.py --format both
```

### Scrape specific range
```bash
python3 scraper.py --start 1 --end 100 --format json
```

### Options

- `--start N`: Start page (default: 1)
- `--end N`: End page (default: unlimited)
- `--format {json|csv|both}`: Output format (default: json)
- `--interval N`: Save progress every N pages (default: 10)
- `--test`: Test mode - scrape only 3 pages

## Output

Files are saved to `output/` directory:

- `sppg_data.json`: All scraped data in JSON format
- `sppg_data.csv`: All scraped data in CSV format
- `progress.json`: Last scraped page (for resuming)

## Data Fields

| Field | Description |
|-------|-------------|
| no | Row number |
| provinsi | Province |
| kab_kota | Regency/City |
| kecamatan | District |
| kelurahan_desa | Village |
| alamat | Address |
| nama_sppg | SPPG Name (unique ID) |

## Resume Capability

If scraping is interrupted, simply run the same command again. The scraper will:

1. Load existing data from `sppg_data.json`
2. Check `progress.json` for last scraped page
3. Resume from the next page
4. Skip any duplicates based on "Nama SPPG"

## Example

```bash
# First run - start scraping
python3 scraper.py --format both --interval 50

# If interrupted at page 500, run again to continue
python3 scraper.py --format both --interval 50
# Will resume from page 501
```
