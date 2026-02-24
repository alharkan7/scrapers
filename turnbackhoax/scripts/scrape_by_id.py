#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turn Back Hoax Scraper - By Article ID

Scrapes article content directly by iterating through article IDs.
No CSV input required - just define START_ARTICLE_ID and END_ARTICLE_ID.

Usage:
    python3 scrape_by_id.py

Configuration:
    Edit START_ARTICLE_ID and END_ARTICLE_ID below.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
from tqdm import tqdm
from datetime import datetime

# ============================================================================
# CONFIGURATION - Edit these values
# ============================================================================

START_ARTICLE_ID = 1      # Starting article ID (1 for full scrape)
END_ARTICLE_ID = 33000   # Ending article ID (set high, script will stop automatically)

# Stop scraping after this many consecutive "not found" or 404 errors
MAX_CONSECUTIVE_MISSES = 20

# Output file (will resume if exists)
OUTPUT_FILE = "../data/turnbackhoax_articles_by_id.csv"
SKIPPED_FILE = "../data/skipped_article_ids.csv"

# Delay between requests (seconds) - be polite to the server
REQUEST_DELAY = 1.0

# Number of retry attempts for failed requests
MAX_RETRIES = 3

# Delay between retries (seconds)
RETRY_DELAY = 2.0

# Define CSV columns globally
CSV_COLUMNS = [
    'article_id', 'url', 'full_title', 'category', 'date', 'media',
    'cover_image_url', 'hasil_periksa_fakta', 'kategori_berita', 'sumber',
    'narasi', 'penjelasan', 'kesimpulan', 'referensi', 'error', 'scraped_at'
]

# ============================================================================
# DO NOT EDIT BELOW THIS LINE
# ============================================================================

BASE_URL = "https://turnbackhoax.id/articles"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}


def normalize_unicode_characters(text):
    """Normalize unicode characters to their ASCII equivalents."""
    if not isinstance(text, str):
        return text
    
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
    """Clean HTML content and format it into readable paragraphs."""
    # Remove script and style elements
    for script in html_content.find_all(['script', 'style']):
        script.decompose()

    # Get text and clean it
    text = html_content.get_text(separator=' ')
    text = normalize_unicode_characters(text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)

    paragraphs = text.split('\n\n')
    cleaned_paragraphs = [p.strip() for p in paragraphs if p.strip()]

    return '\n\n'.join(cleaned_paragraphs)


def scrape_article(article_id, max_retries=3, retry_delay=2.0):
    """
    Scrape detailed information from a turnbackhoax article by ID.
    Retries on failure up to max_retries times.
    
    Args:
        article_id: Numeric article ID
        max_retries: Number of retry attempts for failed requests
        retry_delay: Delay between retries in seconds
        
    Returns:
        Dictionary with comprehensive article data, or None if article doesn't exist
    """
    url = f"{BASE_URL}/{article_id}"
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
            
            # Check for 404 - no retry needed
            if response.status_code == 404:
                return None
            
            # Server errors (5xx) - should retry
            if response.status_code >= 500:
                last_error = f"HTTP {response.status_code}"
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return {
                    'article_id': article_id,
                    'url': url,
                    'error': f"{last_error} after {max_retries} attempts",
                    'scraped_at': datetime.now().isoformat()
                }
            
            # Other non-200 status codes
            if response.status_code != 200:
                return {
                    'article_id': article_id,
                    'url': url,
                    'error': f"HTTP {response.status_code}",
                    'scraped_at': datetime.now().isoformat()
                }
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if page contains actual article content
            article = soup.find('article')
            if not article:
                # Check if it's a "not found" page
                title = soup.find('title')
                if title and ('tidak ditemukan' in title.text.lower() or 'not found' in title.text.lower()):
                    return None
                # Page exists but no article tag
                return {
                    'article_id': article_id,
                    'url': url,
                    'error': 'No article content found',
                    'scraped_at': datetime.now().isoformat()
                }

            # Initialize result dictionary
            result = {
                'article_id': article_id,
                'url': response.url,  # Use final URL after redirects
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
                'error': '',
                'scraped_at': datetime.now().isoformat()
            }

            # 1. Full Title
            title_tag = soup.find('h1')
            if title_tag:
                result['full_title'] = title_tag.text.strip()

            # 2. Category, Date, Media from info div
            info_div = article.find('div', class_=lambda x: x and 'flex' in str(x))
            if info_div:
                info_texts = list(info_div.stripped_strings)
                if len(info_texts) >= 2:
                    result['category'] = info_texts[1]
                if len(info_texts) >= 3:
                    result['date'] = info_texts[2]
                if len(info_texts) >= 4:
                    result['media'] = info_texts[3]

            # 3. Cover Image (first img in article)
            imgs = article.find_all('img')
            if imgs:
                result['cover_image_url'] = imgs[0].get('src', '')

            # 4. Hasil Periksa Fakta section
            factcheck_section = soup.find('section', class_='article-factcheck')
            if factcheck_section:
                result_span = factcheck_section.find('span', class_='factcheck-result')
                if result_span:
                    result['hasil_periksa_fakta'] = result_span.text.strip()
                
                category_span = factcheck_section.find('span', class_='factcheck-category')
                if category_span:
                    kategori_text = category_span.text.strip()
                    if 'Kategori Berita:' in kategori_text:
                        result['kategori_berita'] = kategori_text.replace('Kategori Berita:', '').strip()
                
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

        except requests.exceptions.Timeout:
            last_error = 'Request timeout'
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
        except Exception as e:
            # Parse errors should not be retried
            return {
                'article_id': article_id,
                'url': url,
                'error': f"Parse error: {str(e)}",
                'scraped_at': datetime.now().isoformat()
            }
    
    # All retries exhausted
    return {
        'article_id': article_id,
        'url': url,
        'error': f"{last_error} after {max_retries} attempts",
        'scraped_at': datetime.now().isoformat()
    }


def save_result(result):
    """Save a single result to CSV, ensuring column consistency."""
    if not result:
        return
        
    # Ensure all columns exist
    for col in CSV_COLUMNS:
        if col not in result:
            result[col] = ""
            
    # Create DataFrame with enforced column order
    df = pd.DataFrame([result], columns=CSV_COLUMNS)
    
    # Append to CSV
    # If file doesn't exist, write header. If it does, don't.
    header = not os.path.exists(OUTPUT_FILE)
    df.to_csv(OUTPUT_FILE, mode='a', header=header, index=False, encoding='utf-8')


def save_skipped(article_id, url, status_code, description):
    """Save a skipped/404 article to the skipped file."""
    skip_record = {
        'article_id': article_id,
        'url': url,
        'status_code': status_code,
        'status_description': description
    }
    
    df = pd.DataFrame([skip_record])
    
    # Append to CSV
    header = not os.path.exists(SKIPPED_FILE)
    df.to_csv(SKIPPED_FILE, mode='a', header=header, index=False, encoding='utf-8')


def get_scraped_ids(output_file, skipped_file=None):
    """Get set of article IDs already scraped or skipped."""
    scraped = set()
    
    # 1. Read successful scrapes
    if os.path.exists(output_file):
        try:
            df = pd.read_csv(output_file, encoding='utf-8')
            if 'article_id' in df.columns:
                scraped.update(df['article_id'].dropna().astype(int).unique())
        except Exception as e:
            print(f"Warning: Could not read output file: {e}")
            
    # 2. Read skipped IDs (404s)
    if skipped_file and os.path.exists(skipped_file):
        try:
            df = pd.read_csv(skipped_file, encoding='utf-8')
            if 'article_id' in df.columns:
                scraped.update(df['article_id'].dropna().astype(int).unique())
        except Exception as e:
            print(f"Warning: Could not read skipped file: {e}")
    
    return scraped


def main():
    """Main scraping function."""
    print("=" * 70)
    print("Turn Back Hoax Scraper - By Article ID")
    print("=" * 70)
    print()
    print(f"Article ID range: {START_ARTICLE_ID} to {END_ARTICLE_ID}")
    print(f"Total IDs to check: {END_ARTICLE_ID - START_ARTICLE_ID + 1}")
    print(f"Stop threshold: {MAX_CONSECUTIVE_MISSES} consecutive misses")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Request delay: {REQUEST_DELAY}s")
    print(f"Max retries: {MAX_RETRIES}")
    print()
    
    # Get already scraped IDs
    scraped_ids = get_scraped_ids(OUTPUT_FILE, SKIPPED_FILE)
    if scraped_ids:
        print(f"Already scraped/skipped: {len(scraped_ids)} articles")
        print(f"Resuming from where we left off...")
    
    # Determine IDs to scrape
    all_ids = range(START_ARTICLE_ID, END_ARTICLE_ID + 1)
    ids_to_scrape = [aid for aid in all_ids if aid not in scraped_ids]
    
    print(f"IDs to scrape: {len(ids_to_scrape)}")
    print()
    
    if not ids_to_scrape:
        print("All articles already scraped!")
        return
    
    # Create CSV with headers if it doesn't exist (handled by save_result now, but good to init)
    if not os.path.exists(OUTPUT_FILE):
        empty_df = pd.DataFrame(columns=CSV_COLUMNS)
        empty_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        print(f"Created new output file: {OUTPUT_FILE}")
        
    # Create Skipped CSV header if it doesn't exist
    if not os.path.exists(SKIPPED_FILE):
        skipped_df = pd.DataFrame(columns=['article_id', 'url', 'status_code', 'status_description'])
        skipped_df.to_csv(SKIPPED_FILE, index=False, encoding='utf-8')
    
    # Statistics
    stats = {
        'scraped': 0,
        'not_found': 0,
        'errors': 0
    }
    
    # Scrape articles
    print("Starting scrape...")
    print("-" * 70)
    
    consecutive_misses = 0
    pbar = tqdm(ids_to_scrape, desc="Scraping")
    
    for article_id in pbar:
        pbar.set_description(f"ID {article_id}")
        
        result = scrape_article(article_id, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY)
        
        if result is None:
            # Article doesn't exist (404)
            stats['not_found'] += 1
            consecutive_misses += 1
            
            # Save to skipped file instead of main file
            save_skipped(article_id, f"{BASE_URL}/{article_id}", 404, "Not Found")
            
        elif result.get('error'):
            # Error occurred
            stats['errors'] += 1
            
            # If "No article content found", count as miss
            if 'No article content found' in result.get('error', ''):
                consecutive_misses += 1
                save_skipped(article_id, result.get('url'), 200, "No article content found")
            else:
                consecutive_misses = 0
                # Save actual errors (timeouts, etc) to main file
                save_result(result)
        else:
            # Successfully scraped
            stats['scraped'] += 1
            consecutive_misses = 0
            
            # Save result (success only)
            save_result(result)

        pbar.set_postfix({
            'found': stats['scraped'], 
            '404': stats['not_found'], 
            'err': stats['errors'],
            'streak': consecutive_misses
        })

        if consecutive_misses >= MAX_CONSECUTIVE_MISSES:
            pbar.close()
            print(f"\n\nStopping: Reached {MAX_CONSECUTIVE_MISSES} consecutive misses.")
            break
        
        # Delay between requests
        time.sleep(REQUEST_DELAY)
    
    pbar.close()
    
    # Final summary
    print()
    print("=" * 70)
    print("Scraping completed!")
    print("=" * 70)
    print(f"Articles found: {stats['scraped']}")
    print(f"Articles not found (404): {stats['not_found']}")
    print(f"Errors: {stats['errors']}")
    print(f"Data saved to: {OUTPUT_FILE}")
    print()
    
    # Show sample if we scraped anything
    if stats['scraped'] > 0:
        try:
            final_df = pd.read_csv(OUTPUT_FILE, encoding='utf-8')
            print(f"Total records in file: {len(final_df)}")
            print("\nSample of scraped data:")
            print(final_df[['article_id', 'full_title', 'category']].tail())
        except Exception as e:
            print(f"Could not read final CSV: {e}")


if __name__ == "__main__":
    main()
