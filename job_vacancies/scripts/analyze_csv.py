#!/usr/bin/env python3
"""
Quick analysis utility for JobStreet vacancy CSV data.
"""

import csv
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

def analyze_csv(csv_path):
    """Analyze the CSV file and provide recommendations."""

    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        return

    print(f"Analyzing: {csv_path}\n")

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No data found in CSV")
        return

    print(f"Total jobs: {len(rows)}")

    # Analyze scraped_at dates
    scraped_dates = [row['scraped_at'][:10] for row in rows if row['scraped_at']]
    date_counts = Counter(scraped_dates)

    print(f"\n{'='*60}")
    print("SCRAPING SESSIONS")
    print(f"{'='*60}")
    for date, count in sorted(date_counts.items()):
        print(f"  {date}: {count:,} jobs ({count/len(rows)*100:.1f}%)")

    # Calculate scraping frequency
    if len(date_counts) >= 2:
        first_date = min(date_counts.keys())
        last_date = max(date_counts.keys())
        d1 = datetime.strptime(first_date, '%Y-%m-%d')
        d2 = datetime.strptime(last_date, '%Y-%m-%d')
        days_diff = (d2 - d1).days
        print(f"\n  First scrape: {first_date}")
        print(f"  Last scrape: {last_date}")
        print(f"  Time span: {days_diff} days")

        if days_diff > 0:
            avg_jobs_per_day = len(rows) / days_diff
            print(f"  Average: {avg_jobs_per_day:.1f} jobs/day")

    # Analyze posted_date patterns
    print(f"\n{'='*60}")
    print("POSTED DATE PATTERNS (sample)")
    print(f"{'='*60}")
    posted_dates = [row['posted_date'] for row in rows if row['posted_date']]
    unique_posted = list(set(posted_dates))[:20]
    for pd in sorted(unique_posted, reverse=True):
        count = posted_dates.count(pd)
        print(f"  {pd}: {count} jobs")

    # Recommendations
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")

    today = datetime.now()
    last_scrape = datetime.strptime(max(date_counts.keys()), '%Y-%m-%d')
    days_since_last_scrape = (today - last_scrape).days

    print(f"\nDays since last scrape: {days_since_last_scrape}")

    if days_since_last_scrape == 0:
        print("✓ You scraped TODAY!")
        print("  Recommendation: Use DATE_RANGE = 1 for future daily scrapes")
        print(f"  Next scrape: Use DATE_RANGE = {days_since_last_scrape + 1} to get any new jobs")
    elif days_since_last_scrape <= 7:
        print(f"✓ Last scrape was {days_since_last_scrape} day(s) ago")
        print(f"  Recommendation: Use DATE_RANGE = {days_since_last_scrape + 1}")
    elif days_since_last_scrape <= 30:
        print(f"⚠ Last scrape was {days_since_last_scrape} days ago")
        print(f"  Recommendation: Use DATE_RANGE = {days_since_last_scrape + 1}")
        print("  Consider scraping more frequently (weekly)")
    else:
        print(f"⚠ Last scrape was {days_since_last_scrape} days ago")
        print(f"  Recommendation: Use DATE_RANGE = {days_since_last_scrape + 1}")
        print("  Consider setting up regular weekly or monthly scrapes")

    # Check for duplicates
    job_ids = [row['job_id'] for row in rows if row['job_id']]
    unique_ids = set(job_ids)
    duplicates = len(job_ids) - len(unique_ids)

    print(f"\n{'='*60}")
    print("DATA QUALITY")
    print(f"{'='*60}")
    print(f"  Total job IDs: {len(job_ids):,}")
    print(f"  Unique job IDs: {len(unique_ids):,}")
    if duplicates > 0:
        print(f"  ⚠ Duplicate job IDs: {duplicates}")
        print("  Consider running a deduplication script")
    else:
        print(f"  ✓ No duplicates found")

    # Suggest scraping schedule
    print(f"\n{'='*60}")
    print("SUGGESTED SCRAPING SCHEDULES")
    print(f"{'='*60}")

    if avg_jobs_per_day > 100:
        print("High volume detected!")
        print("\nOption 1 - Daily Scraping:")
        print("  DATE_RANGE = 1")
        print("  Run: Every day")
        print(f"  Expected: ~{int(avg_jobs_per_day)} new jobs/day")

        print("\nOption 2 - Weekly Scraping:")
        print("  DATE_RANGE = 7")
        print("  Run: Every week")
        print(f"  Expected: ~{int(avg_jobs_per_day * 7)} new jobs/week")
    else:
        print("Moderate volume detected")

        print("\nOption 1 - Daily Scraping:")
        print("  DATE_RANGE = 1")
        print("  Run: Every day")
        print(f"  Expected: ~{int(avg_jobs_per_day)} new jobs/day")

        print("\nOption 2 - Weekly Scraping:")
        print("  DATE_RANGE = 7")
        print("  Run: Every week")
        print(f"  Expected: ~{int(max(1, avg_jobs_per_day * 7))} new jobs/week")

        print("\nOption 3 - Monthly Scraping:")
        print("  DATE_RANGE = 30")
        print("  Run: Every month")
        print(f"  Expected: ~{int(max(1, avg_jobs_per_day * 30))} new jobs/month")

    print(f"\n{'='*60}")

if __name__ == "__main__":
    default_csv = "job_vacancies/data/jobstreet_vacancies.csv"

    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = default_csv

    analyze_csv(csv_path)
