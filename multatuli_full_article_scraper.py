#!/usr/bin/env python3
"""
Full article scraper for Project Multatuli articles.
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class MultatuliFullArticleScraper:
    def __init__(self, base_url="https://projectmultatuli.org", headless=True):
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

        # Setup Selenium WebDriver
        self.headless = headless
        self.driver = None

    def setup_driver(self):
        """Setup Selenium WebDriver."""
        if self.driver is None:
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36')

            try:
                # Use Selenium 4.x API with service
                from selenium.webdriver.chrome.service import Service
                service = Service(executable_path='/opt/homebrew/bin/chromedriver')
                self.driver = webdriver.Chrome(service=service, options=options)
                self.driver.implicitly_wait(3)
                print("Chrome driver setup successfully!")
            except Exception as e:
                print(f"Error setting up Chrome driver: {e}")
                print("Make sure Chrome and ChromeDriver are installed.")
                raise

    def teardown_driver(self):
        """Close Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def scrape_full_article(self, url):
        """
        Scrape a full article from a Multatuli URL.

        Parameters:
        - url (str): The URL of the article to scrape

        Returns:
        - dict: Dictionary containing all extracted article data
        """
        print(f"Scraping article: {url}")

        try:
            # Navigate to the article page
            self.driver.get(url)

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )

        except Exception as e:
            print(f"Error loading article {url}: {e}")
            return None

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        article_data = {}

        # Extract title from h1 elementor-heading-title
        title_elem = soup.find('h1', class_='elementor-heading-title')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        else:
            # Fallback: try any h1
            title_elem = soup.find('h1')
            if title_elem:
                article_data['title'] = title_elem.get_text(strip=True)

        # Extract cover image URL and caption from figure.wp-caption
        cover_image_url = None
        cover_image_caption = None

        cover_figure = soup.find('figure', class_='wp-caption')
        if cover_figure:
            img_elem = cover_figure.find('img')
            if img_elem:
                cover_image_url = img_elem.get('src') or img_elem.get('data-src')

            figcaption_elem = cover_figure.find('figcaption', class_='widget-image-caption')
            if figcaption_elem:
                cover_image_caption = figcaption_elem.get_text(strip=True)

        article_data['cover_image_url'] = cover_image_url
        article_data['cover_image_caption'] = cover_image_caption

        # Extract author from post info with itemprop="author"
        author_elem = soup.find('li', itemprop='author')
        if author_elem:
            author_link = author_elem.find('a')
            if author_link:
                article_data['author'] = author_link.get_text(strip=True)
            else:
                # Fallback: get text directly from li element
                author_text = author_elem.get_text(strip=True)
                if author_text:
                    article_data['author'] = author_text

        # Extract date from post info with itemprop="datePublished"
        date_elem = soup.find('li', itemprop='datePublished')
        if date_elem:
            date_span = date_elem.find('span', class_='elementor-post-info__item--type-date')
            if date_span:
                article_data['date'] = date_span.get_text(strip=True)

        # Extract category from post info with itemprop="about"
        category_elem = soup.find('li', itemprop='about')
        if category_elem:
            category_link = category_elem.find('a', class_='elementor-post-info__terms-list-item')
            if category_link:
                article_data['category'] = category_link.get_text(strip=True)

        # Extract full text content
        # Look for main article content - try various selectors
        content_selectors = [
            'div.elementor-element.elementor-widget-theme-post-content',
            'div.entry-content',
            'div.post-content',
            'div.content',
            'article',
            'div.elementor-widget-container'
        ]

        full_text = ""
        content_elem = None

        for selector in content_selectors:
            if '.' in selector:
                parts = selector.split('.')
                tag = parts[0]
                classes = parts[1:]
                content_elem = soup.find(tag, class_=lambda x: x and all(cls in x for cls in classes))
            else:
                content_elem = soup.find(selector)

            if content_elem:
                break

        # If no specific content container found, try to find paragraphs after the title
        if not content_elem:
            title_elem = soup.find('h1', class_='elementor-heading-title')
            if title_elem:
                # Find all content after the title
                content_candidates = title_elem.find_all_next(['p', 'div', 'h2', 'h3', 'h4', 'blockquote'])
                if content_candidates:
                    content_elem = content_candidates[0].parent

        if content_elem:
            # Extract text from paragraphs and other text elements
            paragraphs = content_elem.find_all(['p', 'h2', 'h3', 'h4', 'blockquote', 'div'])
            text_parts = []

            for para in paragraphs:
                # Skip elements that are likely not part of the main article text
                if para.find_parent(['aside', 'footer', 'nav', 'header', 'figure', 'figcaption']):
                    continue

                # Skip elements that contain metadata or navigation
                classes = para.get('class', [])
                if any(cls in ['elementor-post-info', 'wp-caption-text', 'widget-image-caption'] for cls in classes):
                    continue

                text = para.get_text(strip=True)
                if text and len(text) > 20:  # Filter out very short texts that might be metadata
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

        # Setup driver once for all articles
        try:
            self.setup_driver()
        except Exception as e:
            print(f"Failed to setup driver: {e}")
            return []

        full_articles = []

        try:
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
                    print(f"✓ Successfully scraped: {full_article_data.get('title', 'Unknown title')[:60]}...")
                else:
                    print(f"✗ Failed to scrape article: {url}")
                    # Still add the basic data if scraping failed
                    full_articles.append(article)

                # Add delay to be respectful to the server
                time.sleep(2)
        finally:
            # Always cleanup driver
            self.teardown_driver()

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
                'cover_image_url': article.get('cover_image_url', ''),
                'cover_image_caption': article.get('cover_image_caption', ''),
                'author': article.get('author', ''),
                'date': article.get('date', ''),
                'category': article.get('category', ''),
                'url': article.get('url', ''),
                'scraped_at': article.get('scraped_at', ''),
                'full_text': article.get('full_text', '')
            }
            csv_data.append(csv_row)

        fieldnames = ['title', 'cover_image_url', 'cover_image_caption', 'author', 'date', 'category', 'url', 'scraped_at', 'full_text']

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)


def scrape_multatuli_full_articles(json_file, output='multatuli_full_articles', output_format='both', headless=True):
    """
    Scrape full Multatuli articles from URLs in a JSON file.

    Parameters:
    - json_file (str): Path to JSON file containing article URLs
    - output (str): Output filename (without extension), default 'multatuli_full_articles'
    - output_format (str): Output format ('json', 'csv', or 'both'), default 'both'
    - headless (bool): Run browser in headless mode, default True

    Returns:
    - list: List of scraped full articles
    """
    if output_format not in ['json', 'csv', 'both']:
        raise ValueError("output_format must be 'json', 'csv', or 'both'")

    if not os.path.exists(json_file):
        raise FileNotFoundError(f"JSON file not found: {json_file}")

    scraper = MultatuliFullArticleScraper(headless=headless)
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
    parser = argparse.ArgumentParser(description='Scrape full Project Multatuli articles from URLs in JSON file')
    parser.add_argument('--json-file', '-j', required=True, help='Path to JSON file containing article URLs')
    parser.add_argument('--output', '-o', default='multatuli_full_articles', help='Output filename (without extension)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                       help='Output format')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                       help='Run browser in visible mode')

    args = parser.parse_args()

    scrape_multatuli_full_articles(
        json_file=args.json_file,
        output=args.output,
        output_format=args.format,
        headless=args.headless
    )


if __name__ == "__main__":
    main()
