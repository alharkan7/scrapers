#!/usr/bin/env python3
"""
Web scraper for Good News from Indonesia (goodnewsfromindonesia.id).
Scrapes article URLs from topic pages with configurable parameters.

Pagination logic:
- Pages are sorted from newest to oldest (page 1 has latest articles)
- DATE_END is the latest date we want to include
- DATE_START is the earliest date we want to include
- Skip pages with articles newer than DATE_END
- Start scraping when we find articles on or before DATE_END
- Stop when all articles on a page are older than DATE_START
"""

import requests
from bs4 import BeautifulSoup
import csv
import argparse
import time
import os
from datetime import datetime
from urllib.parse import urlencode


class GoodNewsScraper:
    def __init__(self, base_url="https://www.goodnewsfromindonesia.id", output_dir="data"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        })
        self.output_dir = output_dir
        self.seen_urls = set()

    def ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")

    def load_existing_urls(self, output_file):
        """Load existing URLs from CSV file to avoid duplicates."""
        if not os.path.exists(output_file):
            return

        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get('url')
                    if url:
                        self.seen_urls.add(url)
            print(f"Loaded {len(self.seen_urls)} existing URLs from {output_file}")
        except Exception as e:
            print(f"Warning: Could not load existing URLs: {e}")

    def init_csv_file(self, output_file):
        """Initialize CSV file with headers if it doesn't exist."""
        if not os.path.exists(output_file):
            fieldnames = ['url', 'topic', 'title', 'author', 'date', 'date_raw', 'image_url']
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            print(f"Created new CSV file: {output_file}")

    def append_to_csv(self, articles, output_file):
        """Append articles to CSV file."""
        if not articles:
            return

        fieldnames = ['url', 'topic', 'title', 'author', 'date', 'date_raw', 'image_url']

        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(output_file)

        with open(output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write headers if file doesn't exist
            if not file_exists:
                writer.writeheader()

            writer.writerows(articles)

    def get_page_content(self, topic, page):
        """Fetch the content of a specific topic page."""
        url = f"{self.base_url}/topic/{topic}?page={page}"
        print(f"Fetching: {url}")
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def parse_date(self, date_str):
        """
        Parse date string from Indonesian format to YYYY-MM-DD.
        Example: "2 Feb 2026" -> "2026-02-02"
        """
        # Month mapping for Indonesian abbreviations
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'Mei': '05', 'Jun': '06', 'Jul': '07', 'Agu': '08',
            'Sep': '09', 'Okt': '10', 'Nov': '11', 'Des': '12'
        }
        
        # Split the date string
        parts = date_str.split()
        if len(parts) >= 3:
            day = parts[0].zfill(2)  # Pad with leading zero if needed
            month_abbr = parts[1]
            year = parts[2]
            month = month_map.get(month_abbr, '01')
            return f"{year}-{month}-{day}"
        return None

    def classify_articles_by_date(self, articles, date_start, date_end):
        """
        Classify articles by their date relative to the target range.
        
        Returns:
            tuple: (too_new, in_range, too_old) lists of articles
        """
        too_new = []
        in_range = []
        too_old = []
        
        for article in articles:
            article_date = self.parse_date(article.get('date_raw', ''))
            if not article_date:
                # If we can't parse the date, include it to be safe
                in_range.append(article)
                continue
            
            if article_date > date_end:
                too_new.append(article)
            elif article_date >= date_start:
                in_range.append(article)
            else:  # article_date < date_start
                too_old.append(article)
        
        return too_new, in_range, too_old

    def extract_articles(self, html_content, topic):
        """Extract articles from HTML content without date filtering."""
        soup = BeautifulSoup(html_content, 'lxml')
        articles = []

        # Find all thumbnail-list containers
        article_containers = soup.find_all('div', class_='thumbnail-list')

        for container in article_containers:
            article = {}

            # Extract URL and Title
            title_link = container.find('h2', class_='thumbnail-list--title')
            if title_link:
                a_tag = title_link.find('a')
                if a_tag:
                    article['url'] = a_tag.get('href')
                    article['title'] = a_tag.get('title') or a_tag.get_text(strip=True)

            # Extract Topic
            category_elem = container.find('div', class_='thumbnail-list--category')
            if category_elem:
                a_tag = category_elem.find('a')
                if a_tag:
                    article['topic'] = a_tag.get_text(strip=True)

            # Extract Author
            author_elem = container.find('div', class_='thumbnail-list--author')
            if author_elem:
                author_link = author_elem.find('a')
                if author_link:
                    article['author'] = author_link.get_text(strip=True)

            # Extract Date
            if author_elem:
                # Date is in the last span with title attribute
                spans = author_elem.find_all('span')
                for span in spans:
                    if span.get('title'):
                        date_raw = span.get_text(strip=True)
                        article['date_raw'] = date_raw
                        article['date'] = self.parse_date(date_raw)
                        break

            # Extract Image URL
            img_container = container.find('div', class_='thumbnail-list-images')
            if img_container:
                img = img_container.find('img')
                if img:
                    # Try src first, then data-src for lazy-loaded images
                    article['image_url'] = img.get('src') or img.get('data-src')

            # Only include if we have basic info
            if article.get('url'):
                articles.append(article)

        return articles

    def scrape_topic(self, topic, start_page, end_page, date_start, date_end, output_file):
        """
        Scrape articles from a specific topic with date-aware pagination.
        
        Pagination logic:
        - Pages are sorted from newest to oldest (page 1 has latest articles)
        - Skip pages where all articles are newer than DATE_END
        - Start scraping when we find articles on or before DATE_END
        - Stop when all articles on a page are older than DATE_START
        
        Args:
            topic: Topic name
            start_page: Starting page number
            end_page: Ending page number (0 for infinite)
            date_start: Start date in YYYY-MM-DD format (earliest date to include)
            date_end: End date in YYYY-MM-DD format (latest date to include)
            output_file: Path to output CSV file
            
        Returns:
            int: Number of new articles scraped
        """
        total_new_articles = 0
        page = start_page
        scraping_started = False
        
        while True:
            # Check if we've reached the end page
            if end_page > 0 and page > end_page:
                print(f"Reached end page {end_page}. Stopping.")
                break

            print(f"\n{'='*60}")
            print(f"Checking {topic} - page {page}")
            print(f"{'='*60}")
            
            html_content = self.get_page_content(topic, page)

            if not html_content:
                print(f"Failed to fetch page {page}. Stopping.")
                break

            # Check if page has no more content ("Belum ada konten yang tersedia")
            if "Belum ada konten yang tersedia" in html_content:
                print("No more content available. Stopping.")
                break

            # Extract all articles from this page
            articles = self.extract_articles(html_content, topic)
            
            if not articles:
                print(f"No articles found on page {page}. Stopping.")
                break

            # Classify articles by date
            too_new, in_range, too_old = self.classify_articles_by_date(articles, date_start, date_end)
            
            print(f"Date analysis: {len(too_new)} too new, {len(in_range)} in range, {len(too_old)} too old")
            
            # Decide whether to start/stop scraping
            if not scraping_started:
                # We haven't started scraping yet
                if len(too_new) > 0 and len(in_range) == 0 and len(too_old) == 0:
                    # All articles are too new, skip this page
                    print(f"All {len(too_new)} articles are newer than {date_end}. Skipping page.")
                else:
                    # Found our first page to scrape
                    scraping_started = True
                    print(f"Found first page with articles in date range. Starting to scrape.")
            else:
                # Already scraping
                if len(too_old) > 0 and len(in_range) == 0:
                    # All articles are too old, stop scraping
                    print(f"All articles on this page are before {date_start}. Stopping.")
                    break
            
            # Only process articles in range if we've started scraping
            if scraping_started:
                # Filter out already seen URLs
                new_articles = []
                for article in in_range:
                    url = article.get('url')
                    if url and url not in self.seen_urls:
                        new_articles.append(article)
                        self.seen_urls.add(url)
                
                if new_articles:
                    print(f"Saving {len(new_articles)} new articles to CSV")
                    self.append_to_csv(new_articles, output_file)
                    total_new_articles += len(new_articles)
                elif in_range:
                    print(f"All {len(in_range)} articles in range are already scraped")
            
            # Add a small delay to be respectful to the server
            time.sleep(1)

            page += 1

        return total_new_articles


def scrape_articles(topics, date_start, date_end, page_start=1, page_end=0,
                   output_file="goodnews_id_urls"):
    """
    Scrape Good News from Indonesia articles.

    Parameters:
    - topics (list): List of topics to scrape
    - date_start (str): Start date in YYYY-MM-DD format (earliest date to include)
    - date_end (str): End date in YYYY-MM-DD format (latest date to include)
    - page_start (int): Starting page number, default 1
    - page_end (int): Ending page number, 0 for infinite, default 0
    - output_file (str): Output CSV filename (with or without .csv extension), default 'goodnews_id_urls'

    Returns:
    - int: Total number of new articles scraped
    """
    scraper = GoodNewsScraper()
    scraper.ensure_output_dir()

    # Ensure output file has .csv extension
    if not output_file.endswith('.csv'):
        output_file = f"{output_file}.csv"

    # Full path to output file
    output_path = os.path.join(scraper.output_dir, output_file)

    # Initialize CSV file and load existing URLs
    scraper.init_csv_file(output_path)
    scraper.load_existing_urls(output_path)

    total_new_articles = 0

    for topic in topics:
        print(f"\n{'#'*60}")
        print(f"Scraping topic: {topic}")
        print(f"Date range: {date_start} to {date_end}")
        print(f"Page range: {page_start} to {'infinite' if page_end == 0 else page_end}")
        print(f"Output: {output_path}")
        print(f"{'#'*60}")

        new_articles = scraper.scrape_topic(topic, page_start, page_end, date_start, date_end, output_path)
        total_new_articles += new_articles

        print(f"\n{'#'*60}")
        print(f"New articles from {topic}: {new_articles}")
        print(f"{'#'*60}")

    print(f"\n{'='*60}")
    print(f"Total new articles scraped across all topics: {total_new_articles}")
    print(f"Output saved to: {output_path}")
    print(f"{'='*60}")

    return total_new_articles


def main():
    # Import config values
    from scraper_url_config import TOPIC, DATE_START, DATE_END, PAGE_START, PAGE_END

    parser = argparse.ArgumentParser(description='Scrape Good News from Indonesia articles')
    parser.add_argument('--topics', '-t', nargs='+', help='Topics to scrape (default: from config)')
    parser.add_argument('--date-start', '-ds', help='Start date in YYYY-MM-DD format (default: from config)')
    parser.add_argument('--date-end', '-de', help='End date in YYYY-MM-DD format (default: from config)')
    parser.add_argument('--page-start', '-ps', type=int, help='Starting page number (default: from config)')
    parser.add_argument('--page-end', '-pe', type=int, help='Ending page number, 0 for infinite (default: from config)')
    parser.add_argument('--output', '-o', default='goodnews_id_urls', help='Output CSV filename (default: goodnews_id_urls)')

    args = parser.parse_args()

    # Use command line args if provided, otherwise use config values
    topics = args.topics if args.topics else TOPIC
    date_start = args.date_start if args.date_start else DATE_START
    date_end = args.date_end if args.date_end else DATE_END
    page_start = args.page_start if args.page_start else PAGE_START
    page_end = args.page_end if args.page_end is not None else PAGE_END

    scrape_articles(
        topics=topics,
        date_start=date_start,
        date_end=date_end,
        page_start=page_start,
        page_end=page_end,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
