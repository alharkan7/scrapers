#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze Date Outliers in scraped TurnBackHoax data
"""

import pandas as pd
from datetime import datetime
import re

# Read the CSV file
df = pd.read_csv('../data/turnbackhoax_articles_by_id.csv', encoding='utf-8')

print("=" * 80)
print("DATE OUTLIER ANALYSIS")
print("=" * 80)
print(f"\nTotal records: {len(df)}")
print(f"Records with dates: {df['date'].notna().sum()}")
print()

# Function to parse date strings
def parse_date(date_str):
    """Try to parse date string to datetime object"""
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None
    
    # Common formats in Indonesian dates
    formats = [
        '%d/%m/%Y',  # 03/01/2025
        '%d-%m-%Y',  # 03-01-2025
        '%Y-%m-%d',  # 2025-01-03
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    
    return None

# Parse all dates
df['parsed_date'] = df['date'].apply(parse_date)
df['year'] = df['parsed_date'].apply(lambda x: x.year if x else None)

# Show year distribution
print("YEAR DISTRIBUTION:")
print("-" * 80)
year_counts = df['year'].value_counts().sort_index()
print(year_counts)
print()

# Define outliers (not 2025, which should be the focus)
outliers = df[df['year'].notna() & (df['year'] != 2025)].copy()

print(f"\nOUTLIER RECORDS (not year 2025): {len(outliers)}")
print("-" * 80)

if len(outliers) > 0:
    # Sort by year
    outliers = outliers.sort_values('year')
    
    # Show detailed outliers
    print("\nDetailed outlier information:")
    for idx, row in outliers.iterrows():
        print(f"\nArticle ID: {row['article_id']}")
        print(f"URL: {row['url']}")
        print(f"Date string: {row['date']}")
        print(f"Parsed year: {row['year']}")
        print(f"Title: {row['full_title'][:80]}...")
    
    # Save outliers to CSV for further investigation
    outliers_file = '../data/date_outliers.csv'
    outliers[['article_id', 'url', 'date', 'year', 'full_title', 'category']].to_csv(
        outliers_file, index=False, encoding='utf-8'
    )
    print(f"\n\nOutlier details saved to: {outliers_file}")
    
    # Show summary by year
    print("\n\nOUTLIER SUMMARY BY YEAR:")
    print("-" * 80)
    outlier_years = outliers['year'].value_counts().sort_index()
    for year, count in outlier_years.items():
        print(f"{year}: {count} articles")
        # Show some example IDs
        example_ids = outliers[outliers['year'] == year]['article_id'].head(5).tolist()
        print(f"  Example IDs: {example_ids}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
