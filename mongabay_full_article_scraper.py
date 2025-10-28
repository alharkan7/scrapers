#!/usr/bin/env python3
"""
Full article scraper for Mongabay.co.id articles.
Scrapes complete article content from URLs in a JSON file.
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import argparse
import time
import re
from datetime import datetime
import os


class MongabayFullArticleScraper:
    def __init__(self, base_url="https://mongabay.co.id"):
        self.base_url = base_url
        self.session = requests.Session()
        # Set more realistic headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })

    def scrape_full_article(self, url):
        """
        Scrape a full article from a Mongabay URL.

        Parameters:
        - url (str): The URL of the article to scrape

        Returns:
        - dict: Dictionary containing all extracted article data
        """
        print(f"Scraping article: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching article {url}: {e}")
            return None

        soup = BeautifulSoup(response.content, 'lxml')
        article_data = {}

        # Extract title
        title_elem = soup.find('h1')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)

        # Extract author
        author_elem = soup.find('span', class_='bylines')
        if author_elem:
            author_link = author_elem.find('a')
            if author_link:
                article_data['author'] = author_link.get_text(strip=True)

        # Extract date
        date_elem = soup.find('span', class_='date')
        if date_elem:
            article_data['date'] = date_elem.get_text(strip=True)

        # Extract location and series from taxonomy spans
        taxonomy_elems = soup.find_all('span', class_='taxonomy')
        if len(taxonomy_elems) >= 1:
            location_link = taxonomy_elems[0].find('a')
            if location_link:
                article_data['location'] = location_link.get_text(strip=True)

        if len(taxonomy_elems) >= 2:
            series_link = taxonomy_elems[1].find('a')
            if series_link:
                article_data['series'] = series_link.get_text(strip=True)

        # Extract cover image URL from div with background style
        cover_image_url = None

        # Look for div with background image in style
        for div in soup.find_all('div', style=re.compile(r'background.*url')):
            style = div.get('style', '')
            url_match = re.search(r'background.*url\(["\']?(.*?)["\']?\)', style)
            if url_match:
                cover_image_url = url_match.group(1)
                break

        # If not found, try looking for other image elements
        if not cover_image_url:
            # Look for featured image or article image
            img_elem = soup.find('img', class_=re.compile(r'featured|article|cover'))
            if img_elem:
                cover_image_url = img_elem.get('src') or img_elem.get('data-src')

        article_data['cover_image_url'] = cover_image_url

        # Extract full text content
        # Look for the main article content - this may vary by article structure
        content_selectors = [
            'div.article-content',
            'div.entry-content',
            'div.post-content',
            'div.content',
            'article',
            'div.article-body'
        ]

        full_text = ""
        content_elem = None

        for selector in content_selectors:
            if '.' in selector:
                class_name = selector.split('.')[-1]
                content_elem = soup.find('div', class_=class_name)
            else:
                content_elem = soup.find(selector)

            if content_elem:
                break

        # If specific selector not found, try to find paragraphs after the article header
        if not content_elem:
            article_headline = soup.find('div', class_='article-headline')
            if article_headline:
                # Find all paragraphs that come after the headline
                content_elem = article_headline.find_next_siblings(['div', 'p', 'article'])
                if content_elem:
                    content_elem = content_elem[0]

        if content_elem:
            # Extract text from paragraphs and other text elements
            paragraphs = content_elem.find_all(['p', 'h2', 'h3', 'h4', 'blockquote'])
            text_parts = []

            for para in paragraphs:
                # Skip elements that are likely not part of the main article text
                if para.find_parent(['aside', 'footer', 'nav', 'header']):
                    continue

                text = para.get_text(strip=True)
                if text and len(text) > 10:  # Filter out very short texts that might be metadata
                    text_parts.append(text)

            full_text = '\n\n'.join(text_parts)

        article_data['full_text'] = full_text
        article_data['url'] = url

        # Add scraping timestamp
        article_data['scraped_at'] = datetime.now().isoformat()

        return article_data

    def scrape_articles_from_json(self, json_file):
        """
        Scrape full articles from URLs listed in a JSON file.

        Parameters:
        - json_file (str): Path to JSON file containing article URLs

        Returns:
        - list: List of scraped full article data
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                articles_data = json.load(f)
        except FileNotFoundError:
            print(f"JSON file not found: {json_file}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")
            return []

        full_articles = []

        for i, article in enumerate(articles_data, 1):
            url = article.get('url')
            if not url:
                print(f"Article {i} has no URL, skipping")
                continue

            print(f"Processing article {i}/{len(articles_data)}")
            full_article_data = self.scrape_full_article(url)

            if full_article_data:
                # Merge with existing data if available
                merged_data = {**article, **full_article_data}
                full_articles.append(merged_data)
            else:
                print(f"Failed to scrape article: {url}")
                # Still add the basic data if scraping failed
                full_articles.append(article)

            # Add delay to be respectful to the server
            time.sleep(2)

        return full_articles

    def save_to_json(self, articles, filename):
        """Save articles to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

    def save_to_csv(self, articles, filename):
        """Save articles to CSV file."""
        if not articles:
            print("No articles to save.")
            return

        # Flatten the data for CSV
        csv_data = []
        for article in articles:
            csv_row = {
                'title': article.get('title', ''),
                'author': article.get('author', ''),
                'date': article.get('date', ''),
                'location': article.get('location', ''),
                'series': article.get('series', ''),
                'cover_image_url': article.get('cover_image_url', ''),
                'url': article.get('url', ''),
                'scraped_at': article.get('scraped_at', ''),
                'full_text': article.get('full_text', '')
            }
            csv_data.append(csv_row)

        fieldnames = ['title', 'author', 'date', 'location', 'series', 'cover_image_url', 'url', 'scraped_at', 'full_text']

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)


def scrape_mongabay_full_articles(json_file, output='mongabay_full_articles', output_format='both'):
    """
    Scrape full Mongabay articles from URLs in a JSON file.

    Parameters:
    - json_file (str): Path to JSON file containing article URLs
    - output (str): Output filename (without extension), default 'mongabay_full_articles'
    - output_format (str): Output format ('json', 'csv', or 'both'), default 'both'

    Returns:
    - list: List of scraped full articles
    """
    if output_format not in ['json', 'csv', 'both']:
        raise ValueError("output_format must be 'json', 'csv', or 'both'")

    if not os.path.exists(json_file):
        raise FileNotFoundError(f"JSON file not found: {json_file}")

    scraper = MongabayFullArticleScraper()
    articles = scraper.scrape_articles_from_json(json_file)

    # Generate readable timestamp for filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    print(f"\nTotal full articles scraped: {len(articles)}")

    if output_format in ['json', 'both']:
        json_file = f"{output}_{timestamp}.json"
        scraper.save_to_json(articles, json_file)
        print(f"Full articles saved to {json_file}")

    if output_format in ['csv', 'both']:
        csv_file = f"{output}_{timestamp}.csv"
        scraper.save_to_csv(articles, csv_file)
        print(f"Full articles saved to {csv_file}")

    return articles


def main():
    parser = argparse.ArgumentParser(description='Scrape full Mongabay.co.id articles from URLs in JSON file')
    parser.add_argument('--json-file', '-j', required=True, help='Path to JSON file containing article URLs')
    parser.add_argument('--output', '-o', default='mongabay_full_articles', help='Output filename (without extension)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                       help='Output format')

    args = parser.parse_args()

    scrape_mongabay_full_articles(
        json_file=args.json_file,
        output=args.output,
        output_format=args.format
    )


if __name__ == "__main__":
    main()
