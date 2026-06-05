#!/usr/bin/env python3
"""
BGN SPPG Scraper
Scrapes operational SPPG data from https://www.bgn.go.id/operasional-sppg
"""

import json
import csv
import time
import os
from typing import Dict, List
from urllib.parse import urlencode

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install requests beautifulsoup4 lxml")
    exit(1)


class BGNPPGScraper:
    """Scraper for BGN SPPG operational data"""

    BASE_URL = "https://www.bgn.go.id/operasional-sppg"
    OUTPUT_DIR = "output"

    def __init__(self, output_format: str = "json"):
        """
        Initialize the scraper

        Args:
            output_format: Output format ('json', 'csv', or 'both')
        """
        self.output_format = output_format.lower()
        self.scraped_data: List[Dict] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Create output directory
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    def load_existing_data(self, json_file: str = None) -> None:
        """
        Load existing scraped data to resume

        Args:
            json_file: Path to existing JSON file (defaults to sppg_data.json)
        """
        if json_file is None:
            json_file = os.path.join(self.OUTPUT_DIR, "sppg_data.json")

        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.scraped_data = data if isinstance(data, list) else []
                print(f"Loaded {len(self.scraped_data)} existing records")
            except Exception as e:
                print(f"Error loading existing data: {e}")
                self.scraped_data = []

    def fetch_page(self, page_num: int, max_retries: int = 3) -> str:
        """
        Fetch a page with retry logic

        Args:
            page_num: Page number to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            HTML content of the page
        """
        url = f"{self.BASE_URL}?page={page_num}"

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed for page {page_num}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    def parse_table_row(self, row) -> Dict[str, str]:
        """
        Parse a single table row

        Args:
            row: BeautifulSoup tr element

        Returns:
            Dictionary with row data
        """
        cells = row.find_all('td')
        if len(cells) < 7:
            return None

        data = {
            'no': cells[0].get_text(strip=True),
            'provinsi': cells[1].get_text(strip=True),
            'kab_kota': cells[2].get_text(strip=True),
            'kecamatan': cells[3].get_text(strip=True),
            'kelurahan_desa': cells[4].get_text(strip=True),
            'alamat': cells[5].get_text(strip=True),
            'nama_sppg': cells[6].get_text(strip=True),
        }

        # Validate that we have the unique ID
        if not data['nama_sppg']:
            return None

        return data

    def scrape_page(self, page_num: int) -> List[Dict]:
        """
        Scrape a single page

        Args:
            page_num: Page number to scrape

        Returns:
            List of records from the page
        """
        print(f"Scraping page {page_num}...")
        html = self.fetch_page(page_num)
        soup = BeautifulSoup(html, 'lxml')

        # Find the table body
        table_body = soup.find('tbody', id='sppg-body')
        if not table_body:
            print(f"Warning: Table body not found on page {page_num}")
            return []

        rows = table_body.find_all('tr', class_='divide-x')
        page_data = []

        for row in rows:
            data = self.parse_table_row(row)
            if data:
                page_data.append(data)

        print(f"  Found {len(page_data)} records on page {page_num}")
        return page_data

    def save_json(self, data: List[Dict], filename: str = None) -> None:
        """
        Save data to JSON file

        Args:
            data: List of records to save
            filename: Output filename (defaults to sppg_data.json)
        """
        if filename is None:
            filename = os.path.join(self.OUTPUT_DIR, "sppg_data.json")

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(data)} records to {filename}")

    def save_csv(self, data: List[Dict], filename: str = None) -> None:
        """
        Save data to CSV file

        Args:
            data: List of records to save
            filename: Output filename (defaults to sppg_data.csv)
        """
        if filename is None:
            filename = os.path.join(self.OUTPUT_DIR, "sppg_data.csv")

        if not data:
            print("No data to save to CSV")
            return

        fieldnames = ['no', 'provinsi', 'kab_kota', 'kecamatan', 'kelurahan_desa', 'alamat', 'nama_sppg']

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"Saved {len(data)} records to {filename}")

    def save_progress(self, last_page: int) -> None:
        """
        Save progress checkpoint

        Args:
            last_page: Last successfully scraped page
        """
        progress_file = os.path.join(self.OUTPUT_DIR, "progress.json")
        with open(progress_file, 'w') as f:
            json.dump({'last_page': last_page, 'timestamp': time.time()}, f)

    def load_progress(self) -> int:
        """
        Load progress from checkpoint

        Returns:
            Page number to resume from
        """
        progress_file = os.path.join(self.OUTPUT_DIR, "progress.json")
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    return data.get('last_page', 0)
            except Exception:
                pass
        return 0

    def scrape_range(self, start_page: int = 1, end_page: int = None,
                    save_interval: int = 10) -> List[Dict]:
        """
        Scrape a range of pages

        Args:
            start_page: First page to scrape (default: 1)
            end_page: Last page to scrape (None for unlimited)
            save_interval: Save progress every N pages

        Returns:
            All scraped data
        """
        # Load existing data
        self.load_existing_data()
        resume_from = self.load_progress()

        if resume_from > start_page:
            start_page = resume_from
            print(f"Resuming from page {start_page}")

        page_num = start_page
        all_data = self.scraped_data.copy()

        try:
            while True:
                if end_page and page_num > end_page:
                    print(f"Reached end page {end_page}")
                    break

                page_data = self.scrape_page(page_num)

                # Check if we got any data
                if not page_data:
                    print(f"No data found on page {page_num}. End of pagination?")
                    # Try one more page to confirm
                    next_data = self.scrape_page(page_num + 1)
                    if not next_data:
                        print("Confirmed: End of pagination reached")
                        break
                    else:
                        page_data = next_data
                        page_num += 1

                # Add new data
                all_data.extend(page_data)

                # Save progress periodically
                if page_num % save_interval == 0:
                    self.save_json(all_data)
                    if self.output_format in ['csv', 'both']:
                        self.save_csv(all_data)
                    self.save_progress(page_num)
                    print(f"Checkpoint saved at page {page_num}")

                page_num += 1

                # Small delay to be respectful
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nScraping interrupted by user")
        except Exception as e:
            print(f"\nError occurred: {e}")
            print(f"Last successful page: {page_num - 1}")
        finally:
            # Final save
            self.save_json(all_data)
            if self.output_format in ['csv', 'both']:
                self.save_csv(all_data)
            if page_num > start_page:
                self.save_progress(page_num - 1)

        print(f"\nScraping complete!")
        print(f"Total records: {len(all_data)}")
        print(f"Pages scraped: {page_num - start_page}")

        return all_data


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape BGN SPPG operational data')
    parser.add_argument('--start', type=int, default=1, help='Start page (default: 1)')
    parser.add_argument('--end', type=int, default=None, help='End page (default: unlimited)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='json',
                        help='Output format (default: json)')
    parser.add_argument('--interval', type=int, default=10,
                        help='Save interval in pages (default: 10)')
    parser.add_argument('--test', action='store_true',
                        help='Test mode: scrape only 3 pages')

    args = parser.parse_args()

    if args.test:
        args.end = args.start + 2
        print("TEST MODE: Will scrape 3 pages")

    scraper = BGNPPGScraper(output_format=args.format)
    scraper.scrape_range(
        start_page=args.start,
        end_page=args.end,
        save_interval=args.interval
    )


if __name__ == "__main__":
    main()
