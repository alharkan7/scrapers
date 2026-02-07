#!/usr/bin/env python3
"""
Web scraper for detailed article pages from Good News from Indonesia.
Scrapes full article content from URLs in a CSV file.
"""

import requests
from bs4 import BeautifulSoup
import csv
import argparse
import time
import os
import re
import json
from datetime import datetime


class GoodNewsDetailedScraper:
    def __init__(self, base_url="https://www.goodnewsfromindonesia.id", output_dir="data"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        })
        self.output_dir = output_dir

    def ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")

    def load_scraped_urls(self, output_file):
        """Load URLs that have already been scraped from JSON Lines file."""
        scraped_urls = set()
        if not os.path.exists(output_file):
            return scraped_urls

        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            article = json.loads(line)
                            url = article.get('url')
                            if url:
                                scraped_urls.add(url)
                        except json.JSONDecodeError:
                            continue
            print(f"Loaded {len(scraped_urls)} already-scraped URLs from {output_file}")
        except Exception as e:
            print(f"Warning: Could not load existing URLs: {e}")

        return scraped_urls

    def load_urls_from_csv(self, input_file):
        """Load URLs to scrape from CSV file."""
        urls_data = []
        
        if not os.path.exists(input_file):
            print(f"Input file not found: {input_file}")
            return urls_data

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get('url')
                    if url:
                        urls_data.append({
                            'url': url,
                            'topic': row.get('topic', ''),
                            'author': row.get('author', ''),
                            'date': row.get('date', ''),
                            'title': row.get('title', ''),
                            'image_url': row.get('image_url', '')
                        })
            
            print(f"Loaded {len(urls_data)} URLs from {input_file}")
        except Exception as e:
            print(f"Error reading input CSV: {e}")

        return urls_data

    def extract_reading_length(self, date_str):
        """
        Extract reading length from date string.
        Example: "8 Desember 2025 08.00 WIB • 2 menit" -> "2 menit"
        """
        # Look for pattern like "• X menit" where X is a number
        match = re.search(r'•\s*(\d+\s*(?:menit|jam|jam\s*\d+\s*menit))', date_str)
        if match:
            return match.group(1).strip()
        return ""

    def get_article_content(self, url):
        """Fetch article page content."""
        print(f"Fetching: {url}")
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching article: {e}")
            return None

    def extract_article_details(self, html_content, url, basic_data):
        """Extract detailed article information from HTML."""
        soup = BeautifulSoup(html_content, 'lxml')
        
        article_data = {
            'url': url,
            'topic': basic_data.get('topic', ''),
            'author': basic_data.get('author', ''),
            'date_time': '',
            'full_title': '',
            'reading_length': '',
            'cover_image_url': '',
            'cover_image_caption': '',
            'full_article_content': '',
            'tags': ''
        }

        # Extract date time and reading length
        date_elem = soup.find('div', class_='article-author-date')
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            article_data['date_time'] = date_text
            article_data['reading_length'] = self.extract_reading_length(date_text)

        # Extract full title
        title_elem = soup.find('h1', class_='article-title')
        if title_elem:
            article_data['full_title'] = title_elem.get_text(strip=True)

        # Extract cover image URL
        cover_img = soup.find('div', class_='article-photos')
        if cover_img:
            img = cover_img.find('img', class_='img-fluid')
            if img:
                article_data['cover_image_url'] = img.get('src') or img.get('data-src')

        # Extract cover image caption
        caption_div = soup.find('div', class_='article-photos-source')
        if caption_div:
            p_elem = caption_div.find('p', class_='mb-0')
            if p_elem:
                article_data['cover_image_caption'] = p_elem.get_text(strip=True)

        # Extract full article content
        # The content is spread across multiple div class="article-content" elements
        content_parts = []
        content_divs = soup.find_all('div', class_='article-content')
        
        for div in content_divs:
            # Remove "baca juga" sections (related articles)
            baca_juga = div.find('div', class_='article-read')
            if baca_juga:
                baca_juga.decompose()
            
            # Get text content
            text = div.get_text(separator='\n', strip=True)
            if text:
                content_parts.append(text)
        
        article_data['full_article_content'] = '\n\n'.join(content_parts)

        # Extract tags
        tag_div = soup.find('div', class_='article-tag')
        if tag_div:
            tags = []
            tag_links = tag_div.find_all('a')
            for tag_link in tag_links:
                tag_text = tag_link.get_text(strip=True)
                if tag_text and tag_text != "TAG:":
                    tags.append(tag_text)
            article_data['tags'] = tags

        return article_data

    def append_to_jsonl(self, article_data, output_file):
        """Append article data to JSON Lines file (one JSON object per line)."""
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(article_data, ensure_ascii=False) + '\n')

    def scrape_article(self, url, basic_data, output_file):
        """
        Scrape a single article and save to JSON Lines file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        html_content = self.get_article_content(url)
        if not html_content:
            return False

        try:
            article_data = self.extract_article_details(html_content, url, basic_data)
            
            # Write to JSON Lines file immediately
            self.append_to_jsonl(article_data, output_file)
            print(f"Saved article: {article_data.get('full_title', url)}")
            
            return True
        except Exception as e:
            print(f"Error processing article {url}: {e}")
            return False

    def scrape_articles(self, input_file, output_file="goodnews_id_details.jsonl"):
        """
        Scrape detailed articles from URLs in input CSV file.
        
        Parameters:
        - input_file (str): Path to input CSV file with URLs
        - output_file (str): Path to output JSON Lines file, default 'goodnews_id_details.jsonl'
        
        Returns:
            dict: Statistics about scraping run
        """
        stats = {
            'total_urls': 0,
            'already_scraped': 0,
            'successfully_scraped': 0,
            'failed': 0
        }

        # Ensure output directory exists
        self.ensure_output_dir()

        # Full path to output file
        output_path = os.path.join(self.output_dir, output_file)

        # Load already-scraped URLs to avoid duplicates
        scraped_urls = self.load_scraped_urls(output_path)

        # Load URLs to scrape
        urls_data = self.load_urls_from_csv(input_file)
        stats['total_urls'] = len(urls_data)

        if not urls_data:
            print("No URLs to scrape.")
            return stats

        print(f"\n{'='*60}")
        print(f"Starting detailed scraping")
        print(f"Input: {input_file}")
        print(f"Output: {output_path}")
        print(f"Format: JSON Lines (one JSON object per line)")
        print(f"{'='*60}\n")

        for i, url_data in enumerate(urls_data, 1):
            url = url_data['url']

            # Check if already scraped
            if url in scraped_urls:
                print(f"\n[{i}/{stats['total_urls']}] Skipping already scraped: {url}")
                stats['already_scraped'] += 1
                continue

            print(f"\n[{i}/{stats['total_urls']}] Processing: {url}")

            # Scrape article
            success = self.scrape_article(url, url_data, output_path)

            if success:
                stats['successfully_scraped'] += 1
                scraped_urls.add(url)
            else:
                stats['failed'] += 1

            # Add a small delay to be respectful to server
            time.sleep(1)

        return stats


def main():
    parser = argparse.ArgumentParser(description='Scrape detailed article content from Good News from Indonesia URLs')
    parser.add_argument('--input', '-i', default='data/goodnews_id_urls.csv',
                       help='Input CSV file with URLs (default: data/goodnews_id_urls.csv)')
    parser.add_argument('--output', '-o', default='goodnews_id_details.jsonl',
                       help='Output JSON Lines file (default: goodnews_id_details.jsonl)')

    args = parser.parse_args()

    # If input file is relative path, check in data directory
    input_file = args.input
    if not os.path.isabs(input_file) and not os.path.exists(input_file):
        # Try in data directory
        input_file = os.path.join('data', args.input)

    scraper = GoodNewsDetailedScraper()
    stats = scraper.scrape_articles(input_file, args.output)

    print(f"\n{'='*60}")
    print("Scraping Complete!")
    print(f"{'='*60}")
    print(f"Total URLs in input: {stats['total_urls']}")
    print(f"Already scraped: {stats['already_scraped']}")
    print(f"Successfully scraped: {stats['successfully_scraped']}")
    print(f"Failed: {stats['failed']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
