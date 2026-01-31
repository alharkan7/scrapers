#!/usr/bin/env python3
"""
Script to analyze and suggest expanded search parameters for more job data.

Run this to see how to get more jobs for your research.
"""

import csv
from pathlib import Path

# Read current data
csv_path = Path("job_vacancies/data/jobstreet_vacancies.csv")
if csv_path.exists():
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    current_locations = set()
    current_categories = set()

    for row in rows:
        if row.get('city'):
            current_locations.add(row['city'])
        if row.get('job_category'):
            current_categories.add(row['job_category'])

    print("="*70)
    print("CURRENT DATA ANALYSIS")
    print("="*70)
    print(f"\nTotal jobs: {len(rows)}")
    print(f"\nLocations covered: {len(current_locations)}")
    for loc in sorted(current_locations):
        count = sum(1 for r in rows if r.get('city') == loc)
        print(f"  - {loc}: {count:,} jobs")

    print(f"\nJob categories: {len(current_categories)}")
    print("(Most are empty because searching with '' keyword)")

print("\n" + "="*70)
print("EXPAND YOUR SEARCH TO GET MORE JOBS")
print("="*70)

print("""
You're currently scraping:
  - 1 location: Jakarta
  - 1 keyword: "" (all jobs)
  - Date range: 373 days

To get THOUSANDS more jobs for your research, use these options:

OPTION 1: Add More Indonesian Cities
─────────────────────────────────────────
Edit SEARCH_LOCATIONS in jobstreet_scraper_playwright.py:

SEARCH_LOCATIONS = [
    "Jakarta",
    "Surabaya",      # 2nd largest city
    "Bandung",        # Major tech hub
    "Medan",          # 3rd largest city
    "Semarang",        # Central Java
    "Makassar",        # Eastern Indonesia
    "Yogyakarta",      # Education hub
    "Tangerang",       # Jakarta area
    "Bekasi",          # Jakarta area
    "Bali",           # Tourism/jobs hub
]

Expected: ~30,000-50,000 jobs (10-15x more data)


OPTION 2: Add Job Category Keywords
─────────────────────────────────────────
Edit SEARCH_KEYWORDS in jobstreet_scraper_playwright.py:

SEARCH_KEYWORDS = [
    "",                # All jobs (you already have this)
    "admin",           # Administrative jobs
    "marketing",        # Marketing jobs
    "it",              # IT jobs
    "software",         # Software engineering
    "engineer",        # Engineering jobs
    "finance",         # Finance/accounting
    "sales",           # Sales jobs
    "hr",              # Human resources
    "fresh-graduate",   # Entry level
    "manager",         # Management
]

Set: MAX_KEYWORDS_TO_USE = 10 (or 20 if you add more keywords)

Expected: ~50,000-100,000 jobs (15-30x more data)


OPTION 3: Combine Both (RECOMMENDED)
─────────────────────────────────────────
Edit both SEARCH_LOCATIONS and SEARCH_KEYWORDS:

SEARCH_LOCATIONS = [
    "Jakarta", "Surabaya", "Bandung", "Medan",
    "Semarang", "Makassar", "Yogyakarta",
    "Tangerang", "Bekasi", "Bali"
]

SEARCH_KEYWORDS = [
    "", "admin", "marketing", "it", "software",
    "engineer", "finance", "sales", "hr",
    "fresh-graduate", "manager"
]

MAX_KEYWORDS_TO_USE = 10
DATE_RANGE = 373  # Keep this for comprehensive coverage

Expected: ~200,000-500,000 jobs (100-150x more data!)


OPTION 4: Increase Page Limits
─────────────────────────────────────────
If you want to go deeper in existing searches:

MAX_JOBS_PER_SEARCH = 50000  # Was 10000
MAX_PAGES_PER_SEARCH = 500       # Was 100

Expected: ~5,000-10,000 more jobs from Jakarta


QUICK START COMMANDS
─────────────────────────────────────────

# Option 1: Add cities only (fast, 30-50K jobs)
python3 job_vacancies/scrapers_v1/jobstreet_scraper_playwright.py \\
    --locations Jakarta Surabaya Bandung Medan Semarang \\
    --max-jobs 50000

# Option 2: Add keywords only (medium speed, 50-100K jobs)
python3 job_vacancies/scrapers_v1/jobstreet_scraper_playwright.py \\
    --keywords admin marketing it software engineer finance sales \\
    --max-keywords 6 \\
    --max-jobs 100000

# Option 3: Everything (slow, 200-500K jobs)
python3 job_vacancies/scrapers_v1/jobstreet_scraper_playwright.py \\
    --locations Jakarta Surabaya Bandung Medan Semarang Makassar Yogyakarta Tangerang Bekasi Bali \\
    --keywords "" admin marketing it software engineer finance sales hr fresh-graduate manager \\
    --max-keywords 10 \\
    --max-jobs 500000 \\
    --headless


CURRENT STATUS
─────────────────────────────────────────
With your current settings:
  - Location: 1 city (Jakarta)
  - Keywords: 1 (all jobs)
  - Date range: 373 days
  - Max jobs: 10,000

You already have 3,395 jobs from Jakarta.
The script found only 1 new job on the first page because
you've already scraped most jobs from that search combination.

TO GET MORE DATA: Expand locations and/or keywords!
""")

print("="*70)
