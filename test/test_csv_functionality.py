#!/usr/bin/env python3
"""
Test script demonstrating CSV output functionality for full article scraper
"""

from full_article_scraper import scrape_full_articles

# Example usage with CSV output
print("Example: CSV output")
result_csv = scrape_full_articles("test_small_articles.json", "csv_output", output_format='csv')
print(f"Scraped {len(result_csv) if result_csv else 0} articles to CSV\n")

# Example usage with both JSON and CSV output
print("Example: Both JSON and CSV output")
result_both = scrape_full_articles("test_small_articles.json", "both_output", output_format='both')
print(f"Scraped {len(result_both) if result_both else 0} articles to both formats\n")

# Example usage with JSON output (default)
print("Example: JSON output (default)")
result_json = scrape_full_articles("test_small_articles.json", "json_output", output_format='json')
print(f"Scraped {len(result_json) if result_json else 0} articles to JSON\n")

print("All formats tested successfully!")
