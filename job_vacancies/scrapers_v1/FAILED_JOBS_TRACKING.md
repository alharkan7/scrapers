# Failed Jobs Tracking - Feature Added

## What's New

The detail scraper now tracks jobs that failed or expired in a separate CSV file.

## How It Works

### 1. Separate File for Failed Jobs
- **Output file**: `job_vacancies/data/jobstreet_details.csv`
- **Failed jobs log**: `job_vacancies/data/jobstreet_details_failed.csv`

### 2. Automatic Filtering on Re-run

When you run the scraper again, it:

**Loads from `jobstreet_details_failed.csv`:**
```python
job_id,job_url,failure_reason,failed_at
89805630,https://...,Expired/Removed: Job not longer advertised,2026-01-31T20:38:38
89524614,https://...,Expired/Removed: Job not longer advertised,2026-01-31T20:38:45
```

**Skips these jobs automatically:**
```python
jobs_to_scrape = [
    job for job in all_jobs
    if job["job_id"] not in self.scraped_job_ids  # Already scraped
    and job["job_id"] not in self.failed_job_ids  # Previously failed
]
```

### 3. Error Classification

Failed jobs are classified by type:

- **Expired** (404, not found, removed, deleted)
  → Logged to failed file
  → Skipped on future runs

- **Timeout** (page load timeout)
  → Retried up to 3 times
  → If still fails, logged to failed file

- **Network** (connection issues)
  → Retried up to 3 times
  → If still fails, logged to failed file

- **Validation** (missing required fields)
  → NOT retried (parsing won't fix this)
  → Logged to failed file

- **Unknown** (other errors)
  → Retried up to 3 times
  → If still fails, logged to failed file

## Usage Examples

### Default Behavior
```bash
# Uses default files
python3 job_vacancies/scrapers_v1/jobstreet_detail_scraper.py --headless

# Creates:
#   job_vacancies/data/jobstreet_details.csv (successful jobs)
#   job_vacancies/data/jobstreet_details_failed.csv (failed jobs)
```

### Custom Failed Jobs Log
```bash
# Specify custom failed jobs file
python3 job_vacancies/scrapers_v1/jobstreet_detail_scraper.py \
    --failed-log job_vacancies/data/my_failed_jobs.csv \
    --headless
```

## Expected Log Output

```
2026-01-31 20:38:00 - INFO - Detail scraper initialized.
2026-01-31 20:38:00 - INFO - Input: job_vacancies/data/jobstreet_vacancies.csv
2026-01-31 20:38:00 - INFO - Output: job_vacancies/data/jobstreet_details.csv
2026-01-31 20:38:00 - INFO - Failed job log: job_vacancies/data/jobstreet_details_failed.csv
2026-01-31 20:38:00 - INFO - Loaded 0 existing job IDs from jobstreet_details.csv
2026-01-31 20:38:00 - INFO - Loaded 0 previously failed job IDs
2026-01-31 20:38:00 - INFO - Total jobs in input: 20579
2026-01-31 20:38:00 - INFO - Already scraped: 0
2026-01-31 20:38:00 - INFO - Previously failed: 0
2026-01-31 20:38:00 - INFO - Remaining to scrape: 20579

Fetching job details: 0%|                    | 0/20579 [00:00<?, ?it/s]
2026-01-31 20:38:38 - WARNING -   ✗ Missing or invalid job_title
2026-01-31 20:38:38 - WARNING - ⚠ Validation failed for 89805630
2026-01-31 20:38:38 - INFO -   Job 89805630 expired/removed - logging to failed file
2026-01-31 20:38:38 - WARNING - ✗ Failed to scrape job 89805630

2026-01-31 20:45:32 - INFO - Completed in 414.2 seconds
2026-01-31 20:45:32 - INFO - Total job details collected: 16226
2026-01-31 20:45:32 - INFO - Total unique jobs saved: 16226
2026-01-31 20:45:32 - INFO - Success rate: 78.9% (16226/20579)
2026-01-31 20:45:32 - INFO - Expired/removed jobs: 2
2026-01-31 20:45:32 - INFO - Validation failures: 2
2026-01-31 20:45:32 - INFO - Pages loaded: 20579
2026-01-31 20:45:32 - INFO - Failed extractions: 4351
2026-01-31 20:45:32 - INFO - Retry attempts: 312
2026-01-31 20:45:32 - INFO - CSV writes: 16226
2026-01-31 20:45:32 - INFO - Average time per job: 3.7s
2026-01-31 20:45:32 - INFO - Output file: job_vacancies/data/jobstreet_details.csv
2026-01-31 20:45:32 - INFO - Failed jobs log: job_vacancies/data/jobstreet_details_failed.csv
2026-01-31 20:45:32 - INFO -   Note: Expired jobs logged to job_vacancies/data/jobstreet_details_failed.csv and will be skipped in future runs
```

## Benefits

### 1. No Wasted Time
- Expired/removed jobs are tracked separately
- Future runs skip them immediately
- No need to re-attract extraction

### 2. Clear Statistics
- See exactly how many jobs expired
- Distinguish expired vs. validation failures
- Know what to investigate

### 3. Resume Capability
- Can analyze failed jobs later
- Determine if it's worth re-trying
- Clean up false negatives

### 4. Research Insights
Failed jobs file helps identify:

- High expiration rate → Jobs are quickly removed
- Validation failures → Website structure changed
- Network issues → Need to adjust delays
- 404 patterns → Which job types expire faster

## Manual Review

After scraping completes:

```bash
# Check failed jobs
cat job_vacancies/data/jobstreet_details_failed.csv

# Analyze patterns
# - Are certain job types failing?
# - Is expiration rate too high?
# - Should you increase timeouts?
# - Do some URLs consistently fail?
```

## Integration with Main Scraper

When combining both scrapers:

1. **Main scraper** (jobstreet_scraper_playwright.py)
   - Scrapes job listings
   - Outputs: `job_vacancies/data/jobstreet_vacancies.csv`

2. **Detail scraper** (jobstreet_detail_scraper.py)
   - Reads from: `job_vacancies/data/jobstreet_vacancies.csv`
   - Outputs: `job_vacancies/data/jobstreet_details.csv`
   - Tracks failures: `job_vacancies/data/jobstreet_details_failed.csv`

This creates a complete dataset with:
- ✅ Successfully extracted job details
- ✅ Tracked failed/expired jobs for analysis
- ✅ No wasted re-scraping attempts
