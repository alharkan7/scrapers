# BRIN Research Group Scraper

Scrapes research group information from the BRIN (Badan Riset dan Inovasi Nasional) website.

## Features

- **Incremental Scraping**: Resumes from where you left off by reading existing output file
- **Immediate Writes**: Writes each scraped item to file immediately (no data loss if script stops)
- **Configurable Range**: Specify start and end page IDs via command-line arguments
- **Progress Tracking**: Shows real-time progress with statistics
- **Error Handling**: Skips blank or invalid pages automatically
- **Rate Limiting**: Built-in delay to be respectful to the server

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Scrape all pages (1-1633):
```bash
python scraper.py
```

### Test with a Small Range

Test with pages 1-10:
```bash
python scraper.py --start 1 --end 10
```

### Resume Scraping

If you stopped the script at page 500, you can resume:
```bash
python scraper.py --start 501 --end 1633
```

### Custom Output File

Save to a different file (relative to script directory):
```bash
python scraper.py --start 1 --end 100 --output test_scrape.csv
```

Or specify an absolute path:
```bash
python scraper.py --start 1 --end 100 --output /path/to/output.csv
```

### Adjust Delay

Increase delay between requests (default is 0.5 seconds):
```bash
python scraper.py --delay 1.0
```

### Help

Show all available options:
```bash
python scraper.py --help
```

## Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--start` | int | 1 | Starting page ID |
| `--end` | int | 1633 | Ending page ID |
| `--output` | string | brin_research_groups.csv | Output CSV filename (saved in script directory) |
| `--delay` | float | 0.5 | Delay between requests in seconds |

## Output Format

The script generates a CSV file with the following columns:

- `page_id` - The page ID number
- `url` - Full URL to the page
- `kelompok_riset` - Research group name (from title)
- `satuan_kerja_organisasi_riset` - Research organization unit
- `satuan_kerja_pusat_riset` - Research center unit
- `rumpun_riset` - Research cluster/field
- `kelompok_riset_nama` - Research group name (from detail section)
- `nomor_sk_penetapan` - Determination decree number
- `topik_riset` - Research topic
- `lingkup_kegiatan_riset` - Research activity scope
- `lokasi_riset` - Research location
- `mitra_kerjasama` - Current collaboration partners
- `nama_koordinator` - Coordinator name
- `email_koordinator` - Coordinator email

## Example Output

```csv
page_id,url,kelompok_riset,satuan_kerja_organisasi_riset,satuan_kerja_pusat_riset,rumpun_riset,kelompok_riset_nama,nomor_sk_penetapan,topik_riset,lingkup_kegiatan_riset,lokasi_riset,mitra_kerjasama,nama_koordinator,email_koordinator
1633,https://manajementalenta.brin.go.id/kelompok-riset/detail/1633,Kelris Biofarmaseutika,Organisasi Riset Kesehatan,Pusat Riset Vaksin dan Obat,Ilmu Kesehatan,,Peranan mikrobioma untuk kesehatan,Health Biotechnology, Molecular Biology, Health Microbiome, Cell Biology,,,Indira Putri Negari, Ph.D.,indiraputri24@gmail.com
```

## How It Works

1. **Load Existing Data**: The script reads the existing output file (if it exists) to get already scraped page IDs
2. **Skip Scraped Pages**: When iterating through the page range, it skips IDs that are already in the output file
3. **Scrape Page**: For each unscraped page ID, it fetches the HTML and extracts the data
4. **Write Immediately**: Each successfully scraped item is written to the CSV file immediately
5. **Handle Errors**: Blank pages (no content) and errors are logged but don't stop the script

## Tips

- **First Run**: Start with a small range (e.g., `--start 1 --end 10`) to test
- **Resume**: If the script stops, you can run it again with the same parameters and it will skip already scraped pages
- **Check Progress**: The script prints progress every 50 pages
- **Network Issues**: If you encounter network errors, increase the delay with `--delay 1.0`

## Troubleshooting

### Script stops unexpectedly
Just run it again with the same parameters. It will resume from where it left off.

### Blank pages in output
Some page IDs don't have data. These are expected and logged as "Blank pages".

### Connection timeout
Increase the delay: `python scraper.py --delay 2.0`

### CSV file has broken lines/malformed data
If your scraping was interrupted or the CSV file appears broken (lines split incorrectly), use the repair script:

```bash
python repair_csv.py
```

This will create a new file `brin_research_groups_repaired.csv` with:
- Merged split lines
- Properly quoted fields
- Newlines and extra spaces cleaned up
- Correct CSV formatting

## Data Quality Notes

The website's data structure varies significantly:
- Some fields may be empty
- Some pages have incomplete information
- Fields with long text (like `lingkup_kegiatan_riset`) may contain special characters
- Email addresses may be separated by semicolons or listed on multiple lines

The script automatically cleans the data by:
- Removing extra whitespace and newlines
- Properly quoting fields with special characters
- Writing each record immediately to prevent data loss

## License

This script is for educational and research purposes.
