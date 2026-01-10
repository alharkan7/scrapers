# -*- coding: utf-8 -*-
"""
Turn Back Hoax Scraper

A comprehensive scraper for turnbackhoax.id that can:
1. Scrape headlines from multiple pages
2. Scrape full article content
3. Process and clean scraped data

Original Jupyter notebook: turnbackhoax/Scraping_Turn_Back_Hoax.ipynb
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm
import re
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from datetime import datetime


# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Page range for scraping headlines
START_PAGE = 13
END_PAGE = 663

# Google Sheet configuration for article scraping
SHEET_ID = "1hX-iWkJslmBHTMvYE-0fLs9I46vvm_Er3sfrn9pBMms"
SHEET_NAME = "0"  # gid from the URL

# Headers to mimic browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ============================================================================
# STEP 1: SCRAPING HEADLINES (SELENIUM-BASED)
# ============================================================================

# Month names for date range parameter
MONTHS = [
#    "January", 
#    "February", 
    "March",
    "April", 
    "May", 
    "June",
    "July", 
    "August", 
    "September", 
#    "October",
#    "November", 
    "December"
]

YEAR_START = 2025
YEAR_END = 2025

def get_date_ranges(start_year=YEAR_START, end_year=YEAR_END, start_month=1, end_month=None):
    """
    Generate list of date ranges (Month+Year) for scraping.
    Only generates ranges for months that exist in the MONTHS list.
    
    Args:
        start_year: Starting year
        end_year: Ending year
        start_month: Starting month (1-12)
        end_month: Ending month (1-12, default: 12)
        
    Returns:
        List of date range strings like ["January+2025", "February+2025", ...]
    """
    if end_year is None:
        end_year = datetime.now().year
    if end_month is None:
        end_month = 12
    
    date_ranges = []
    
    # Generate in ascending chronological order (oldest first)
    # Only include months that exist in the MONTHS list
    for year in range(start_year, end_year + 1):
        month_start = start_month if year == start_year else 1
        month_end = end_month if year == end_year else 12
        
        for month in range(month_start, month_end + 1):
            # Check if this month exists in the MONTHS list
            month_name = get_month_name(month)
            if month_name and month_name in MONTHS:
                date_ranges.append(f"{month_name}+{year}")
    
    return date_ranges


def get_month_name(month_num):
    """Get month name from month number (1-12)."""
    all_months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    if 1 <= month_num <= 12:
        return all_months[month_num - 1]
    return None


def setup_selenium_driver(headless=True):
    """
    Set up and return a Selenium Chrome WebDriver.
    
    Args:
        headless: Whether to run browser in headless mode
        
    Returns:
        WebDriver instance
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver


def parse_articles_from_page(driver):
    """
    Parse article data from the current page loaded in the driver.
    
    Args:
        driver: Selenium WebDriver with page loaded
        
    Returns:
        List of dictionaries containing article data
    """
    articles_data = []
    
    # Wait for articles to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.news-card-h-alt"))
        )
    except TimeoutException:
        print("Warning: Timeout waiting for articles to load")
        return articles_data
    
    # Get page source and parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    articles = soup.find_all('div', class_='news-card-h-alt')
    
    for article in articles:
        article_data = {
            'title': '',
            'url': '',
            'preview': '',
            'image_url': '',
            'date': '',
            'category': ''
        }
        
        # Extract title and URL
        title_element = article.find('h2')
        link_element = article.find('a', href=True)
        
        if title_element:
            title_span = title_element.find('span', class_='hidden')
            if title_span:
                article_data['title'] = title_span.text.strip()
            else:
                article_data['title'] = title_element.text.strip()
        
        if link_element:
            href = link_element['href']
            # Make sure URL is absolute
            if not href.startswith('http'):
                href = f"https://turnbackhoax.id{href}"
            article_data['url'] = href

        # Extract preview text
        preview_element = article.find('p')
        if preview_element:
            preview_span = preview_element.find('span', class_='hidden')
            if preview_span:
                article_data['preview'] = preview_span.text.strip()
            else:
                article_data['preview'] = preview_element.text.strip()

        # Extract image URL
        image_element = article.find('img')
        if image_element and image_element.get('src'):
            article_data['image_url'] = image_element['src']

        # Extract date
        date_span = article.find('span', class_='text-light-black')
        if date_span:
            article_data['date'] = date_span.text.strip()

        # Extract category
        category_link = article.find('a', href=lambda x: x and 'category=' in str(x))
        if category_link:
            article_data['category'] = category_link.text.strip()
        
        articles_data.append(article_data)
    
    return articles_data


def get_total_pages(driver):
    """
    Get the total number of pages for the current date range.
    
    Args:
        driver: Selenium WebDriver with page loaded
        
    Returns:
        Total number of pages (int)
    """
    try:
        # Look for the 'last' pagination button which has the total page count
        last_button = driver.find_element(By.CSS_SELECTOR, "button.nav-item.sprites-last")
        total_pages = int(last_button.get_attribute("data-page"))
        return total_pages
    except (NoSuchElementException, ValueError):
        # Try to find from total-pages data attribute
        try:
            pagination_nav = driver.find_element(By.CSS_SELECTOR, "[data-total-pages]")
            return int(pagination_nav.get_attribute("data-total-pages"))
        except:
            return 1


def is_next_button_active(driver):
    """
    Check if the 'next' pagination button is active (not disabled).
    
    Args:
        driver: Selenium WebDriver
        
    Returns:
        True if next button is active, False if disabled or not found
    """
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "button.nav-item.sprites-next")
        # Check if button has 'disabled' attribute or 'disabled' class
        is_disabled = next_button.get_attribute("disabled") is not None
        has_disabled_class = "disabled" in next_button.get_attribute("class")
        return not (is_disabled or has_disabled_class)
    except NoSuchElementException:
        return False


def click_next_button(driver, max_wait=10, max_retries=3):
    """
    Click the 'next' pagination button to go to the next page.
    Waits for the content to actually change after clicking.
    Retries if the content doesn't change.
    
    Args:
        driver: Selenium WebDriver
        max_wait: Maximum seconds to wait for content to change per attempt
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if successfully clicked and content changed, False otherwise
    """
    for attempt in range(max_retries):
        try:
            # First check if the next button is active
            if not is_next_button_active(driver):
                return False
            
            # Get the first article URL before clicking (to detect change)
            try:
                first_article_before = driver.find_element(By.CSS_SELECTOR, "div.news-card-h-alt a")
                first_url_before = first_article_before.get_attribute("href")
            except NoSuchElementException:
                first_url_before = None
            
            # Also get the current page number before clicking
            try:
                current_page_before = get_current_page(driver)
            except:
                current_page_before = 0
            
            # Find and click the next button
            next_button = driver.find_element(By.CSS_SELECTOR, "button.nav-item.sprites-next:not(.disabled)")
            
            # Scroll button into view if needed
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(0.3)
            
            # Click using JavaScript to avoid interception issues
            driver.execute_script("arguments[0].click();", next_button)
            
            # Wait for content to change (poll until first article URL changes or page number changes)
            start_time = time.time()
            content_changed = False
            
            while time.time() - start_time < max_wait:
                time.sleep(0.5)
                
                # Check if page number changed
                try:
                    current_page_after = get_current_page(driver)
                    if current_page_after > current_page_before:
                        content_changed = True
                        break
                except:
                    pass
                
                # Check if first article URL changed
                try:
                    first_article_after = driver.find_element(By.CSS_SELECTOR, "div.news-card-h-alt a")
                    first_url_after = first_article_after.get_attribute("href")
                    if first_url_after != first_url_before:
                        content_changed = True
                        break
                except NoSuchElementException:
                    pass
            
            if content_changed:
                # Additional small delay to ensure all AJAX content is loaded
                time.sleep(1)
                return True
            
            # Content didn't change, retry
            if attempt < max_retries - 1:
                print(f"Retry {attempt + 1}/{max_retries}: Content did not change, retrying...")
                time.sleep(2)  # Wait before retry
            
        except NoSuchElementException:
            return False
        except Exception as e:
            print(f"Error clicking next button: {e}")
            if attempt >= max_retries - 1:
                return False
    
    print(f"Warning: Content did not change after {max_retries} attempts")
    return False


def get_current_page(driver):
    """
    Get the current page number from pagination.
    
    Args:
        driver: Selenium WebDriver
        
    Returns:
        Current page number (int)
    """
    try:
        current_button = driver.find_element(By.CSS_SELECTOR, "button.nav-item.current")
        return int(current_button.get_attribute("data-page"))
    except:
        return 1


def select_date_from_dropdown(driver, date_range):
    """
    Manually select a date from the archive dropdown.
    The website ignores the dateRange URL parameter, so we need to click the dropdown.
    
    Args:
        driver: Selenium WebDriver
        date_range: Date string like "January+2025" or "January 2025"
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert format for display (e.g., "January+2025" -> "January 2025")
        date_display = date_range.replace('+', ' ')
        
        # Click the dropdown button to open it
        dropdown_btn = driver.find_element(By.CSS_SELECTOR, ".custom-selector__btn")
        driver.execute_script("arguments[0].click();", dropdown_btn)
        time.sleep(0.5)
        
        # Find and click the date option in the dropdown
        # First try exact match, then try partial match
        try:
            # Try clicking by href containing the date
            date_link = driver.find_element(
                By.CSS_SELECTOR, 
                f'a.dropdown-item[href*="{date_range}"]'
            )
            driver.execute_script("arguments[0].click();", date_link)
        except NoSuchElementException:
            # Try finding by text content
            dropdown_items = driver.find_elements(By.CSS_SELECTOR, "a.dropdown-item")
            date_found = False
            for item in dropdown_items:
                if date_display in item.text:
                    driver.execute_script("arguments[0].click();", item)
                    date_found = True
                    break
            
            if not date_found:
                print(f"Warning: Could not find date option '{date_display}' in dropdown")
                return False
        
        # Wait for content to load after selection
        time.sleep(2)
        
        # Wait for articles to appear
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.news-card-h-alt"))
            )
        except TimeoutException:
            print(f"Warning: No articles loaded after selecting {date_display}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error selecting date from dropdown: {e}")
        return False


def scrape_headlines_by_date(date_range, driver, start_page=1, end_page=None, output_file=None, existing_urls=None):
    """
    Scrape headlines for a specific date range (Month+Year).
    Uses the 'next' button to navigate between pages.
    Skips articles that have already been scraped (by URL).
    
    Args:
        date_range: Date range string like "January+2025"
        driver: Selenium WebDriver instance
        start_page: Starting page number (default: 1)
        end_page: Ending page number (None = all pages)
        output_file: Output CSV file path
        existing_urls: Set of URLs already scraped (to skip duplicates)
        
    Returns:
        Tuple of (list of new article dictionaries, count of skipped duplicates)
    """
    if existing_urls is None:
        existing_urls = set()
    # First load the main articles page
    url = "https://turnbackhoax.id/articles?category=all"
    
    print(f"\n{'='*60}")
    print(f"Scraping: {date_range.replace('+', ' ')}")
    print(f"{'='*60}")
    
    driver.get(url)
    time.sleep(2)  # Wait for initial load
    
    # Wait for page to be ready
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".custom-selector__btn"))
        )
    except TimeoutException:
        print(f"Warning: Page did not load properly")
        return [], 0
    
    # Manually select the date from the dropdown (URL parameter is ignored by the website)
    print(f"Selecting date from dropdown: {date_range.replace('+', ' ')}")
    if not select_date_from_dropdown(driver, date_range):
        print(f"Warning: Could not select date {date_range.replace('+', ' ')}")
        return [], 0
    
    # Wait for articles to be present after date selection
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.news-card-h-alt"))
        )
    except TimeoutException:
        print(f"Warning: No articles found for {date_range.replace('+', ' ')}")
        return [], 0
    
    # Get total pages for this date range
    total_pages = get_total_pages(driver)
    if end_page is None or end_page > total_pages:
        end_page = total_pages
    
    print(f"Total pages for {date_range.replace('+', ' ')}: {total_pages}")
    print(f"Scraping pages {start_page} to {end_page}")
    
    all_articles = []
    current_page = 1
    
    # If start_page is greater than 1, we need to click next until we reach it
    if start_page > 1:
        print(f"Navigating to start page {start_page}...")
        for _ in range(start_page - 1):
            if not click_next_button(driver):
                print(f"Warning: Could not navigate to page {start_page}")
                return all_articles, 0  # Return what we have so far
            current_page += 1
    
    # Create progress bar for pages to scrape
    pages_to_scrape = end_page - start_page + 1
    pbar = tqdm(total=pages_to_scrape, desc=f"Pages ({date_range.replace('+', ' ')})")
    
    total_skipped = 0
    
    while current_page <= end_page:
        pbar.set_description(f"Page {current_page}/{end_page}")
        
        # Parse articles from current page
        articles = parse_articles_from_page(driver)
        
        if not articles:
            print(f"Warning: No articles found on page {current_page}")
        
        # Filter out articles that already exist (by URL)
        new_articles = []
        for article in articles:
            if article['url'] not in existing_urls:
                article['page_number'] = current_page
                article['date_range'] = date_range.replace('+', ' ')
                new_articles.append(article)
            else:
                total_skipped += 1
        
        # Write only new articles to CSV immediately
        if new_articles and output_file:
            df = pd.DataFrame(new_articles)
            df.to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8')
        
        all_articles.extend(new_articles)
        pbar.set_postfix({'new': len(all_articles), 'skipped': total_skipped})
        pbar.update(1)
        
        # If we've reached the end page, stop
        if current_page >= end_page:
            break
        
        # Try to click next button
        if not click_next_button(driver):
            print(f"\nReached end of pagination at page {current_page}")
            break
        
        current_page += 1
        
        # Additional delay to ensure content is fully loaded
        time.sleep(1)
    
    pbar.close()
    return all_articles, total_skipped


def scrape_all_headlines(date_ranges=None, start_page=1, end_page=None, output_file=None, headless=True):
    """
    Scrape headlines from multiple date ranges using Selenium.
    
    Args:
        date_ranges: List of date range strings (e.g., ["January+2025", "December+2024"])
                    If None, scrapes current month only
        start_page: Starting page for each date range
        end_page: Ending page for each date range (None = all pages)
        output_file: Output CSV file path
        headless: Whether to run browser in headless mode
        
    Returns:
        DataFrame with all scraped data
    """
    # Default to current month if no date ranges specified
    if date_ranges is None:
        current_month = MONTHS[datetime.now().month - 1]
        current_year = datetime.now().year
        date_ranges = [f"{current_month}+{current_year}"]
    
    # Determine output filename
    if output_file is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f'turnbackhoax_headlines_{timestamp}.csv'
    
    # Check for existing data - use URL for deduplication (most robust)
    existing_urls = set()
    file_exists = False
    if pd.io.common.file_exists(output_file):
        try:
            existing_df = pd.read_csv(output_file, encoding='utf-8')
            if 'url' in existing_df.columns:
                existing_urls = set(existing_df['url'].dropna().unique())
                print(f"Found existing file: {output_file}")
                print(f"Already scraped: {len(existing_urls)} unique articles")
                file_exists = True
        except Exception as e:
            print(f"Warning: Could not read existing file: {e}")
    
    # Create CSV with headers if it doesn't exist
    if not file_exists:
        empty_df = pd.DataFrame(columns=['title', 'url', 'preview', 'image_url', 'date', 'category', 'page_number', 'date_range'])
        empty_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Created new output file: {output_file}")
    
    # Setup Selenium driver
    print("\nStarting browser...")
    driver = setup_selenium_driver(headless=headless)
    
    try:
        total_articles = 0
        total_skipped = 0
        date_ranges_scraped = 0
        
        for date_range in date_ranges:
            date_range_display = date_range.replace('+', ' ')
            
            # Check if browser session is still valid, recreate if needed
            try:
                driver.current_url  # This will throw if session is invalid
            except Exception:
                print("Browser session lost, restarting...")
                try:
                    driver.quit()
                except:
                    pass
                driver = setup_selenium_driver(headless=headless)
            
            # Scrape this date range (will skip already scraped URLs)
            articles, skipped = scrape_headlines_by_date(
                date_range=date_range,
                driver=driver,
                start_page=start_page,
                end_page=end_page,
                output_file=output_file,
                existing_urls=existing_urls
            )
            
            total_skipped += skipped
            
            if articles:
                # Articles are already written to CSV per page in scrape_headlines_by_date
                # Add newly scraped URLs to existing set for next iterations
                for article in articles:
                    existing_urls.add(article['url'])
                total_articles += len(articles)
                date_ranges_scraped += 1
                print(f"Saved {len(articles)} new articles from {date_range_display} (skipped {skipped} duplicates)")
        
        print(f"\n{'='*70}")
        print(f"Scraping completed!")
        print(f"Date ranges processed: {date_ranges_scraped}")
        print(f"Total articles scraped: {total_articles}")
        print(f"Data saved to: {output_file}")
        print(f"{'='*70}")
        
        # Return the complete DataFrame
        try:
            final_df = pd.read_csv(output_file, encoding='utf-8')
            return final_df
        except Exception as e:
            print(f"Warning: Could not read final CSV: {e}")
            return None
            
    finally:
        driver.quit()
        print("Browser closed.")


# Legacy function for backwards compatibility (deprecated)
def scrape_turnbackhoax_page(page_number):
    """
    DEPRECATED: This function uses requests which doesn't work with the current website.
    Use scrape_all_headlines() with Selenium instead.
    """
    print("WARNING: scrape_turnbackhoax_page is deprecated. Use scrape_all_headlines() instead.")
    return None


# Legacy function for backwards compatibility (deprecated)
def scrape_all_pages(start_page=None, end_page=None, output_file=None):
    """
    DEPRECATED: This function uses requests which doesn't work with the current website.
    Use scrape_all_headlines() with Selenium instead.
    """
    print("WARNING: scrape_all_pages is deprecated. Use scrape_all_headlines() instead.")
    print("Converting to new Selenium-based scraping...")
    
    return scrape_all_headlines(
        date_ranges=None,  # Will use current month
        start_page=start_page or 1,
        end_page=end_page,
        output_file=output_file,
        headless=True
    )


# ============================================================================
# STEP 2: SCRAPING FULL CONTENT
# ============================================================================

def normalize_unicode_characters(text):
    """
    Normalize unicode characters to their ASCII equivalents
    
    Args:
        text: Input text with potential unicode characters
        
    Returns:
        Text with normalized characters
    """
    if not isinstance(text, str):
        return text
    
    # Replace smart quotes with regular quotes
    replacements = {
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash
        '\u2026': '...',  # Horizontal ellipsis
        '\u00a0': ' ',  # Non-breaking space
        '\u2022': '•',  # Bullet point
        '\u00ab': '<<',  # Left-pointing double angle quotation mark
        '\u00bb': '>>',  # Right-pointing double angle quotation mark
    }
    
    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)
    
    return text


def clean_html_content(html_content):
    """
    Clean HTML content and format it into readable paragraphs
    
    Args:
        html_content: BeautifulSoup element containing HTML content
        
    Returns:
        Cleaned text with proper paragraph formatting
    """
    # Remove script and style elements
    for script in html_content.find_all(['script', 'style']):
        script.decompose()

    # Get text and clean it
    text = html_content.get_text(separator=' ')

    # Normalize unicode characters
    text = normalize_unicode_characters(text)

    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)

    # Create proper paragraphs
    paragraphs = text.split('\n\n')
    cleaned_paragraphs = [p.strip() for p in paragraphs if p.strip()]

    return '\n\n'.join(cleaned_paragraphs)

def scrape_article(url):
    """
    Scrape detailed information from a turnbackhoax article
    
    Args:
        url: URL of the article to scrape
        
    Returns:
        Dictionary with comprehensive article data
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Initialize result dictionary
        result = {
            'url': url,
            'full_title': '',
            'category': '',
            'date': '',
            'media': '',
            'cover_image_url': '',
            'hasil_periksa_fakta': '',
            'kategori_berita': '',
            'sumber': '',
            'narasi': '',
            'penjelasan': '',
            'kesimpulan': '',
            'referensi': ''
        }

        # Get article tag
        article = soup.find('article')
        if not article:
            return result

        # 1. Full Title
        title_tag = soup.find('h1')
        if title_tag:
            result['full_title'] = title_tag.text.strip()

        # 2. Category, Date, Media from info div
        info_div = article.find('div', class_=lambda x: x and 'flex' in str(x))
        if info_div:
            info_texts = list(info_div.stripped_strings)
            if len(info_texts) >= 2:
                result['category'] = info_texts[1]  # Category
            if len(info_texts) >= 3:
                result['date'] = info_texts[2]  # Date
            if len(info_texts) >= 4:
                result['media'] = info_texts[3]  # Media

        # 3. Cover Image (first img in article)
        imgs = article.find_all('img')
        if imgs:
            result['cover_image_url'] = imgs[0].get('src', '')

        # 4. Hasil Periksa Fakta section
        factcheck_section = soup.find('section', class_='article-factcheck')
        if factcheck_section:
            # Get factcheck result
            result_span = factcheck_section.find('span', class_='factcheck-result')
            if result_span:
                result['hasil_periksa_fakta'] = result_span.text.strip()
            
            # Get category from factcheck
            category_span = factcheck_section.find('span', class_='factcheck-category')
            if category_span:
                kategori_text = category_span.text.strip()
                # Extract category after "Kategori Berita: "
                if 'Kategori Berita:' in kategori_text:
                    result['kategori_berita'] = kategori_text.replace('Kategori Berita:', '').strip()
            
            # Get source
            source_span = factcheck_section.find('span', class_='factcheck-source')
            if source_span:
                source_link = source_span.find('a')
                if source_link and source_link.get('href'):
                    result['sumber'] = source_link.get('href', '')

        # 5. Narasi section
        narasi_section = soup.find('section', class_='article-origin')
        if narasi_section:
            quoted_div = narasi_section.find('div', class_='quoted')
            if quoted_div:
                result['narasi'] = clean_html_content(quoted_div)

        # 6. Penjelasan section (first article-explanation)
        explanation_sections = soup.find_all('section', class_='article-explanation')
        if len(explanation_sections) >= 1:
            content_div = explanation_sections[0].find('div', class_=False)
            if content_div:
                result['penjelasan'] = clean_html_content(content_div)

        # 7. Kesimpulan section (second article-explanation)
        if len(explanation_sections) >= 2:
            content_div = explanation_sections[1].find('div', class_=False)
            if content_div:
                result['kesimpulan'] = clean_html_content(content_div)

        # 8. Referensi section
        references_section = soup.find('section', class_='article-references')
        if references_section:
            content_div = references_section.find('div', class_=False)
            if content_div:
                result['referensi'] = clean_html_content(content_div)

        return result

    except Exception as e:
        print(f"\nError scraping {url}: {e}")
        return {
            'url': url,
            'full_title': '',
            'category': '',
            'date': '',
            'media': '',
            'cover_image_url': '',
            'hasil_periksa_fakta': '',
            'kategori_berita': '',
            'sumber': '',
            'narasi': '',
            'penjelasan': '',
            'kesimpulan': '',
            'referensi': '',
            'error': str(e)
        }

def scrape_articles_from_csv(csv_file, output_file=None):
    """
    Scrape full article content from URLs in a local CSV file (from Step 1)
    
    Args:
        csv_file: Path to the CSV file containing article URLs
        output_file: Output CSV file path (creates new if None)
        
    Returns:
        DataFrame with scraped articles or None if error occurs
    """
    try:
        # Read local CSV file
        print(f"Reading input CSV file: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        # Check if 'url' column exists
        if 'url' not in df.columns:
            print("Error: CSV file must have a 'url' column")
            return None
        
        # Determine output filename
        if output_file is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f'turnbackhoax_full_articles_{timestamp}.csv'
        
        # Check for existing data and determine which URLs to skip
        existing_urls = set()
        file_exists = False
        existing_df = None
        
        if pd.io.common.file_exists(output_file):
            try:
                existing_df = pd.read_csv(output_file, encoding='utf-8')
                if 'url' in existing_df.columns:
                    # Find URLs that have full_title (indicating they were fully scraped)
                    scraped_mask = existing_df['url'].notna()
                    if 'full_title' in existing_df.columns:
                        scraped_mask = scraped_mask & existing_df['full_title'].notna()
                    existing_urls = set(existing_df.loc[scraped_mask, 'url'])
                    print(f"Found existing file: {output_file}")
                    print(f"Already scraped: {len(existing_urls)} URLs")
                    file_exists = True
            except Exception as e:
                print(f"Warning: Could not read existing file: {e}")
        
        # Get URLs to scrape
        all_urls = df['url'].dropna().unique().tolist()
        urls_to_scrape = [url for url in all_urls if url not in existing_urls]
        
        print(f"Total URLs in input: {len(all_urls)}")
        print(f"URLs to scrape: {len(urls_to_scrape)}")
        print(f"URLs to skip: {len(existing_urls)}")
        
        # Create CSV with headers if it doesn't exist
        if not file_exists:
            # Get all columns from input + article columns
            article_columns = ['full_title', 'category', 'date', 'media', 'cover_image_url', 
                             'hasil_periksa_fakta', 'kategori_berita', 'sumber', 
                             'narasi', 'penjelasan', 'kesimpulan', 'referensi']
            
            # Rename conflicting columns from input
            all_columns = []
            for col in df.columns:
                if col in ['category', 'date']:
                    all_columns.append(f'{col}_original')
                else:
                    all_columns.append(col)
            all_columns.extend(article_columns)
            
            empty_df = pd.DataFrame(columns=all_columns)
            empty_df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"Created new output file: {output_file}")
        
        # Track statistics
        articles_scraped = 0
        articles_skipped = len(existing_urls)
        
        # Process each URL with progress bar
        for url in tqdm(urls_to_scrape, desc="Scraping articles"):
            # Scrape the article
            result = scrape_article(url)
            
            # Get the row(s) from input CSV for this URL
            url_rows = df[df['url'] == url].copy()
            
            # Rename conflicting columns
            if 'category' in url_rows.columns:
                url_rows.rename(columns={'category': 'category_original'}, inplace=True)
            if 'date' in url_rows.columns:
                url_rows.rename(columns={'date': 'date_original'}, inplace=True)
            
            # Add scraped data to each row
            for key, value in result.items():
                if key != 'url':
                    url_rows[key] = value
            
            # Append to CSV immediately
            url_rows.to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8')
            
            articles_scraped += 1
            
            # Add a delay between requests to be polite to the server
            time.sleep(1)
        
        print(f"\n{'='*70}")
        print(f"Scraping completed!")
        print(f"Articles scraped: {articles_scraped}")
        print(f"Articles skipped: {articles_skipped}")
        print(f"Total articles in file: {articles_scraped + articles_skipped}")
        print(f"Data saved to: {output_file}")
        print(f"{'='*70}")
        
        # Return the complete DataFrame
        try:
            final_df = pd.read_csv(output_file, encoding='utf-8')
            return final_df
        except Exception as e:
            print(f"Warning: Could not read final CSV: {e}")
            return None
    
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found")
        return None
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        import traceback
        traceback.print_exc()
        return None

def scrape_articles_from_google_sheet(sheet_id=None, sheet_name=None):
    """
    Process Google Sheet and scrape articles
    
    Args:
        sheet_id: Google Sheet ID (uses SHEET_ID if None)
        sheet_name: Google Sheet name/gid (uses SHEET_NAME if None)
        
    Returns:
        DataFrame with scraped articles or None if error occurs
    """
    # Use global variables if not provided
    if sheet_id is None:
        sheet_id = SHEET_ID
    if sheet_name is None:
        sheet_name = SHEET_NAME

    # Validate configuration
    if not sheet_id or not sheet_name:
        print("Error: SHEET_ID and SHEET_NAME must be configured")
        print("Please set these values in the configuration section at the top of the script")
        return None

    # URL of the Google Sheet (export as CSV)
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_name}"

    try:
        # Read Google Sheet
        print("Reading Google Sheet...")
        df = pd.read_csv(csv_url)

        # Filter rows where column H is True
        df_filtered = df[df.iloc[:, 7] == True]  # Column H is index 7
        urls = df_filtered.iloc[:, 2].tolist()  # Column C is index 2

        print(f"Found {len(urls)} URLs to process")

        # Initialize list to store results
        results = []

        # Process each URL with progress bar
        for url in tqdm(urls, desc="Scraping articles"):
            result = scrape_article(url)
            results.append(result)
            time.sleep(1)  # Be polite to the server

        # Create DataFrame from results
        results_df = pd.DataFrame(results)

        # Save to CSV with timestamp and UTF-8 encoding
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f'turnbackhoax_articles_{timestamp}.csv'
        results_df.to_csv(filename, index=False, encoding='utf-8')

        print(f"\nScraping completed successfully!")
        print(f"Total articles scraped: {len(results_df)}")
        print(f"Data saved to: {filename}")

        return results_df

    except Exception as e:
        print(f"Error processing Google Sheet: {e}")
        return None


# ============================================================================
# STEP 3: CLEANSING ARTICLE CONTENT
# ============================================================================

def process_text(text):
    """
    Clean and format text content
    
    Args:
        text: Text string to process
        
    Returns:
        Processed text with proper formatting
    """
    if not isinstance(text, str):
        return text

    # Pattern for continuous "=" (like "=====" of any length)
    text = re.sub(r'={2,}', r'\n\g<0>\n', text)

    # Pattern for spaced "=" (like "= = =" with any number of "=")
    text = re.sub(r'(?:=\s+){2,}=', r'\n\g<0>\n', text)

    return text


def clean_google_sheet_data(sheet_id=None, sheet_name=None):
    """
    Clean and process data from Google Sheet
    
    Args:
        sheet_id: Google Sheet ID (uses SHEET_ID if None)
        sheet_name: Google Sheet name/gid (uses SHEET_NAME if None)
        
    Returns:
        DataFrame with processed data or None if error occurs
    """
    # Use global variables if not provided
    if sheet_id is None:
        sheet_id = SHEET_ID
    if sheet_name is None:
        sheet_name = SHEET_NAME

    # Validate configuration
    if not sheet_id or not sheet_name:
        print("Error: SHEET_ID and SHEET_NAME must be configured")
        print("Please set these values in the configuration section at the top of the script")
        return None

    # URL of the Google Sheet (export as CSV)
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_name}"

    try:
        # Read the sheet
        print("Reading Google Sheet...")
        df = pd.read_csv(csv_url)

        # Process column G starting from row 2
        df.iloc[1:, 6] = df.iloc[1:, 6].apply(process_text)

        # Save to CSV with UTF-8 encoding
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_filename = f'processed_sheet_{timestamp}.csv'
        txt_filename = f'processed_column_g_{timestamp}.txt'
        
        df.to_csv(csv_filename, index=False, encoding='utf-8')

        # Save to text file
        with open(txt_filename, 'w', encoding='utf-8') as f:
            for text in df.iloc[1:, 6]:
                f.write(str(text) + '\n\n')

        print(f"\nData processing completed successfully!")
        print(f"CSV saved to: {csv_filename}")
        print(f"Text file saved to: {txt_filename}")
        print("\nSample of processed text:")
        print(df.iloc[1, 6])

        return df

    except Exception as e:
        print(f"Error processing Google Sheet: {e}")
        return None


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """
    Main function to run the scraper with command-line arguments
    """
    parser = argparse.ArgumentParser(
        description='Turn Back Hoax Scraper - Scrape articles from turnbackhoax.id',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape headlines for current month
  python3 scraping_turn_back_hoax.py headlines
  
  # Scrape headlines for a specific month
  python3 scraping_turn_back_hoax.py headlines --date-range "January+2025"
  
  # Scrape headlines for multiple months (comma-separated)
  python3 scraping_turn_back_hoax.py headlines --date-range "January+2025,December+2024"
  
  # Scrape headlines with page limit (first 5 pages only)
  python3 scraping_turn_back_hoax.py headlines --date-range "January+2025" --end 5
  
  # Scrape headlines with visible browser (not headless)
  python3 scraping_turn_back_hoax.py headlines --date-range "January+2025" --show-browser
  
  # Scrape headlines with specific output file (resumes if exists)
  python3 scraping_turn_back_hoax.py headlines --output headlines.csv
  
  # Scrape full articles from a CSV file
  python3 scraping_turn_back_hoax.py articles --csv headlines.csv
  
  # Scrape full articles with specific output file (resumes if exists)
  python3 scraping_turn_back_hoax.py articles --csv headlines.csv --output full_articles.csv
  
  # Scrape full articles from Google Sheet
  python3 scraping_turn_back_hoax.py articles
  
  # Clean data from Google Sheet
  python3 scraping_turn_back_hoax.py clean
        """
    )

    parser.add_argument(
        'mode',
        choices=['headlines', 'articles', 'clean'],
        help='Scraping mode: headlines (scrape article list), articles (scrape full content), clean (process data)'
    )
    
    parser.add_argument(
        '--date-range',
        type=str,
        help='Date range(s) for headlines mode. Format: "Month+Year" (e.g., "January+2025"). '
             'Multiple ranges can be comma-separated (e.g., "January+2025,December+2024"). '
             'Default: current month.'
    )
    
    parser.add_argument(
        '--start',
        type=int,
        default=1,
        help='Starting page number for each date range (default: 1)'
    )
    
    parser.add_argument(
        '--end',
        type=int,
        help='Ending page number for each date range (default: all pages)'
    )
    
    parser.add_argument(
        '--csv',
        type=str,
        help='CSV file path (for articles mode, alternative to Google Sheet)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV file path (resumes if exists)'
    )
    
    parser.add_argument(
        '--show-browser',
        action='store_true',
        help='Show browser window (not headless) for headlines mode'
    )
    
    parser.add_argument(
        '--sheet-id',
        type=str,
        help='Google Sheet ID (overrides config)'
    )
    
    parser.add_argument(
        '--sheet-name',
        type=str,
        help='Google Sheet name/gid (overrides config)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Turn Back Hoax Scraper (Selenium Edition)")
    print("=" * 70)
    print()

    if args.mode == 'headlines':
        print("Mode: Scraping Headlines")
        print("-" * 70)
        
        # Parse date ranges
        date_ranges = None
        if args.date_range:
            date_ranges = [dr.strip() for dr in args.date_range.split(',')]
            print(f"Date ranges: {[dr.replace('+', ' ') for dr in date_ranges]}")
        else:
            # Use get_date_ranges() which respects the MONTHS list in the script
            date_ranges = get_date_ranges()
            print(f"Date ranges (from config): {[dr.replace('+', ' ') for dr in date_ranges]}")
        
        if args.output:
            print(f"Output file: {args.output}")
        if args.show_browser:
            print("Browser mode: Visible")
        
        df = scrape_all_headlines(
            date_ranges=date_ranges,
            start_page=args.start,
            end_page=args.end,
            output_file=args.output,
            headless=not args.show_browser
        )
        if df is not None:
            print("\nSample of scraped data:")
            print(df.head())

    elif args.mode == 'articles':
        print("Mode: Scraping Full Articles")
        print("-" * 70)
        
        # Check if CSV file is provided
        if args.csv:
            print(f"Source: Local CSV file ({args.csv})")
            if args.output:
                print(f"Output file: {args.output}")
            df = scrape_articles_from_csv(args.csv, output_file=args.output)
        else:
            print("Source: Google Sheet")
            df = scrape_articles_from_google_sheet(
                sheet_id=args.sheet_id,
                sheet_name=args.sheet_name
            )
        
        if df is not None:
            print("\nSample of scraped data:")
            print(df.head())

    elif args.mode == 'clean':
        print("Mode: Cleaning Data")
        print("-" * 70)
        df = clean_google_sheet_data(
            sheet_id=args.sheet_id,
            sheet_name=args.sheet_name
        )

    print()
    print("=" * 70)
    print("Process completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()