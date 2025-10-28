#!/usr/bin/env python3
"""
Web scraper for Mongabay.co.id search results.
Scrapes articles about nickel mining from https://mongabay.co.id/?s=tambang%20nikel&formats=
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class MongabayScraper:
    def __init__(self, base_url="https://mongabay.co.id", headless=True):
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
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36')

            try:
                self.driver = webdriver.Chrome(options=options)
                self.driver.implicitly_wait(10)
            except Exception as e:
                print(f"Error setting up Chrome driver: {e}")
                print("Make sure Chrome and ChromeDriver are installed.")
                raise

    def teardown_driver(self):
        """Close Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def get_search_page_content(self, query="tambang nikel", formats=""):
        """Fetch the initial search page content."""
        params = {'s': query}
        if formats:
            params['formats'] = formats

        url = f"{self.base_url}/?{urlencode(params)}"
        print(f"Fetching URL: {url}")
        try:
            response = self.session.get(url, timeout=30)
            print(f"Response status: {response.status_code}")
            response.raise_for_status()
            print(f"Response content length: {len(response.text)}")
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching search page: {e}")
            return None

    def extract_image_url(self, img_elem):
        """Extract image URL from img element."""
        if not img_elem:
            return None

        # First try srcset (preferred for responsive images)
        srcset = img_elem.get('srcset')
        if srcset:
            # Take the first URL from srcset (usually the smallest/highest quality)
            urls = srcset.split(',')
            if urls:
                first_url = urls[0].strip().split()[0]
                return first_url

        # Fallback to src attribute
        return img_elem.get('src')

    def extract_articles_from_html(self, html_content):
        """Extract articles from HTML content."""
        soup = BeautifulSoup(html_content, 'lxml')
        articles = []

        # Find all article containers
        article_containers = soup.find_all('div', class_='article--container pv--8')

        for container in article_containers:
            article = {}

            # Extract title
            title_elem = container.find('h4')
            if title_elem:
                article['title'] = title_elem.get_text(strip=True)

            # Extract URL
            link_elem = container.find('a')
            if link_elem and link_elem.get('href'):
                article['url'] = link_elem['href']

            # Extract image URL
            img_elem = container.find('img')
            if img_elem:
                article['image_url'] = self.extract_image_url(img_elem)

            # Extract author
            author_elem = container.find('span', class_='byline')
            if author_elem:
                article['author'] = author_elem.get_text(strip=True)

            # Extract date
            date_elem = container.find('span', class_='date')
            if date_elem:
                article['date'] = date_elem.get_text(strip=True)

            if article:
                articles.append(article)

        return articles

    def load_more_articles(self, existing_urls, query="tambang nikel", formats=""):
        """
        Load more articles by clicking the 'Muat lebih banyak' button using Selenium.
        """
        if not self.driver:
            self.setup_driver()

        # Navigate to the search page if not already there
        params = {'s': query}
        if formats:
            params['formats'] = formats
        url = f"{self.base_url}/?{urlencode(params)}"

        if self.driver.current_url != url:
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load

        try:
            # Wait for articles to load initially
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "article--container"))
            )

            # Try to find and click the load more button
            load_more_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.load-more.theme--button.primary"))
            )

            # Scroll to the button to make sure it's visible
            self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            time.sleep(1)

            # Click the load more button
            load_more_button.click()
            print("Clicked load more button")

            # Wait for new articles to load
            time.sleep(3)

            # Get the updated page source
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'lxml')

            # Extract all articles from the updated page
            all_articles = self.extract_articles_from_html(html_content)

            # Filter out articles that were already seen
            new_articles = []
            for article in all_articles:
                url = article.get('url')
                if url and url not in existing_urls:
                    new_articles.append(article)

            return new_articles

        except TimeoutException:
            print("Load more button not found or not clickable")
            return []
        except Exception as e:
            print(f"Error loading more articles: {e}")
            return []

    def scrape_articles(self, query="tambang nikel", formats="", max_pages=None):
        """Scrape articles with load more functionality using Selenium."""
        all_articles = []
        seen_urls = set()

        print(f"Scraping articles for query: '{query}'")

        # Setup Selenium driver
        self.setup_driver()

        try:
            # Navigate to the search page
            params = {'s': query}
            if formats:
                params['formats'] = formats
            url = f"{self.base_url}/?{urlencode(params)}"
            self.driver.get(url)

            # Wait for initial articles to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "article--container"))
            )

            page_count = 0
            max_pages = max_pages or float('inf')

            while page_count < max_pages:
                # Get current page content
                html_content = self.driver.page_source
                current_articles = self.extract_articles_from_html(html_content)

                # Filter out already seen articles
                new_articles = []
                for article in current_articles:
                    url = article.get('url')
                    if url and url not in seen_urls:
                        new_articles.append(article)
                        seen_urls.add(url)
                        all_articles.append(article)

                if page_count == 0:
                    print(f"Found {len(new_articles)} articles on initial page")
                else:
                    print(f"Found {len(new_articles)} new articles on page {page_count + 1}")

                # Try to load more articles
                if page_count + 1 >= max_pages:
                    break

                try:
                    # Check if load more button exists and is visible
                    load_more_button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button.load-more.theme--button.primary"))
                    )

                    # Check if button is visible and enabled
                    if not load_more_button.is_displayed():
                        print("Load more button is not visible. Stopping.")
                        break

                    if not load_more_button.is_enabled():
                        print("Load more button is disabled. Stopping.")
                        break

                    # Scroll to the button to make sure it's in view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
                    time.sleep(1)

                    # Additional check - make sure no overlay is blocking the button
                    try:
                        # Try regular click first
                        load_more_button.click()
                        print(f"Successfully clicked load more button for page {page_count + 2}")
                    except Exception as click_error:
                        print(f"Regular click failed, trying JavaScript click: {click_error}")
                        # Fallback to JavaScript click
                        self.driver.execute_script("arguments[0].click();", load_more_button)
                        print(f"Used JavaScript click for load more button on page {page_count + 2}")

                    # Wait for new content to load (increased to 5 seconds as requested)
                    time.sleep(5)

                    # Verify that new content loaded by checking if there are more articles
                    current_page_source = self.driver.page_source
                    current_articles_count = len(self.extract_articles_from_html(current_page_source))

                    if current_articles_count <= len(all_articles):
                        print(f"No new articles loaded after clicking button (still {current_articles_count} total articles). Stopping.")
                        break

                    print(f"Articles count increased to {current_articles_count}")
                    page_count += 1

                except TimeoutException:
                    print("No more 'load more' button found. Stopping.")
                    break
                except Exception as e:
                    print(f"Error clicking load more button: {e}")
                    break

        finally:
            # Always cleanup the driver
            self.teardown_driver()

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

        fieldnames = ['title', 'author', 'date', 'image_url', 'url']

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(articles)


def scrape_mongabay_articles(query="tambang nikel", formats="", max_pages=None,
                           output='mongabay_articles', output_format='both', headless=True):
    """
    Scrape Mongabay.co.id articles.

    Parameters:
    - query (str): Search query, default 'tambang nikel'
    - formats (str): Formats parameter, default ''
    - max_pages (int): Maximum number of pages to load, default None (load all)
    - output (str): Output filename (without extension), default 'mongabay_articles'
    - output_format (str): Output format ('json', 'csv', or 'both'), default 'both'
    - headless (bool): Run browser in headless mode, default True

    Returns:
    - list: List of scraped articles
    """
    if output_format not in ['json', 'csv', 'both']:
        raise ValueError("output_format must be 'json', 'csv', or 'both'")

    scraper = MongabayScraper(headless=headless)
    articles = scraper.scrape_articles(query, formats, max_pages)

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
    parser = argparse.ArgumentParser(description='Scrape Mongabay.co.id articles')
    parser.add_argument('--query', '-q', default='tambang nikel', help='Search query (default: tambang nikel)')
    parser.add_argument('--formats', '-f', default='', help='Formats parameter')
    parser.add_argument('--max-pages', '-m', type=int, help='Maximum number of pages to load')
    parser.add_argument('--output', '-o', default='mongabay_articles', help='Output filename (without extension)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                       help='Output format')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                       help='Run browser in visible mode')

    args = parser.parse_args()

    scrape_mongabay_articles(
        query=args.query,
        formats=args.formats,
        max_pages=args.max_pages,
        output=args.output,
        output_format=args.format,
        headless=args.headless
    )


if __name__ == "__main__":
    main()
