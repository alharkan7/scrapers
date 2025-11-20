#!/usr/bin/env python3
"""
Web scraper for Detik.com search results.
Scrapes articles from https://www.detik.com/search/searchnews with configurable parameters.
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import argparse
import time
import re
from datetime import datetime
from urllib.parse import urlencode


class DetikScraper:
    def __init__(self, base_url="https://www.detik.com/search/searchnews"):
        self.base_url = base_url
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_page_content(self, params):
        """Fetch the content of a specific search page."""
        url = f"{self.base_url}?{urlencode(params)}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page with params {params}: {e}")
            return None

    def extract_image_url(self, media_image):
        """Extract image URL from media__image div."""
        # First try to get from img src
        img_elem = media_image.find('img')
        if img_elem and img_elem.get('src'):
            return img_elem['src']

        # If no img element, try to extract from background-image style
        ratiobox = media_image.find('span', class_='ratiobox')
        if ratiobox and ratiobox.get('style'):
            style = ratiobox['style']
            # Extract URL from background-image: url("...");
            match = re.search(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
            if match:
                return match.group(1)

        return None

    def extract_articles(self, soup):
        """Extract articles from the search results page."""
        articles = []

        # Find all article containers
        article_containers = soup.find_all('div', class_='media media--right media--image-radius block-link')

        for container in article_containers:
            article = {}

            # Extract title
            title_elem = container.find('h3', class_='media__title')
            if title_elem:
                title_link = title_elem.find('a')
                if title_link:
                    article['title'] = title_link.get_text(strip=True)
                    article['url'] = title_link.get('href')

            # Extract image URL
            media_image = container.find('div', class_='media__image')
            if media_image:
                article['image_url'] = self.extract_image_url(media_image)

            # Extract description
            desc_elem = container.find('div', class_='media__desc')
            if desc_elem:
                article['description'] = desc_elem.get_text(strip=True)

            # Extract date
            date_elem = container.find('div', class_='media__date')
            if date_elem:
                span_elem = date_elem.find('span')
                if span_elem:
                    article['date'] = span_elem.get_text(strip=True)

            # Extract subtitle (source/category)
            subtitle_elem = container.find('h2', class_='media__subtitle')
            if subtitle_elem:
                article['source'] = subtitle_elem.get_text(strip=True)

            if article:
                articles.append(article)

        return articles

    def scrape_page(self, params):
        """Scrape a single page and return all articles."""
        page_num = params.get('page', 1)
        print(f"Scraping page {page_num}...")

        html_content = self.get_page_content(params)
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'lxml')
        articles = self.extract_articles(soup)

        # Add a small delay to be respectful to the server
        time.sleep(1)

        return articles

    def scrape_range(self, base_params, start_page, end_page):
        """Scrape a range of pages."""
        all_articles = []

        for page_num in range(start_page, end_page + 1):
            params = base_params.copy()
            params['page'] = page_num
            page_articles = self.scrape_page(params)
            all_articles.extend(page_articles)
            print(f"Found {len(page_articles)} articles on page {page_num}")

        return all_articles

    def save_to_json(self, articles, filename):
        """Save articles to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

    def save_to_csv(self, articles, filename):
        """Save articles to CSV file."""
        if not articles:
            print("No articles to save.")
            return

        fieldnames = ['title', 'url', 'date', 'description', 'image_url', 'source']

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(articles)


def scrape_articles(query, start_page, end_page, result_type='relevansi',
                   fromdatex=None, todatex=None, output='detik_articles', output_format='both'):
    """
    Scrape Detik.com search results.

    Parameters:
    - query (str): Search query
    - start_page (int): Starting page number
    - end_page (int): Ending page number
    - result_type (str): Result type ('relevansi' or 'latest'), default 'relevansi'
    - fromdatex (str): Start date in DD/MM/YYYY format, optional
    - todatex (str): End date in DD/MM/YYYY format, optional
    - output (str): Output filename (without extension), default 'detik_articles'
    - output_format (str): Output format ('json', 'csv', or 'both'), default 'both'

    Returns:
    - list: List of scraped articles
    """
    if start_page > end_page:
        raise ValueError("start_page must be less than or equal to end_page")

    if result_type not in ['relevansi', 'latest']:
        raise ValueError("result_type must be 'relevansi' or 'latest'")

    if output_format not in ['json', 'csv', 'both']:
        raise ValueError("output_format must be 'json', 'csv', or 'both'")

    # Build base parameters
    base_params = {
        'query': query,
        'result_type': result_type,
        'siteid': 3
    }

    if fromdatex:
        base_params['fromdatex'] = fromdatex
    if todatex:
        base_params['todatex'] = todatex

    scraper = DetikScraper()
    articles = scraper.scrape_range(base_params, start_page, end_page)

    # Generate readable timestamp for filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    print(f"\nTotal articles scraped: {len(articles)}")

    if output_format in ['json', 'both']:
        json_file = f"{output}_{timestamp}.json"
        scraper.save_to_json(articles, json_file)
        print(f"Articles saved to {json_file}")

    if output_format in ['csv', 'both']:
        csv_file = f"{output}_{timestamp}.csv"
        scraper.save_to_csv(articles, csv_file)
        print(f"Articles saved to {csv_file}")

    return articles


def main():
    parser = argparse.ArgumentParser(description='Scrape Detik.com search results')
    parser.add_argument('query', help='Search query')
    parser.add_argument('start_page', type=int, help='Starting page number')
    parser.add_argument('end_page', type=int, help='Ending page number')
    parser.add_argument('--result-type', choices=['relevansi', 'latest'], default='relevansi',
                       help='Result type (default: relevansi)')
    parser.add_argument('--from-date', help='Start date in DD/MM/YYYY format')
    parser.add_argument('--to-date', help='End date in DD/MM/YYYY format')
    parser.add_argument('--output', '-o', default='detik_articles', help='Output filename (without extension)')
    parser.add_argument('--format', '-f', choices=['json', 'csv', 'both'], default='both',
                       help='Output format')

    args = parser.parse_args()

    scrape_articles(
        query=args.query,
        start_page=args.start_page,
        end_page=args.end_page,
        result_type=args.result_type,
        fromdatex=args.from_date,
        todatex=args.to_date,
        output=args.output,
        output_format=args.format
    )


if __name__ == "__main__":
    main()
