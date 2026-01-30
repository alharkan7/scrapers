#!/usr/bin/env python3
"""
BRIN Research Group Scraper
Scrapes research group information from https://manajementalenta.brin.go.id/kelompok-riset/detail/{number}

Usage:
    python scraper.py                    # Scrape pages 1-1633 (default)
    python scraper.py --start 1 --end 10  # Scrape pages 1-10 (test run)
    python scraper.py --start 500 --end 600 # Resume scraping from 500-600

The script will append to the output file and skip already scraped pages.
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import argparse
import os
from typing import Dict, Optional, Set


def get_scraped_page_ids(output_file: str) -> Set[int]:
    """
    Load already scraped page IDs from existing output file
    
    Args:
        output_file: Path to the CSV output file
        
    Returns:
        Set of page IDs that have already been scraped
    """
    scraped_ids = set()
    
    if not os.path.exists(output_file):
        return scraped_ids
    
    try:
        with open(output_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('page_id'):
                    try:
                        scraped_ids.add(int(row['page_id']))
                    except ValueError:
                        pass
    except Exception as e:
        print(f"Warning: Could not read existing file {output_file}: {e}")
    
    return scraped_ids


def clean_data_for_csv(data: Dict[str, str]) -> Dict[str, str]:
    """
    Clean data to prevent CSV formatting issues
    
    Args:
        data: Dictionary containing scraped data
        
    Returns:
        Cleaned dictionary with newlines and special characters handled
    """
    cleaned = {}
    for key, value in data.items():
        if value:
            # Replace newlines and multiple spaces with single space
            # This prevents CSV from breaking when fields contain line breaks
            cleaned_value = ' '.join(str(value).split())
        else:
            cleaned_value = ''
        cleaned[key] = cleaned_value
    return cleaned


def scrape_research_group(page_id: int) -> Optional[Dict[str, str]]:
    """
    Scrape a single research group page
    
    Args:
        page_id: The page ID to scrape
        
    Returns:
        Dictionary containing the scraped data, or None if page is invalid
    """
    url = f"https://manajementalenta.brin.go.id/kelompok-riset/detail/{page_id}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main content section
        box_general = soup.find('div', class_='box_general_3')
        if not box_general:
            print(f"Page {page_id}: No content box found - likely blank page")
            return None
        
        # Initialize data dictionary
        data = {
            'page_id': page_id,
            'url': url,
            'kelompok_riset': '',
            'satuan_kerja_organisasi_riset': '',
            'satuan_kerja_pusat_riset': '',
            'rumpun_riset': '',
            'kelompok_riset_nama': '',
            'nomor_sk_penetapan': '',
            'topik_riset': '',
            'lingkup_kegiatan_riset': '',
            'lokasi_riset': '',
            'mitra_kerjasama': '',
            'nama_koordinator': '',
            'email_koordinator': ''
        }
        
        # Extract title (first h3 in indent_title_in)
        title_div = box_general.find('div', class_='indent_title_in')
        if title_div:
            h3_tags = title_div.find_all('h3')
            if len(h3_tags) > 0:
                data['kelompok_riset'] = h3_tags[0].get_text(strip=True)
        
        # Extract all the fields from wrapper_indent
        wrapper = box_general.find('div', class_='wrapper_indent')
        if wrapper:
            # Find all paragraphs with strong tags
            paragraphs = wrapper.find_all('p')
            
            for p in paragraphs:
                strong_tag = p.find('strong')
                if strong_tag:
                    label = strong_tag.get_text(strip=True)
                    
                    # Get the text after the strong tag
                    # The value is either in the same paragraph after <br> or in a separate element
                    value = ''
                    
                    # Try to get text after <br>
                    br_tag = p.find('br')
                    if br_tag:
                        # Get all text after the br tag
                        value = br_tag.next_sibling
                        if value and isinstance(value, str):
                            value = value.strip()
                        else:
                            value = ''
                    else:
                        # No br tag, get text after strong tag
                        strong_next = strong_tag.next_sibling
                        if strong_next and isinstance(strong_next, str):
                            value = strong_next.strip()
                    
                    # Map label to field
                    label_lower = label.lower()
                    if 'satuan kerja organisasi riset' in label_lower:
                        data['satuan_kerja_organisasi_riset'] = value
                    elif 'satuan kerja pusat riset' in label_lower:
                        data['satuan_kerja_pusat_riset'] = value
                    elif 'rumpun riset' in label_lower:
                        data['rumpun_riset'] = value
                    elif 'kelompok riset' in label_lower and 'kegiatan' not in label_lower.lower():
                        # Skip the first one (title) and get the second one
                        if not data['kelompok_riset_nama'] and data['kelompok_riset']:
                            data['kelompok_riset_nama'] = value
                    elif 'nomor sk penetapan' in label_lower:
                        data['nomor_sk_penetapan'] = value
                    elif 'topik riset' in label_lower:
                        data['topik_riset'] = value
                    elif 'lingkup kegiatan riset' in label_lower:
                        data['lingkup_kegiatan_riset'] = value
                    elif 'lokasi riset' in label_lower:
                        data['lokasi_riset'] = value
                    elif 'mitra kerjasama' in label_lower:
                        data['mitra_kerjasama'] = value
                    elif 'nama koordinator' in label_lower:
                        data['nama_koordinator'] = value
                    elif 'email koordinator' in label_lower:
                        data['email_koordinator'] = value
        
        # Check if this is a valid data entry (has at least some content)
        if (data['kelompok_riset'] or 
            data['kelompok_riset_nama'] or 
            data['nama_koordinator']):
            return data
        else:
            print(f"Page {page_id}: No valid data found")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Page {page_id}: Request error - {e}")
        return None
    except Exception as e:
        print(f"Page {page_id}: Error parsing - {e}")
        return None


def main():
    """Main function to scrape all research groups"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Scrape BRIN research group data from manajementalenta.brin.go.id',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scraper.py                    # Scrape all pages (1-1633)
  python scraper.py --start 1 --end 10  # Test run: scrape pages 1-10
  python scraper.py --start 500 --end 600 # Resume scraping from 500-600
        """
    )
    parser.add_argument('--start', type=int, default=1, help='Starting page ID (default: 1)')
    parser.add_argument('--end', type=int, default=1633, help='Ending page ID (default: 1633)')
    parser.add_argument('--output', type=str, default='brin_research_groups.csv', 
                       help='Output CSV file (default: brin_research_groups.csv)')
    parser.add_argument('--delay', type=float, default=0.5, 
                       help='Delay between requests in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    # Get the script's directory to set default output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Validate arguments
    if args.start < 1:
        print("Error: Start ID must be at least 1")
        return
    
    if args.end < args.start:
        print("Error: End ID must be greater than or equal to start ID")
        return
    
    start_id = args.start
    end_id = args.end
    # If output is just a filename (not a path), save it in the script's directory
    if os.path.basename(args.output) == args.output:
        output_file = os.path.join(script_dir, args.output)
    else:
        output_file = args.output
    delay = args.delay
    
    # CSV header
    headers = [
        'page_id',
        'url',
        'kelompok_riset',
        'satuan_kerja_organisasi_riset',
        'satuan_kerja_pusat_riset',
        'rumpun_riset',
        'kelompok_riset_nama',
        'nomor_sk_penetapan',
        'topik_riset',
        'lingkup_kegiatan_riset',
        'lokasi_riset',
        'mitra_kerjasama',
        'nama_koordinator',
        'email_koordinator'
    ]
    
    # Load already scraped page IDs
    scraped_ids = get_scraped_page_ids(output_file)
    if scraped_ids:
        print(f"Found {len(scraped_ids)} already scraped pages in {output_file}")
        print(f"Will skip pages: {min(scraped_ids)} to {max(scraped_ids)} (that exist in file)")
    
    # Check if output file exists to determine if we need to write header
    file_exists = os.path.exists(output_file)
    
    # Statistics
    total_pages = end_id - start_id + 1
    scraped_count = 0
    skipped_count = 0
    blank_count = 0
    error_count = 0
    
    print(f"\nStarting scrape from ID {start_id} to {end_id}")
    print(f"Output file: {output_file}")
    print(f"Delay between requests: {delay}s")
    print("-" * 80)
    
    # Open CSV file in append mode
    with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
        # Configure writer to quote all fields that contain special characters
        writer = csv.DictWriter(csvfile, fieldnames=headers, 
                              quoting=csv.QUOTE_MINIMAL,  # Quote only when necessary
                              quotechar='"', 
                              escapechar='\\')
        
        # Write header only if file is new
        if not file_exists:
            writer.writeheader()
            csvfile.flush()  # Ensure header is written immediately
        
        # Iterate through all page IDs
        for page_id in range(start_id, end_id + 1):
            # Skip if already scraped
            if page_id in scraped_ids:
                print(f"Skipping page {page_id}/{end_id} (already scraped)  ", end='\r')
                skipped_count += 1
                continue
            
            print(f"Processing page {page_id}/{end_id}...  ", end='\r')
            
            data = scrape_research_group(page_id)
            
            if data:
                # Clean data to remove newlines and extra spaces that break CSV
                cleaned_data = clean_data_for_csv(data)
                writer.writerow(cleaned_data)
                csvfile.flush()  # Write immediately to disk
                scraped_count += 1
            elif data is None:
                blank_count += 1
            else:
                error_count += 1
            
            # Add delay to be respectful to the server
            time.sleep(delay)
            
            # Print progress every 50 pages or at the end
            if page_id % 50 == 0 or page_id == end_id:
                print(f"\nProgress: {page_id}/{end_id} | New: {scraped_count} | Skipped: {skipped_count} | Blank: {blank_count} | Errors: {error_count}")
    
    # Final statistics
    print("\n" + "-" * 80)
    print(f"Scraping complete!")
    print(f"Total pages processed: {total_pages}")
    print(f"Newly scraped: {scraped_count}")
    print(f"Skipped (already in file): {skipped_count}")
    print(f"Blank pages (no data): {blank_count}")
    print(f"Errors: {error_count}")
    print(f"Total records in file: {len(get_scraped_page_ids(output_file))}")
    print(f"Data saved to: {output_file}")


if __name__ == "__main__":
    main()
