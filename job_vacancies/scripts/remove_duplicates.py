#!/usr/bin/env python3
"""
Remove duplicate rows from jobstreet_vacancies.csv based on job_id
"""

import pandas as pd
from pathlib import Path

# Paths
csv_path = Path(__file__).parent / "data" / "jobstreet_vacancies.csv"
output_path = Path(__file__).parent / "data" / "jobstreet_vacancies_cleaned.csv"

# Load CSV
print(f"Loading CSV from: {csv_path}")
df = pd.read_csv(csv_path)

# Show initial stats
print(f"\nInitial row count: {len(df)}")
print(f"Initial unique job_ids: {df['job_id'].nunique()}")

# Check for duplicates
duplicates = df.duplicated(subset=['job_id'], keep=False)
duplicate_count = duplicates.sum()

print(f"\nDuplicate job_ids found: {duplicate_count}")
if duplicate_count > 0:
    print("\nSample duplicate job_ids:")
    print(df[duplicates][['job_id', 'job_title']].head(10))

# Remove duplicates, keeping the first occurrence
df_cleaned = df.drop_duplicates(subset=['job_id'], keep='first')

# Show final stats
print(f"\nFinal row count: {len(df_cleaned)}")
print(f"Rows removed: {len(df) - len(df_cleaned)}")
print(f"Unique job_ids after cleaning: {df_cleaned['job_id'].nunique()}")

# Save cleaned CSV
df_cleaned.to_csv(output_path, index=False)
print(f"\nCleaned CSV saved to: {output_path}")

# Verify no duplicates remain
if df_cleaned.duplicated(subset=['job_id']).any():
    print("\nWARNING: Duplicates still exist!")
else:
    print("\n✓ All duplicates removed successfully")
