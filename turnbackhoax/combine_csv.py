#!/usr/bin/env python3
"""
Script to combine turnbackhoax CSV files and remove duplicates.
Combines:
- turnbackhoax_headlines_20260110_100834.csv
- turnbackhoax_manual_scraping.csv

Removes duplicates based on URL column.
Orders by Month Year (descending) and Page Number (descending).
"""

import pandas as pd
from datetime import datetime
import os

def parse_date_range(date_range: str) -> datetime:
    """
    Parse date_range like 'January 2025' or 'May 2025' into a datetime object.
    Returns a datetime for sorting purposes.
    """
    try:
        # Parse format like "January 2025"
        return datetime.strptime(date_range, "%B %Y")
    except (ValueError, TypeError):
        # Return a very old date if parsing fails
        return datetime(1900, 1, 1)


def combine_csv_files():
    # Define file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file1 = os.path.join(script_dir, "turnbackhoax_headlines_20260110_100834.csv")
    file2 = os.path.join(script_dir, "turnbackhoax_manual_scraping.csv")
    output_file = os.path.join(script_dir, "turnbackhoax_combined.csv")

    # Read CSV files
    print(f"Reading {file1}...")
    df1 = pd.read_csv(file1)
    print(f"  - {len(df1)} rows found")

    print(f"Reading {file2}...")
    df2 = pd.read_csv(file2)
    print(f"  - {len(df2)} rows found")

    # Combine dataframes
    print("\nCombining files...")
    combined = pd.concat([df1, df2], ignore_index=True)
    print(f"  - Total rows before removing duplicates: {len(combined)}")

    # Remove duplicates based on URL column (keep first occurrence)
    combined_unique = combined.drop_duplicates(subset=['url'], keep='first')
    duplicates_removed = len(combined) - len(combined_unique)
    print(f"  - Duplicates removed: {duplicates_removed}")
    print(f"  - Total rows after removing duplicates: {len(combined_unique)}")

    # Create a sorting key for date_range
    combined_unique = combined_unique.copy()
    combined_unique['_sort_date'] = combined_unique['date_range'].apply(parse_date_range)
    
    # Convert page_number to numeric for proper sorting
    combined_unique['_sort_page'] = pd.to_numeric(combined_unique['page_number'], errors='coerce').fillna(0)

    # Sort by date_range (descending) and page_number (descending)
    print("\nSorting by Month Year (desc) and Page Number (desc)...")
    combined_sorted = combined_unique.sort_values(
        by=['_sort_date', '_sort_page'],
        ascending=[False, False]
    )

    # Drop the temporary sorting columns
    combined_sorted = combined_sorted.drop(columns=['_sort_date', '_sort_page'])

    # Save to output file
    print(f"\nSaving to {output_file}...")
    combined_sorted.to_csv(output_file, index=False)
    print(f"  - {len(combined_sorted)} rows saved")

    # Print summary of date_range distribution
    print("\nDate range distribution:")
    date_counts = combined_sorted['date_range'].value_counts().sort_index()
    for date_range, count in date_counts.items():
        print(f"  - {date_range}: {count} articles")

    print("\n✅ Done! Combined CSV saved to:", output_file)


if __name__ == "__main__":
    combine_csv_files()
