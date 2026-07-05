import csv
import json
import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

class SismonBGNScraper:
    def __init__(self, url: str = "https://www.sismonbgn.com/data", output_dir: str = "output"):
        self.url = url
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
    def fetch_page(self) -> str:
        """Fetches the HTML content from the URL."""
        print(f"Fetching data from {self.url}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(self.url, headers=headers)
        response.raise_for_status()
        
        return response.text
        
    def parse_data(self, html: str) -> tuple[List[str], List[Dict[str, str]]]:
        """Parses the HTML and extracts the table headers and rows."""
        print("Parsing HTML content...")
        soup = BeautifulSoup(html, 'html.parser')
        
        table = soup.find('table')
        if not table:
            raise ValueError("No table found on the page.")
            
        # Extract headers
        thead = table.find('thead')
        if thead:
            headers = [th.get_text(strip=True) for th in thead.find_all('th')]
        else:
            # Fallback if no thead
            headers = [th.get_text(strip=True) for th in table.find('tr').find_all('th')]
            
        print(f"Found headers: {headers}")
        
        # Extract rows
        tbody = table.find('tbody')
        if not tbody:
            raise ValueError("No tbody found in the table.")
            
        rows = tbody.find_all('tr')
        parsed_data = []
        
        for idx, row in enumerate(rows):
            cells = row.find_all('td')
            # Make sure the row has the same number of cells as headers
            if len(cells) == len(headers):
                row_data = {headers[i]: cells[i].get_text(strip=True) for i in range(len(headers))}
                parsed_data.append(row_data)
                
            if (idx + 1) % 1000 == 0:
                print(f"Parsed {idx + 1} rows...")
                
        print(f"Successfully parsed {len(parsed_data)} rows.")
        return headers, parsed_data

    def save_to_csv(self, headers: List[str], data: List[Dict[str, str]], filename: str = "sismon_data.csv"):
        """Saves the parsed data to a CSV file."""
        filepath = os.path.join(self.output_dir, filename)
        print(f"Saving to {filepath}...")
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
            
        print("CSV save complete.")
        
    def save_to_json(self, data: List[Dict[str, str]], filename: str = "sismon_data.json"):
        """Saves the parsed data to a JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        print(f"Saving to {filepath}...")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("JSON save complete.")
        
    def run(self, save_csv: bool = True, save_json: bool = True):
        """Runs the full scraping process."""
        try:
            html = self.fetch_page()
            headers, data = self.parse_data(html)
            
            if not data:
                print("No data found to save.")
                return
                
            if save_csv:
                self.save_to_csv(headers, data)
                
            if save_json:
                self.save_to_json(data)
                
            print("Done!")
            
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape data from sismonbgn.com")
    parser.add_argument('--no-csv', action='store_true', help="Don't save to CSV")
    parser.add_argument('--no-json', action='store_true', help="Don't save to JSON")
    
    args = parser.parse_args()
    
    scraper = SismonBGNScraper()
    scraper.run(save_csv=not args.no_csv, save_json=not args.no_json)
