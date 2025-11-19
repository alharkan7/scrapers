#!/usr/bin/env python3
"""
Web scraper for Project Multatuli search results.
Scrapes articles about nickel mining from https://projectmultatuli.org/search/tambang+nikel

Features:
- Extracts title, excerpt, author, date, image URL, and article URL
- Handles dynamic loading with "Muat Lebih" (Load More) button
- Automatically clicks load more button until all content is loaded
- Then scrapes all content in one go
- Robust error handling for button detection and content loading
- Saves results to JSON and/or CSV format
- Debug mode available to save HTML when issues occur

Usage:
python3 multatuli_scraper_v2.py --query "tambang nikel" --max-pages 5 --format both
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


class MultatuliScraperV2:
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
        """Setup Selenium WebDriver with anti-detection measures."""
        if self.driver is None:
            options = webdriver.ChromeOptions()
            
            # Anti-detection: Don't use headless (Cloudflare detects it easily)
            # if self.headless:
            #     options.add_argument('--headless')
            
            # Better anti-detection options
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            
            # Use a realistic user agent
            options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
            
            # Disable automation flags
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            try:
                # Let Selenium find chromedriver automatically
                self.driver = webdriver.Chrome(options=options)
                
                # Remove webdriver property to avoid detection
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Set page load strategy
                self.driver.set_page_load_timeout(60)
                
                print("✓ Chrome driver setup successfully!")
            except Exception as e:
                print(f"✗ Error setting up Chrome driver: {e}")
                print("Make sure Chrome and ChromeDriver are installed.")
                raise

    def teardown_driver(self):
        """Close Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def get_search_page_content(self, query="tambang+nikel"):
        """Fetch the initial search page content."""
        # URL structure for projectmultatuli.org search
        url = f"{self.base_url}/search/{query.replace(' ', '+')}"
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

    def extract_articles_from_html(self, html_content):
        """Extract articles from HTML content using a more reliable approach."""
        soup = BeautifulSoup(html_content, 'lxml')
        articles = []

        print(f"Debug: HTML content length: {len(html_content)}")

        # Find all article title links (a.judul containing h4) - these are the most reliable indicators
        title_links = soup.find_all('a', class_='judul')
        print(f"Debug: Found {len(title_links)} title links with class 'judul'")

        # Alternative approach: find all h4 elements that are likely article titles
        all_h4 = soup.find_all('h4')
        print(f"Debug: Found {len(all_h4)} total h4 elements")

        # Check for excerpt elements
        kutipan_elements = soup.find_all('p', class_='kutipan')
        print(f"Debug: Found {len(kutipan_elements)} excerpt elements with class 'kutipan'")

        # Check for author containers
        penulis_containers = soup.find_all('div', class_='penulis')
        print(f"Debug: Found {len(penulis_containers)} author containers with class 'penulis'")
        
        # Debug: Check what's inside the first author container
        if penulis_containers:
            first_author = penulis_containers[0]
            print(f"Debug: First author container HTML: {first_author.prettify()[:500]}")

        # Method 1: Extract from title links with improved container detection
        print("\n=== Method 1: Extracting from title links ===")

        # First, let's collect all the data elements separately
        all_images = soup.find_all('img', class_='foto') or soup.find_all('img')
        all_excerpts = soup.find_all('p', class_='kutipan')
        all_author_containers = soup.find_all('div', class_='penulis')

        print(f"Found {len(all_images)} images, {len(all_excerpts)} excerpts, {len(all_author_containers)} author containers")

        for i, title_link in enumerate(title_links):
            try:
                article = {}

                # Get URL and title
                article['url'] = title_link.get('href')
                h4_elem = title_link.find('h4')
                if h4_elem:
                    article['title'] = h4_elem.get_text(strip=True)

                # Instead of finding a parent container, let's try to find the corresponding elements
                # by looking for elements that appear after this title link in the DOM

                # Find the next image after this title link
                current_elem = title_link
                found_image = False
                while current_elem and not found_image:
                    current_elem = current_elem.find_next('img')
                    if current_elem:
                        src = current_elem.get('src')
                        if src and ('foto' in current_elem.get('class', []) or 'wp-image' in str(current_elem.get('class', '')) or True):  # Accept any image for now
                            article['image_url'] = src
                            found_image = True
                            break

                # Find the next excerpt after this title link
                current_elem = title_link
                found_excerpt = False
                while current_elem and not found_excerpt:
                    current_elem = current_elem.find_next('p', class_='kutipan')
                    if current_elem:
                        article['excerpt'] = current_elem.get_text(strip=True)
                        found_excerpt = True
                        break

                # Find the next author container after this title link
                current_elem = title_link
                found_author = False
                while current_elem and not found_author:
                    current_elem = current_elem.find_next('div', class_='penulis')
                    if current_elem:
                        author_link = current_elem.find('a')
                        if author_link:
                            article['author'] = author_link.get_text(strip=True)

                        # Try multiple date selectors
                        date_elem = (current_elem.find('span', class_='tgl') or
                                   current_elem.find('span', class_='date') or
                                   current_elem.find('time') or
                                   current_elem.find('span', class_=lambda x: x and 'date' in x.lower()))
                        if date_elem:
                            article['date'] = date_elem.get_text(strip=True)

                        found_author = True
                        break

                if article.get('title') and article.get('url'):
                    articles.append(article)
                    print(f"Article {i+1}: {article.get('title', 'No title')[:50]}...")
                    print(f"  Image: {article.get('image_url', 'N/A') is not None}")
                    print(f"  Excerpt: {len(article.get('excerpt', '')) > 0}")
                    print(f"  Author: {article.get('author', 'N/A')}")
                    print(f"  Date: {article.get('date', 'N/A')}")
                else:
                    print(f"Article {i+1}: Incomplete data, skipping")

            except Exception as e:
                print(f"Error extracting article {i+1}: {e}")
                continue

        # Method 2: If we didn't get enough articles, try extracting from kutipan elements
        if len(articles) < len(kutipan_elements):
            print(f"\n=== Method 2: Extracting from {len(kutipan_elements)} kutipan elements ===")

            for i, kutipan in enumerate(kutipan_elements):
                try:
                    # Check if this kutipan is already associated with an article we found
                    container = kutipan.find_parent('div', class_=lambda x: x and 'elementor-widget-wrap' in x)
                    if not container:
                        container = kutipan.find_parent('div', class_=lambda x: x and ('elementor' in x or 'post' in x))

                    if container:
                        # Check if we already have an article from this container
                        container_text = container.get_text(strip=True)[:100]
                        already_have = any(
                            container_text in str(existing_article.get('title', '')) + str(existing_article.get('excerpt', ''))
                            for existing_article in articles
                        )

                        if not already_have:
                            article = {}

                            # Extract excerpt
                            article['excerpt'] = kutipan.get_text(strip=True)

                            # Extract title from container
                            title_link = container.find('a', class_='judul')
                            if title_link:
                                article['url'] = title_link.get('href')
                                h4_elem = title_link.find('h4')
                                if h4_elem:
                                    article['title'] = h4_elem.get_text(strip=True)

                            # Extract image URL
                            img_elem = container.find('img', class_='foto') or container.find('img')
                            if img_elem and img_elem.get('src'):
                                article['image_url'] = img_elem['src']

                            # Extract author and date
                            author_container = container.find('div', class_='penulis')
                            if author_container:
                                author_link = author_container.find('a')
                                if author_link:
                                    article['author'] = author_link.get_text(strip=True)

                                # Try multiple date selectors
                                date_elem = (author_container.find('span', class_='tgl') or
                                           author_container.find('span', class_='date') or
                                           author_container.find('time') or
                                           author_container.find('span', class_=lambda x: x and 'date' in x.lower()))
                                if date_elem:
                                    article['date'] = date_elem.get_text(strip=True)

                            if article.get('title') or article.get('excerpt'):
                                articles.append(article)
                                print(f"Additional article {len(articles)}: {article.get('title', 'No title')[:50]}...")

                except Exception as e:
                    print(f"Error extracting from kutipan {i+1}: {e}")
                    continue

        print(f"\nTotal articles extracted: {len(articles)}")

        # Debug: Show sample of extracted data
        for i, article in enumerate(articles[:3]):
            print(f"Sample Article {i+1}:")
            print(f"  Title: {article.get('title', 'N/A')[:60]}...")
            print(f"  Excerpt: {article.get('excerpt', 'N/A')[:60]}...")
            print(f"  Author: {article.get('author', 'N/A')}")
            print(f"  Date: {article.get('date', 'N/A')}")
            print(f"  URL: {article.get('url', 'N/A')}")
            print("---")

        return articles

    def load_all_content(self, query="tambang nikel", max_pages=None):
        """Load all content by clicking load more until no more content is available."""
        print(f"Loading all content for query: '{query}'")
        start_time = time.time()

        # Setup Selenium driver
        self.setup_driver()

        try:
            # Navigate to the search page
            url = f"{self.base_url}/search/{query.replace(' ', '+')}"
            print(f"Loading page: {url}")
            self.driver.get(url)

            # Wait for Cloudflare challenge to complete
            print("Waiting for page to load (checking for Cloudflare)...", end="", flush=True)
            time.sleep(5)  # Initial wait for Cloudflare challenge
            
            # Check if we're on a Cloudflare challenge page
            page_source = self.driver.page_source
            if "Verify you are human" in page_source or "Just a moment" in page_source:
                print("\n⚠ Cloudflare challenge detected! Waiting up to 30 seconds...")
                
                # Wait for challenge to complete (look for actual content to appear)
                try:
                    WebDriverWait(self.driver, 30).until(
                        lambda driver: "Verify you are human" not in driver.page_source and 
                                     "Just a moment" not in driver.page_source
                    )
                    print("✓ Cloudflare challenge passed!")
                    time.sleep(3)  # Extra wait for content to load
                except TimeoutException:
                    print("✗ Cloudflare challenge timeout. Content may not load properly.")
            else:
                print(" No Cloudflare detected.")

            # Wait for initial articles to load
            print("Waiting for article content to load...", end="", flush=True)
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda driver: len(driver.find_elements(By.TAG_NAME, "h4")) > 1 or
                                   len(driver.find_elements(By.CSS_SELECTOR, "a.judul")) > 0
                )
                h4_count = len(self.driver.find_elements(By.TAG_NAME, "h4"))
                judul_count = len(self.driver.find_elements(By.CSS_SELECTOR, "a.judul"))
                print(f" ✓ Content loaded! (H4: {h4_count}, Article links: {judul_count})")
            except TimeoutException:
                print(" ✗ Timeout waiting for article content.")
                print(f"   Page title: {self.driver.title}")
                print(f"   Current URL: {self.driver.current_url}")

            page_count = 0
            max_pages = max_pages or float('inf')
            consecutive_failures = 0
            max_consecutive_failures = 3

            while page_count < max_pages and consecutive_failures < max_consecutive_failures:
                print(f"\n--- Attempting to load page {page_count + 2} ---")
                print(f"Checking for load more button on page {page_count + 1}...")

                try:
                    # Check if we've reached the maximum pages by looking at data attributes
                    try:
                        anchor_elem = self.driver.find_element(By.CSS_SELECTOR, ".e-load-more-anchor")
                        current_page = int(anchor_elem.get_attribute("data-page") or "1")
                        max_page = int(anchor_elem.get_attribute("data-max-page") or "1")
                        print(f" Page info: current={current_page}, max={max_page}")
                        
                        if current_page >= max_page:
                            print(" ✓ Reached maximum pages. All content loaded.")
                            break
                    except Exception as e:
                        print(f" Could not get page info from anchor element: {e}")

                    # Check if load more button exists and is visible
                    load_more_button = None

                    # More specific selectors based on actual DOM structure
                    selectors = [
                        ("css", ".e-loop__load-more a.elementor-button-link"),
                        ("css", "a.elementor-button-link.elementor-button"),
                        ("xpath", "//div[contains(@class, 'e-loop__load-more')]//a[contains(@class, 'elementor-button')]"),
                        ("xpath", "//span[text()='Muat Lebih']/parent::a"),
                        ("xpath", "//a[contains(@class, 'elementor-button') and .//span[text()='Muat Lebih']]")
                    ]

                    print(f" Trying {len(selectors)} different selectors to find load more button...")
                    for i, (selector_type, selector) in enumerate(selectors, 1):
                        try:
                            print(f"   {i}. Trying {selector_type}: {selector}")
                            if selector_type == "css":
                                load_more_button = WebDriverWait(self.driver, 3).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                )
                            else:  # xpath
                                load_more_button = WebDriverWait(self.driver, 3).until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                )
                            
                            # Verify the button is actually the load more button
                            if load_more_button:
                                button_text = ""
                                try:
                                    button_text = load_more_button.text.strip()
                                    if not button_text:
                                        span_elem = load_more_button.find_element(By.CLASS_NAME, "elementor-button-text")
                                        button_text = span_elem.text.strip()
                                except:
                                    pass
                                
                                if "muat lebih" in button_text.lower():
                                    print(f"   ✓ Found valid load more button with selector #{i}!")
                                    print(f"   Button text: '{button_text}'")
                                    break
                                else:
                                    print(f"   ✗ Button found but text '{button_text}' is not valid")
                                    load_more_button = None
                        except Exception as e:
                            print(f"   ✗ Selector #{i} failed: {e}")
                            continue

                    if not load_more_button:
                        print(" ✗ No load more button found. All content should be loaded.")
                        break

                    # Validate button text and ensure it's clickable
                    button_text = ""
                    try:
                        # Try multiple ways to get the button text
                        button_text = load_more_button.text.strip()
                        if not button_text:
                            text_span = load_more_button.find_element(By.CLASS_NAME, "elementor-button-text")
                            button_text = text_span.text.strip()
                        if not button_text:
                            button_text = self.driver.execute_script("return arguments[0].textContent || arguments[0].innerText;", load_more_button).strip()
                    except Exception as e:
                        print(f" Warning: Could not get button text: {e}")

                    if not button_text or "muat lebih" not in button_text.lower():
                        print(f" ✗ Button text '{button_text}' is not valid. Stopping.")
                        break

                    print(f" ✓ Valid button text found: '{button_text}'")

                    # Check button visibility and position
                    try:
                        is_displayed = load_more_button.is_displayed()
                        is_enabled = load_more_button.is_enabled()
                        location = load_more_button.location
                        size = load_more_button.size
                        print(f" Button status: displayed={is_displayed}, enabled={is_enabled}")
                        print(f" Button position: x={location['x']}, y={location['y']}, width={size['width']}, height={size['height']}")
                    except Exception as e:
                        print(f" Could not get button status: {e}")

                    # Ensure button is visible and clickable
                    try:
                        # Wait for button to be clickable
                        WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(load_more_button)
                        )
                        print(" ✓ Button is clickable!")
                    except TimeoutException:
                        print(" ⚠ Button is not clickable within timeout. Trying to make it visible...")
                        
                        # Scroll to the button
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", load_more_button)
                        time.sleep(2)
                        
                        # Try again
                        try:
                            WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable(load_more_button)
                            )
                            print(" ✓ Button is now clickable after scrolling!")
                        except TimeoutException:
                            print(" ✗ Button still not clickable. Skipping this attempt.")
                            consecutive_failures += 1
                            continue

                    # Count articles before clicking
                    articles_before = len(self.driver.find_elements(By.TAG_NAME, "h4"))
                    print(f" Articles before click: {articles_before}")

                    # Click the load more button
                    click_success = False
                    try:
                        # Try regular click first
                        load_more_button.click()
                        print(f" ✓ Successfully clicked load more button (regular click)")
                        click_success = True
                    except Exception as click_error:
                        print(f" ✗ Regular click failed: {click_error}")
                        try:
                            # Try JavaScript click as fallback
                            self.driver.execute_script("arguments[0].click();", load_more_button)
                            print(f" ✓ Successfully clicked load more button (JavaScript click)")
                            click_success = True
                        except Exception as js_error:
                            print(f" ✗ JavaScript click also failed: {js_error}")
                            consecutive_failures += 1
                            continue

                    if not click_success:
                        print(" ✗ All click methods failed")
                        consecutive_failures += 1
                        continue

                    # Wait for loading to complete
                    print(" Waiting for loading to complete...", end="", flush=True)

                    try:
                        # Wait for new content to load by checking if page number increases
                        initial_page = page_count + 1
                        
                        # Wait for loading spinner to appear (optional)
                        try:
                            WebDriverWait(self.driver, 3).until(
                                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".e-load-more-spinner .eicon-animation-spin")) > 0
                            )
                            print(" Loading started...", end="", flush=True)
                        except TimeoutException:
                            print(" No loading spinner detected...", end="", flush=True)

                        # Wait for loading to complete - either spinner disappears or content changes
                        loading_complete = False
                        wait_attempts = 0
                        max_wait_attempts = 15  # Increased timeout
                        
                        while not loading_complete and wait_attempts < max_wait_attempts:
                            time.sleep(1)
                            wait_attempts += 1
                            
                            # Check if spinner disappeared
                            spinners = self.driver.find_elements(By.CSS_SELECTOR, ".e-load-more-spinner .eicon-animation-spin")
                            if len(spinners) == 0:
                                loading_complete = True
                                print(" ✓ Loading completed (spinner gone)!", flush=True)
                                break
                            
                            # Check if page number changed
                            try:
                                anchor_elem = self.driver.find_element(By.CSS_SELECTOR, ".e-load-more-anchor")
                                current_page = int(anchor_elem.get_attribute("data-page") or "1")
                                if current_page > initial_page:
                                    loading_complete = True
                                    print(f" ✓ Loading completed (page changed to {current_page})!", flush=True)
                                    break
                            except:
                                pass
                            
                            # Check if article count increased
                            articles_now = len(self.driver.find_elements(By.TAG_NAME, "h4"))
                            if articles_now > articles_before:
                                loading_complete = True
                                print(f" ✓ Loading completed (articles increased from {articles_before} to {articles_now})!", flush=True)
                                break
                        
                        if not loading_complete:
                            print(" ⚠ Loading timeout, but continuing...", flush=True)

                        # Final article count
                        articles_after = len(self.driver.find_elements(By.TAG_NAME, "h4"))
                        print(f" Articles after loading: {articles_after} (gained: {articles_after - articles_before})")

                        consecutive_failures = 0  # Reset failure counter on success

                    except Exception as loading_error:
                        print(f" ✗ Error waiting for loading: {loading_error}", flush=True)
                        consecutive_failures += 1

                    page_count += 1

                except TimeoutException:
                    print(" ✗ Timeout looking for load more button.")
                    consecutive_failures += 1

                except Exception as e:
                    print(f" ✗ Error during load more process: {e}")
                    consecutive_failures += 1
                    
                    # Save debug HTML on error
                    try:
                        debug_html = f"debug_error_page_{page_count + 1}.html"
                        with open(debug_html, 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        print(f" Saved error page source to {debug_html} for debugging.")
                    except:
                        pass

            print(f"\n=== Content Loading Summary ===")
            print(f"✓ Successfully clicked load more {page_count} times")
            print(f"✓ Consecutive failures: {consecutive_failures}/{max_consecutive_failures}")
            
            # Final article count
            final_articles = len(self.driver.find_elements(By.TAG_NAME, "h4"))
            print(f"✓ Total articles found: {final_articles}")

        except Exception as e:
            print(f"✗ Error during content loading: {e}")
            # Save debug HTML
            try:
                debug_html = f"debug_loading_error.html"
                with open(debug_html, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f" Saved page source to {debug_html} for debugging.")
            except:
                pass

        elapsed_time = time.time() - start_time
        print(f"Content loading completed in {elapsed_time:.1f} seconds")

        return self.driver.page_source if self.driver else None

    def scrape_articles_selenium(self):
        """Extract articles directly from the browser DOM using Selenium."""
        articles = []

        # Find all title links with class 'judul' (most reliable approach)
        title_links = self.driver.find_elements(By.CSS_SELECTOR, "a.judul")

        print(f"Selenium: Found {len(title_links)} title links with class 'judul'")

        for i, title_link in enumerate(title_links):
            try:
                article = {}

                # Get URL from the link
                article['url'] = title_link.get_attribute('href')

                # Get title from h4 inside the link
                try:
                    h4_elem = title_link.find_element(By.TAG_NAME, "h4")
                    article['title'] = h4_elem.text.strip()
                except:
                    pass
                
                # Get date from tanggal attribute on the title link (primary source)
                try:
                    tanggal = title_link.get_attribute('tanggal')
                    if tanggal:
                        article['date'] = tanggal
                except:
                    pass

                # Instead of finding containers, look for the next relevant elements after this title link
                # Find the next image after this title link
                try:
                    # Use XPath to find the next img element after this title link
                    img = title_link.find_element(By.XPATH, "following::img[1]")
                    if img:
                        src = img.get_attribute('src')
                        if src:
                            article['image_url'] = src
                except:
                    pass

                # Find the next excerpt after this title link
                try:
                    excerpt_elem = title_link.find_element(By.XPATH, "following::p[contains(@class, 'kutipan')][1]")
                    if excerpt_elem:
                        article['excerpt'] = excerpt_elem.text.strip()
                except:
                    pass

                # Find the next author container after this title link
                try:
                    author_container = title_link.find_element(By.XPATH, "following::div[contains(@class, 'penulis')][1]")
                    if author_container:
                        try:
                            author_link = author_container.find_element(By.TAG_NAME, "a")
                            if author_link:
                                article['author'] = author_link.text.strip()
                        except:
                            pass

                        # Try multiple date selectors (as fallback if tanggal attribute wasn't found)
                        if not article.get('date'):
                            date_selectors = [
                                "span.tgl",
                                "span.date",
                                "time",
                                "span[class*='date' i]",
                                ".elementor-post-date",
                                "span.elementor-post-info__item--type-date"
                            ]
                            for selector in date_selectors:
                                try:
                                    date_elem = author_container.find_element(By.CSS_SELECTOR, selector)
                                    if date_elem and date_elem.text.strip():
                                        article['date'] = date_elem.text.strip()
                                        break
                                except:
                                    continue
                except:
                    pass

                # Only add if we have at least title or URL
                if article.get('title') or article.get('url'):
                    articles.append(article)
                    print(f"Selenium Article {i+1}: {article.get('title', 'No title')[:50]}...")
                    print(f"  Image: {article.get('image_url', 'N/A') is not None}")
                    print(f"  Excerpt: {len(article.get('excerpt', '')) > 0}")
                    print(f"  Author: {article.get('author', 'N/A')}")
                    print(f"  Date: {article.get('date', 'N/A')}")
                else:
                    print(f"Selenium Article {i+1}: Incomplete data, skipping")

            except Exception as e:
                print(f"Selenium Error extracting article {i+1}: {e}")
                continue

        # Fallback: If we didn't get many articles, try extracting from kutipan elements
        kutipan_elements = self.driver.find_elements(By.CSS_SELECTOR, "p.kutipan")
        if len(articles) < len(kutipan_elements):
            print(f"Selenium Fallback: Extracting from {len(kutipan_elements)} kutipan elements")

            for i, kutipan in enumerate(kutipan_elements):
                try:
                    # Find container for this kutipan
                    try:
                        container = kutipan.find_element(By.XPATH, "./ancestor::div[contains(@class, 'elementor-widget-wrap')]")
                    except:
                        try:
                            container = kutipan.find_element(By.XPATH, "./ancestor::div[contains(@class, 'elementor') or contains(@class, 'post')]")
                        except:
                            container = None

                    if container:
                        # Check if we already have this article
                        excerpt_text = kutipan.text.strip()
                        already_have = any(
                            existing.get('excerpt') == excerpt_text
                            for existing in articles
                        )

                        if not already_have:
                            article = {'excerpt': excerpt_text}

                            # Extract title and URL
                            try:
                                title_link = container.find_element(By.CSS_SELECTOR, "a.judul")
                                if title_link:
                                    article['url'] = title_link.get_attribute('href')
                                    try:
                                        h4_elem = title_link.find_element(By.TAG_NAME, "h4")
                                        article['title'] = h4_elem.text.strip()
                                    except:
                                        pass
                            except:
                                pass

                            # Extract image
                            try:
                                img = container.find_element(By.CSS_SELECTOR, "img.foto") or container.find_element(By.TAG_NAME, "img")
                                if img:
                                    article['image_url'] = img.get_attribute('src')
                            except:
                                pass

                            # Extract author and date
                            try:
                                author_container = container.find_element(By.CSS_SELECTOR, "div.penulis")
                                if author_container:
                                    try:
                                        author_link = author_container.find_element(By.TAG_NAME, "a")
                                        if author_link:
                                            article['author'] = author_link.text.strip()
                                    except:
                                        pass

                                    # Try multiple date selectors
                                    date_selectors = [
                                        "span.tgl",
                                        "span.date",
                                        "time",
                                        "span[class*='date' i]",
                                        ".elementor-post-date",
                                        "span.elementor-post-info__item--type-date"
                                    ]
                                    for selector in date_selectors:
                                        try:
                                            date_elem = author_container.find_element(By.CSS_SELECTOR, selector)
                                            if date_elem and date_elem.text.strip():
                                                article['date'] = date_elem.text.strip()
                                                break
                                        except:
                                            continue
                            except:
                                pass

                            articles.append(article)
                            print(f"Selenium Fallback Article {len(articles)}: {article.get('title', 'No title')[:50]}...")

                except Exception as e:
                    print(f"Selenium Fallback Error extracting from kutipan {i+1}: {e}")
                    continue

        print(f"Selenium: Total articles extracted: {len(articles)}")
        return articles

    def scrape_articles(self, query="tambang nikel", max_pages=None):
        """Scrape all articles after loading all content."""
        # First, load all content by clicking load more until no more content
        html_content = self.load_all_content(query, max_pages)

        if not html_content:
            print("Failed to load page content")
            return []

        # Now scrape all articles directly from the browser DOM using Selenium
        print("Scraping all articles from browser DOM...")
        all_articles = self.scrape_articles_selenium()

        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        print(f"Found {len(unique_articles)} unique articles")

        # Debug: Save the HTML content for inspection only if we still have 0 articles
        if unique_articles == 0:
            debug_filename = f"debug_final_html_{datetime.now().strftime('%H-%M-%S')}.html"
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Debug: Saved final HTML to {debug_filename} for inspection")

        # Cleanup driver
        self.teardown_driver()

        return unique_articles

    def save_to_json(self, articles, filename):
        """Save articles to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

    def save_to_csv(self, articles, filename):
        """Save articles to CSV file."""
        if not articles:
            print("No articles to save.")
            return

        fieldnames = ['title', 'excerpt', 'author', 'date', 'image_url', 'url']

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(articles)


def scrape_multatuli_articles(query="tambang nikel", max_pages=None,
                           output='multatuli_articles', output_format='both', headless=True, debug=False):
    """
    Scrape Project Multatuli articles using load-all-then-scrape approach.

    Parameters:
    - query (str): Search query, default 'tambang nikel'
    - max_pages (int): Maximum number of pages to load, default None (load all)
    - output (str): Output filename (without extension), default 'multatuli_articles'
    - output_format (str): Output format ('json', 'csv', or 'both'), default 'both'
    - headless (bool): Run browser in headless mode, default True
    - debug (bool): Enable debug mode (saves HTML when button not found), default False

    Returns:
    - list: List of scraped articles
    """
    if output_format not in ['json', 'csv', 'both']:
        raise ValueError("output_format must be 'json', 'csv', or 'both'")

    scraper = MultatuliScraperV2(headless=headless)
    articles = scraper.scrape_articles(query, max_pages)

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
    parser = argparse.ArgumentParser(description='Scrape Project Multatuli articles (load all then scrape)')
    parser.add_argument('--query', '-q', default='tambang nikel', help='Search query (default: tambang nikel)')
    parser.add_argument('--max-pages', '-m', type=int, help='Maximum number of pages to load')
    parser.add_argument('--output', '-o', default='multatuli_articles', help='Output filename (without extension)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                       help='Output format')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                       help='Run browser in visible mode')
    parser.add_argument('--debug', action='store_true', default=False,
                       help='Enable debug mode (saves HTML when button not found)')

    args = parser.parse_args()

    scrape_multatuli_articles(
        query=args.query,
        max_pages=args.max_pages,
        output=args.output,
        output_format=args.format,
        headless=args.headless,
        debug=args.debug
    )


if __name__ == "__main__":
    main()
