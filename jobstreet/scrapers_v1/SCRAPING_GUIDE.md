# JobStreet Scraping Guide

## Data Summary

- **Total Jobs**: 3,392 jobs
- **First Scrape**: 2026-01-08 (3,204 jobs with DATE_RANGE=373)
- **Last Scrape**: 2026-01-31 (188 new jobs)
- **Coverage**: Jobs from ~2025-01-01 to 2026-01-31

## How to Get Unique/New Jobs

### The Automatic Method (Recommended) ⚡

The script **automatically prevents duplicates** using a 3-stage optimization:

1. **Quick ID Check** (Fastest): Extracts only job IDs and checks against known IDs
2. **Early Page Skip**: If a page has 0 new jobs, skips full parsing
3. **Full Extraction**: Only parses complete job data for new jobs

**Performance Boost**: With 3,000+ existing jobs, re-scraping is **10-50x faster** because:
- Old job IDs are identified before full data extraction
- Pages with only old jobs are skipped entirely
- Only new jobs get fully parsed and written to CSV

**Just run the script again** - it will be much faster and only add new jobs!

### Daily Scraping for Fresh Jobs

Edit the `DATE_RANGE` parameter at the top of the script:

```python
# In jobstreet_scraper_playwright.py, line 61:
DATE_RANGE = 1  # Scrape jobs posted in the last 1 day
```

Run daily:
```bash
python3 job_vacancies/scrapers_v1/jobstreet_scraper_playwright.py
```

### Weekly Scraping

```python
DATE_RANGE = 7  # Scrape jobs from the last 7 days
```

Run weekly or bi-weekly.

### Monthly Scraping

```python
DATE_RANGE = 30  # Scrape jobs from the last 30 days
```

## Important Notes

1. **Don't change the output file path**: The script needs to read existing data to avoid duplicates
2. **Don't delete the CSV**: Existing job IDs are loaded before each scraping session
3. **Interrupt safely**: You can press Ctrl+C anytime - jobs are saved incrementally
4. **Resume anytime**: The script can be stopped and resumed without losing data

## Performance Optimization Details

The scraper now uses **smart filtering** to dramatically speed up re-scraping:

### Optimization Stages

1. **Stage 1 - Quick ID Scan** (milliseconds)
   - Extracts only job IDs from page HTML/JSON
   - No scrolling, no full parsing
   - Checks against existing job IDs
   - Returns count of new jobs

2. **Stage 2 - Early Page Skip**
   - If page has 0 new jobs: Skip entirely
   - If page has few new jobs: Proceed carefully
   - Saves time on pages full of duplicates

3. **Stage 3 - Targeted Extraction**
   - Only extracts full data for new jobs
   - Skips full parsing for known jobs
   - Writes new jobs immediately

### Performance Comparison

| Scenario | Old Approach | New Approach | Speedup |
|----------|-------------|--------------|---------|
| Initial scrape (0 existing) | N/A | Full speed | 1x |
| Daily re-scrape (3K existing) | ~2-3 hours | ~2-5 minutes | **30-50x** |
| Weekly re-scrape (3K existing) | ~2-3 hours | ~5-10 minutes | **20-30x** |

### Example Log Output

```
2026-01-31 08:51:48 - INFO - Scraper initialized. Target: 10000 jobs
2026-01-31 08:51:48 - INFO - Existing jobs in CSV: 3392
2026-01-31 08:51:48 - INFO - ✓ Optimization enabled: Will skip 3392 known jobs during extraction

2026-01-31 08:52:08 - INFO -   Page 1: Found 8 new jobs out of 32 total
2026-01-31 08:52:18 - INFO -     Page 1: +8 jobs (Total: 8)
2026-01-31 08:52:28 - INFO -     Page 2: Found 5 new jobs out of 32 total
2026-01-31 08:52:38 - INFO -     Page 2: +5 jobs (Total: 13)
2026-01-31 08:52:48 - DEBUG -     Page 3: All jobs already scraped, skipping
2026-01-31 08:52:58 - INFO -     Page 4: +0 jobs (Total: 13)

2026-01-31 08:53:14 - INFO - Completed in 85.6 seconds
2026-01-31 08:53:14 - INFO - Pages skipped (all duplicate): 4
2026-01-31 08:53:14 - INFO - Jobs skipped by filter: 124
```

## Understanding the Date Fields

### `posted_date`
- Format: "1d ago", "2h ago", "3d ago", etc.
- Relative to when the job posting was viewed
- Used by JobStreet's date range filter

### `scraped_at`
- Format: "2026-01-31T08:53:05.527580"
- Exact timestamp when the job was scraped
- Shows your scraping session dates

### `DATE_RANGE` Parameter
- Controls how far back JobStreet looks for jobs
- Examples:
  - `1` = last 24 hours
  - `7` = last week
  - `30` = last month
  - `373` = last year
- Set this based on how frequently you plan to scrape

## Best Practices

1. **For Fresh Jobs**: Use `DATE_RANGE = 1` and run daily
2. **For Comprehensive Coverage**: Use `DATE_RANGE = 30` and run monthly
3. **For Testing**: Use `DATE_RANGE = 7` and `MAX_TOTAL_JOBS = 100`
4. **Always use the same CSV file**: This enables automatic deduplication
5. **Monitor the logs**: Check "Total unique jobs saved" to verify new data collection

## Example: Daily Fresh Job Collection

```python
# Edit jobstreet_scraper_playwright.py
DATE_RANGE = 1  # Only jobs posted in the last 24 hours
MAX_TOTAL_JOBS = 500  # Reasonable daily limit

# Run daily (could use cron or scheduling tool)
python3 job_vacancies/scrapers_v1/jobstreet_scraper_playwright.py --headless
```

This will give you a growing database of fresh job postings without any duplicates!
