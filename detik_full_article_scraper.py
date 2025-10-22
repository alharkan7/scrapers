#!/usr/bin/env python3
"""
Full article scraper for Detik.com articles.
Scrapes complete article content including metadata and full text from article URLs.
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


class DetikFullArticleScraper:
    def __init__(self):
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_article_content(self, url):
        """Fetch the content of a specific article URL."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching article {url}: {e}")
            return None

    def parse_date_time(self, date_time_str):
        """Parse date and time from Detik format: 'Jumat, 18 Okt 2024 13:41 WIB'"""
        if not date_time_str:
            return None, None

        # Detik format is: 'Day, DD MMM YYYY HH:MM WIB'
        # Extract date and time parts
        parts = date_time_str.split()
        if len(parts) >= 5:
            # Date part: "Jumat, 18 Okt 2024"
            date_parts = parts[:4]  # Skip the comma
            date_str = ' '.join(date_parts).rstrip(',')

            # Time part: "13:41 WIB"
            time_str = ' '.join(parts[4:]).replace('WIB', '').strip()
            return date_str, time_str

        return date_time_str, None

    def extract_full_article_data(self, url):
        """Extract all metadata and full text from a Detik article URL."""
        html_content = self.get_article_content(url)
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, 'lxml')
        article_data = {
            'url': url,
            'title': None,
            'date': None,
            'time': None,
            'author': None,
            'category': None,
            'full_text': None,
            'image_url': None,
            'image_caption': None,
            'scraped_at': datetime.now().isoformat()
        }

        # Extract title
        title_elem = soup.find('h1', class_='detail__title')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)

        # Extract category
        category_elem = soup.find('h2', class_='detail__subtitle')
        if category_elem:
            article_data['category'] = category_elem.get_text(strip=True)

        # Extract date and time
        date_elem = soup.find('div', class_='detail__date')
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            date_str, time_str = self.parse_date_time(date_text)
            article_data['date'] = date_str
            article_data['time'] = time_str

        # Extract author
        author_elem = soup.find('div', class_='box-kolumnis__desc')
        if author_elem:
            author_name_elem = author_elem.find('h5')
            if author_name_elem:
                article_data['author'] = author_name_elem.get_text(strip=True)

        # Extract main image and caption
        media_container = soup.find('div', class_='detail__media')
        if media_container:
            img_elem = media_container.find('img')
            if img_elem and img_elem.get('src'):
                article_data['image_url'] = img_elem['src']

            # Extract image caption
            caption_elem = media_container.find('figcaption', class_='detail__media-caption')
            if caption_elem:
                article_data['image_caption'] = caption_elem.get_text(strip=True)

        # Extract full text content - Detik specific selectors
        content_selectors = [
            '.detail__body-text',
            '.detail__body',
            '.itp_bodycontent',
            '[data-component="Core/ReadMore"]',
            '.detail__readmore'
        ]

        full_text = []
        content_found = False

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Get all paragraphs within the content area
                paragraphs = content_elem.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 10:  # Filter out very short paragraphs
                        full_text.append(text)

                if full_text:
                    content_found = True
                    break

        # If no structured content found, try alternative selectors
        if not content_found:
            # Try to find content in div with itp_bodycontent class
            body_content = soup.find('div', class_='itp_bodycontent')
            if body_content:
                paragraphs = body_content.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 10:
                        full_text.append(text)
                content_found = True

        # If still no content, try general paragraph search with filtering
        if not content_found:
            all_paragraphs = soup.find_all('p')
            for p in all_paragraphs:
                text = p.get_text(strip=True)
                # Filter out navigation, footer, and other non-article content
                if (text and len(text) > 30 and
                    not any(skip_word in text.lower() for skip_word in
                           ['copyright', 'privacy policy', 'disclaimer', 'tentang detik',
                            'redaksi', 'editor', 'reporter', 'follow us', 'baca juga',
                            'simak juga', 'lihat juga']) and
                    not text.startswith('Baca Juga') and
                    not text.startswith('Simak') and
                    not text.startswith('Lihat')):
                    full_text.append(text)

        article_data['full_text'] = '\n\n'.join(full_text) if full_text else None

        return article_data

    def save_to_csv(self, articles, filename):
        """Save full articles to CSV file."""
        if not articles:
            print("No articles to save.")
            return

        # Collect all possible fieldnames from the articles
        fieldnames = set()
        for article in articles:
            fieldnames.update(article.keys())

        # Sort fieldnames for consistent output
        fieldnames = sorted(list(fieldnames))

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(articles)

    def load_article_list(self, json_file):
        """Load article metadata from JSON file."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File {json_file} not found.")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")
            return None

    def scrape_full_articles_from_file(self, input_json_file, output_file=None, output_format='json'):
        """
        Scrape full content for all articles in the input JSON file.

        Parameters:
        - input_json_file (str): Path to JSON file with article metadata
        - output_file (str): Output filename (optional, will auto-generate with timestamp if not provided)
        - output_format (str): Output format ('json', 'csv', or 'both'), default 'json'

        Returns:
        - list: List of full article data
        """
        if output_format not in ['json', 'csv', 'both']:
            raise ValueError("output_format must be 'json', 'csv', or 'both'")

        articles_metadata = self.load_article_list(input_json_file)
        if not articles_metadata:
            return None

        if not output_file:
            # Generate timestamped output filename
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            base_name = os.path.splitext(os.path.basename(input_json_file))[0]
            output_file = f"{base_name}_full_{timestamp}"

        full_articles = []
        total_articles = len(articles_metadata)

        print(f"Starting to scrape {total_articles} articles...")

        for i, article_meta in enumerate(articles_metadata, 1):
            url = article_meta.get('url')
            if not url:
                print(f"Skipping article {i}: No URL found")
                continue

            print(f"Scraping article {i}/{total_articles}: {url}")
            full_article_data = self.extract_full_article_data(url)

            if full_article_data and isinstance(full_article_data, dict):
                # Merge original metadata with full content
                merged_data = {**article_meta, **full_article_data}
                # Remove duplicate keys, preferring the full scraped data
                full_articles.append(merged_data)
                title = full_article_data.get('title', 'Unknown title')
                if title and isinstance(title, str):
                    print(f"✓ Successfully scraped article: {title[:50]}...")
                else:
                    print(f"✓ Successfully scraped article: Unknown title...")
            else:
                print(f"✗ Failed to scrape article: {url}")
                # Still include the original metadata if scraping failed
                full_articles.append(article_meta)

            # Add a small delay to be respectful to the server
            time.sleep(1)

        # Generate readable timestamp for filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Save to JSON file
        if output_format in ['json', 'both']:
            json_file = f"{output_file}_{timestamp}.json" if output_format == 'both' else f"{output_file}.json" if not output_file.endswith('.json') else output_file
            try:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(full_articles, f, ensure_ascii=False, indent=2)
                print(f"Full articles saved to {json_file}")
            except Exception as e:
                print(f"Error saving JSON file: {e}")

        # Save to CSV file
        if output_format in ['csv', 'both']:
            csv_file = f"{output_file}_{timestamp}.csv" if output_format == 'both' else f"{output_file}.csv" if not output_file.endswith('.csv') else output_file
            try:
                self.save_to_csv(full_articles, csv_file)
                print(f"Full articles saved to {csv_file}")
            except Exception as e:
                print(f"Error saving CSV file: {e}")

        return full_articles


def scrape_full_articles(input_json_file, output_file=None, output_format='json'):
    """
    Scrape full article content from Detik.com article URLs.

    Parameters:
    - input_json_file (str): Path to JSON file with article metadata
    - output_file (str): Output filename (optional, will auto-generate with timestamp if not provided)
    - output_format (str): Output format ('json', 'csv', or 'both'), default 'json'

    Returns:
    - list: List of full article data
    """
    if output_format not in ['json', 'csv', 'both']:
        raise ValueError("output_format must be 'json', 'csv', or 'both'")

    scraper = DetikFullArticleScraper()
    return scraper.scrape_full_articles_from_file(input_json_file, output_file, output_format)


def main():
    parser = argparse.ArgumentParser(description='Scrape full article content from Detik.com article URLs')
    parser.add_argument('input_json', help='Input JSON file with article metadata')
    parser.add_argument('--output', '-o', help='Output filename (optional, will auto-generate with timestamp)')
    parser.add_argument('--format', '-f', choices=['json', 'csv', 'both'], default='json',
                       help='Output format')

    args = parser.parse_args()

    scrape_full_articles(args.input_json, args.output, args.format)


if __name__ == "__main__":
    main()
