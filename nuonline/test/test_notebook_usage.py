#!/usr/bin/env python3
"""
Test script to demonstrate notebook usage of the scraper
"""

from scraper import scrape_articles

# Example 1: Basic usage
print("=== Example 1: Basic programmatic usage ===")
articles = scrape_articles(start_page=1, end_page=1, output='notebook_test_basic')

print(f"Scraped {len(articles)} articles")
print(f"First article title: {articles[0]['title'] if articles else 'None'}")

print("\n=== Example 2: Custom parameters ===")
# Example 2: With custom parameters
articles2 = scrape_articles(
    start_page=1,
    end_page=1,
    output='notebook_test_custom',
    output_format='json'
)

print(f"Scraped {len(articles2)} articles to JSON only")

print("\n=== Example 3: Manual variable setting (like in notebook) ===")
# Example 3: Manual variable setting (like what user would do in notebook)
START_PAGE = 1
END_PAGE = 1
OUTPUT_FILE = 'notebook_manual_vars'
OUTPUT_FORMAT = 'csv'

articles3 = scrape_articles(START_PAGE, END_PAGE, OUTPUT_FILE, OUTPUT_FORMAT)
print(f"Scraped {len(articles3)} articles using manual variables")

print("\n=== All tests completed successfully! ===")
