#!/usr/bin/env python3
"""
Test script demonstrating how to use the standalone scrape_full_articles function
independently, similar to how scrape_articles works in scraper.py
"""

import json
from full_article_scraper import scrape_full_articles

# Example usage 1: Auto-generate timestamped filename
print("Example 1: Auto-generating timestamped filename")
result1 = scrape_full_articles("articles_2025-10-22_11-38-41.json")
print(f"Scraped {len(result1) if result1 else 0} articles\n")

# Example usage 2: Specify custom output filename
print("Example 2: Specifying custom output filename")
result2 = scrape_full_articles("articles_2025-10-22_11-38-41.json", "my_custom_full_articles.json")
print(f"Scraped {len(result2) if result2 else 0} articles\n")

# Example usage 3: Process the returned data directly
print("Example 3: Processing returned data directly")
articles = scrape_full_articles("articles_2025-10-22_11-38-41.json", "processed_articles.json")

if articles:
    print(f"Successfully scraped {len(articles)} articles")
    print("\nFirst article details:")
    first_article = articles[0]
    print(f"Title: {first_article.get('title', 'N/A')}")
    print(f"Author: {first_article.get('author', 'N/A')}")
    print(f"Author Role: {first_article.get('author_role', 'N/A')}")
    print(f"Date: {first_article.get('date', 'N/A')}")
    print(f"Time: {first_article.get('time', 'N/A')}")
    print(f"Image Caption: {first_article.get('image_caption', 'N/A')}")
    print(f"Full text length: {len(first_article.get('full_text', ''))} characters")
else:
    print("Failed to scrape articles")
