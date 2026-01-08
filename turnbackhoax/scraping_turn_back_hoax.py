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


# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Page range for scraping headlines
START_PAGE = 1
END_PAGE = 2

# Google Sheet configuration for article scraping
SHEET_ID = "1hX-iWkJslmBHTMvYE-0fLs9I46vvm_Er3sfrn9pBMms"
SHEET_NAME = "0"  # gid from the URL

# Headers to mimic browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ============================================================================
# STEP 1: SCRAPING HEADLINES
# ============================================================================

def scrape_turnbackhoax_page(page_number):
    """
    Scrape headlines and metadata from a single page of turnbackhoax.id
    
    Args:
        page_number: The page number to scrape
        
    Returns:
        DataFrame with scraped data or None if error occurs
    """
    url = f"https://turnbackhoax.id/articles?category=all&&page={page_number}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        data = {
            'title': [],
            'url': [],
            'preview': [],
            'image_url': [],
            'date': [],
            'category': []
        }

        # Updated selector for new website structure
        articles = soup.find_all('div', class_='news-card-h-alt')

        for article in articles:
            # Extract title and URL
            title_element = article.find('h2')
            link_element = article.find('a', href=True)
            
            if title_element:
                # Get the full title (from the span that's visible on larger screens)
                title_span = title_element.find('span', class_='hidden')
                if title_span:
                    title_text = title_span.text.strip()
                else:
                    title_text = title_element.text.strip()
                data['title'].append(title_text)
            else:
                data['title'].append('')
            
            if link_element:
                data['url'].append(link_element['href'])
            else:
                data['url'].append('')

            # Extract preview text
            preview_element = article.find('p')
            if preview_element:
                # Get the full preview (from the span that's visible on larger screens)
                preview_span = preview_element.find('span', class_='hidden')
                if preview_span:
                    preview_text = preview_span.text.strip()
                else:
                    preview_text = preview_element.text.strip()
                data['preview'].append(preview_text)
            else:
                data['preview'].append('')

            # Extract image URL
            image_element = article.find('img')
            if image_element and image_element.get('src'):
                data['image_url'].append(image_element['src'])
            else:
                data['image_url'].append('')

            # Extract date
            date_span = article.find('span', class_='text-light-black')
            if date_span:
                data['date'].append(date_span.text.strip())
            else:
                data['date'].append('')

            # Extract category
            category_link = article.find('a', href=lambda x: x and 'category=' in str(x))
            if category_link:
                data['category'].append(category_link.text.strip())
            else:
                data['category'].append('')

        return pd.DataFrame(data)

    except requests.RequestException as e:
        print(f"\nError on page {page_number}: {e}")
        return None
    except Exception as e:
        print(f"\nUnexpected error on page {page_number}: {e}")
        return None

def scrape_all_pages(start_page=None, end_page=None):
    """
    Scrape headlines from multiple pages of turnbackhoax.id
    
    Args:
        start_page: Starting page number (uses START_PAGE if None)
        end_page: Ending page number (uses END_PAGE if None)
        
    Returns:
        DataFrame with all scraped data or None if error occurs
    """
    # Use global variables if not provided
    if start_page is None:
        start_page = START_PAGE
    if end_page is None:
        end_page = END_PAGE

    # Initialize empty list to store DataFrames from each page
    all_data = []

    # Create progress bar
    pbar = tqdm(range(start_page, end_page + 1), desc="Scraping pages")

    for page_num in pbar:
        # Update progress bar description
        pbar.set_description(f"Scraping page {page_num}")

        # Scrape the current page
        df = scrape_turnbackhoax_page(page_num)

        if df is not None and not df.empty:
            # Add page number column
            df['page_number'] = page_num
            all_data.append(df)

        # Add a delay between requests to be polite to the server
        time.sleep(1)

    if all_data:
        # Combine all DataFrames
        final_df = pd.concat(all_data, ignore_index=True)

        # Save to CSV with UTF-8 encoding
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f'turnbackhoax_headlines_{timestamp}.csv'
        final_df.to_csv(filename, index=False, encoding='utf-8')

        print(f"\nScraping completed successfully!")
        print(f"Total articles scraped: {len(final_df)}")
        print(f"Data saved to: {filename}")

        return final_df
    else:
        print("\nNo data was scraped successfully.")
        return None


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

def scrape_articles_from_csv(csv_file):
    """
    Scrape full article content from URLs in a local CSV file (from Step 1)
    
    Args:
        csv_file: Path to the CSV file containing article URLs
        
    Returns:
        DataFrame with scraped articles or None if error occurs
    """
    try:
        # Read local CSV file
        print(f"Reading CSV file: {csv_file}")
        df = pd.read_csv(csv_file)
        
        # Check if 'url' column exists
        if 'url' not in df.columns:
            print("Error: CSV file must have a 'url' column")
            return None
        
        # Get all URLs
        urls = df['url'].dropna().tolist()
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
        
        # Merge with original data to include title, date, etc.
        final_df = df.merge(results_df, on='url', how='left', suffixes=('_original', ''))
        
        # Save to CSV with timestamp and UTF-8 encoding
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f'turnbackhoax_full_articles_{timestamp}.csv'
        final_df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f"\nScraping completed successfully!")
        print(f"Total articles scraped: {len(results_df)}")
        print(f"Data saved to: {filename}")
        
        return final_df
    
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found")
        return None
    except Exception as e:
        print(f"Error processing CSV file: {e}")
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
  # Scrape headlines from pages 1-10
  python3 scraping_turn_back_hoax.py headlines --start 1 --end 10
  
  # Scrape full articles from a CSV file (output from Step 1)
  python3 scraping_turn_back_hoax.py articles --csv turnbackhoax_headlines_20260108_143901.csv
  
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
        '--start',
        type=int,
        help=f'Starting page number (default: {START_PAGE})'
    )
    
    parser.add_argument(
        '--end',
        type=int,
        help=f'Ending page number (default: {END_PAGE})'
    )
    
    parser.add_argument(
        '--csv',
        type=str,
        help='CSV file path (for articles mode, alternative to Google Sheet)'
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
    print("Turn Back Hoax Scraper")
    print("=" * 70)
    print()

    if args.mode == 'headlines':
        print("Mode: Scraping Headlines")
        print("-" * 70)
        df = scrape_all_pages(start_page=args.start, end_page=args.end)
        if df is not None:
            print("\nSample of scraped data:")
            print(df.head())

    elif args.mode == 'articles':
        print("Mode: Scraping Full Articles")
        print("-" * 70)
        
        # Check if CSV file is provided
        if args.csv:
            print(f"Source: Local CSV file ({args.csv})")
            df = scrape_articles_from_csv(args.csv)
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