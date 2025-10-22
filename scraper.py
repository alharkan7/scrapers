#!/usr/bin/env python3
"""
Web scraper for NU Online Kesehatan articles.
Scrapes only articles tagged with "Kesehatan" from https://www.nu.or.id/kesehatan/{page}
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import argparse
import time
import re
from datetime import datetime


class NUOnlineScraper:
    def __init__(self, base_url="https://www.nu.or.id/kesehatan/"):
        self.base_url = base_url
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_page_content(self, page_number):
        """Fetch the content of a specific page."""
        url = f"{self.base_url}{page_number}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page {page_number}: {e}")
            return None

    def parse_date_time(self, date_time_str):
        """Parse date and time from the format: 'Rabu, 17 September 2025 | 21:00 WIB'"""
        if not date_time_str:
            return None, None

        # Split by '|' to separate date and time
        parts = date_time_str.split('|')
        if len(parts) == 2:
            date_str = parts[0].strip()
            time_str = parts[1].strip().replace('WIB', '').strip()
            return date_str, time_str
        return date_time_str, None

    def extract_cover_article(self, soup):
        """Extract the cover story article from the page."""
        # Find the cover story container
        cover_container = soup.find('div', class_=re.compile(r'border-gray2.*relative.*cursor-pointer'))

        if not cover_container:
            return None

        # Check if article has "Kesehatan" tag
        kesehatan_tag = cover_container.find('a', string=lambda text: text and 'Kesehatan' in text.strip())
        if not kesehatan_tag:
            return None

        article = {}

        # Extract title
        title_elem = cover_container.find('h1')
        if title_elem:
            article['title'] = title_elem.get_text(strip=True)

        # Extract URL
        url_elem = cover_container.find('a', href=re.compile(r'/kesehatan/'))
        if url_elem:
            article['url'] = f"https://www.nu.or.id{url_elem['href']}"

        # Extract image URL
        img_elem = cover_container.find('img')
        if img_elem and img_elem.get('src'):
            article['image_url'] = img_elem['src']

        # Extract date and time
        date_elem = cover_container.find('p', class_=re.compile(r'medium.*font-inter.*text-xs.*text-gray-400'))
        if date_elem:
            date_str, time_str = self.parse_date_time(date_elem.get_text(strip=True))
            article['date'] = date_str
            article['time'] = time_str

        return article if article else None

    def extract_regular_articles(self, soup):
        """Extract regular articles from the page."""
        articles = []

        # Find all regular article containers
        article_containers = soup.find_all('div', class_=re.compile(r'border-gray2.*flex.*w-full'))

        for container in article_containers:
            # Check if article has "Kesehatan" tag
            kesehatan_tag = container.find('a', string=lambda text: text and 'Kesehatan' in text.strip())
            if not kesehatan_tag:
                continue

            article = {}

            # Extract title
            title_elem = container.find('h2')
            if title_elem:
                article['title'] = title_elem.get_text(strip=True)

            # Extract URL
            url_elem = container.find('a', href=re.compile(r'/kesehatan/'))
            if url_elem:
                article['url'] = f"https://www.nu.or.id{url_elem['href']}"

            # Extract image URL
            img_elem = container.find('img')
            if img_elem and img_elem.get('src'):
                article['image_url'] = img_elem['src']

            # Extract date and time
            date_elem = container.find('p', class_=re.compile(r'medium.*font-inter.*text-xs.*text-gray-400'))
            if date_elem:
                date_str, time_str = self.parse_date_time(date_elem.get_text(strip=True))
                article['date'] = date_str
                article['time'] = time_str

            if article:
                articles.append(article)

        return articles

    def scrape_page(self, page_number):
        """Scrape a single page and return all articles."""
        print(f"Scraping page {page_number}...")

        html_content = self.get_page_content(page_number)
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'lxml')
        articles = []

        # Extract cover article
        cover_article = self.extract_cover_article(soup)
        if cover_article:
            articles.append(cover_article)

        # Extract regular articles
        regular_articles = self.extract_regular_articles(soup)
        articles.extend(regular_articles)

        # Add a small delay to be respectful to the server
        time.sleep(1)

        return articles

    def scrape_range(self, start_page, end_page):
        """Scrape a range of pages."""
        all_articles = []

        for page_num in range(start_page, end_page + 1):
            page_articles = self.scrape_page(page_num)
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

        fieldnames = ['title', 'url', 'date', 'time', 'image_url']

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(articles)


def scrape_articles(start_page, end_page, output='articles', output_format='both'):
    """
    Scrape NU Online articles tagged with "Kesehatan".

    Parameters:
    - start_page (int): Starting page number
    - end_page (int): Ending page number
    - output (str): Output filename (without extension), default 'articles'
    - output_format (str): Output format ('json', 'csv', or 'both'), default 'both'

    Returns:
    - list: List of scraped articles
    """
    if start_page > end_page:
        raise ValueError("start_page must be less than or equal to end_page")

    if output_format not in ['json', 'csv', 'both']:
        raise ValueError("output_format must be 'json', 'csv', or 'both'")

    scraper = NUOnlineScraper()
    articles = scraper.scrape_range(start_page, end_page)

    print(f"\nTotal articles scraped: {len(articles)}")

    if output_format in ['json', 'both']:
        json_file = f"{output}.json"
        scraper.save_to_json(articles, json_file)
        print(f"Articles saved to {json_file}")

    if output_format in ['csv', 'both']:
        csv_file = f"{output}.csv"
        scraper.save_to_csv(articles, csv_file)
        print(f"Articles saved to {csv_file}")

    return articles


def main():
    parser = argparse.ArgumentParser(description='Scrape NU Online articles tagged with "Kesehatan"')
    parser.add_argument('start_page', type=int, help='Starting page number')
    parser.add_argument('end_page', type=int, help='Ending page number')
    parser.add_argument('--output', '-o', default='articles', help='Output filename (without extension)')
    parser.add_argument('--format', '-f', choices=['json', 'csv', 'both'], default='both',
                       help='Output format')

    args = parser.parse_args()

    scrape_articles(args.start_page, args.end_page, args.output, args.format)


if __name__ == "__main__":
    main()
