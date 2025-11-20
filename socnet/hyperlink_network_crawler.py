#!/usr/bin/env python3
"""
Hyperlink Network Crawler
Crawls hyperlinks from a list of URLs and generates network analysis data.

Output format: Source, Target, Weight, Label
- Source: The URL being crawled
- Target: The hyperlink found on the source page
- Weight: Number of times the link appears on the source page
- Label: Anchor text or context of the hyperlink
"""

import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import time
import sys


class HyperlinkNetworkCrawler:
    def __init__(self, input_file, output_file='hyperlink_network.csv', delay=1):
        """
        Initialize the crawler.
        
        Args:
            input_file: CSV file containing Actor,URL columns
            output_file: Output CSV file for network data
            delay: Delay between requests in seconds (default: 1)
        """
        self.input_file = input_file
        self.output_file = output_file
        self.delay = delay
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 10
        
    def normalize_url(self, url):
        """Normalize URL by removing trailing slashes and fragments."""
        parsed = urlparse(url)
        # Remove fragment and trailing slash
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized
    
    def is_valid_url(self, url):
        """Check if URL is valid and not a file/mailto/javascript link."""
        parsed = urlparse(url)
        invalid_schemes = ['mailto', 'javascript', 'tel', 'ftp']
        file_extensions = ['.pdf', '.doc', '.docx', '.zip', '.jpg', '.png', '.gif', '.mp4']
        
        if parsed.scheme in invalid_schemes:
            return False
        
        if any(url.lower().endswith(ext) for ext in file_extensions):
            return False
            
        return parsed.scheme in ['http', 'https']
    
    def extract_hyperlinks(self, source_url):
        """
        Extract all hyperlinks from a given URL.
        
        Returns:
            dict: {target_url: [(anchor_text1, anchor_text2, ...)]}
        """
        print(f"\n🔍 Crawling: {source_url}")
        
        try:
            response = requests.get(source_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all anchor tags
            links = soup.find_all('a', href=True)
            
            # Dictionary to store links and their anchor texts
            link_data = defaultdict(list)
            
            for link in links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Convert relative URLs to absolute
                absolute_url = urljoin(source_url, href)
                
                # Normalize and validate
                normalized_url = self.normalize_url(absolute_url)
                
                if not self.is_valid_url(normalized_url):
                    continue
                
                # Extract anchor text
                anchor_text = link.get_text(strip=True)
                if not anchor_text:
                    # Try to get title or aria-label as fallback
                    anchor_text = link.get('title', '') or link.get('aria-label', '') or 'No text'
                
                # Limit anchor text length
                if len(anchor_text) > 100:
                    anchor_text = anchor_text[:97] + '...'
                
                link_data[normalized_url].append(anchor_text)
            
            print(f"✅ Found {len(links)} total links, {len(link_data)} unique links")
            return link_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error crawling {source_url}: {e}")
            return {}
        except Exception as e:
            print(f"❌ Unexpected error crawling {source_url}: {e}")
            return {}
    
    def crawl_all(self):
        """
        Crawl all URLs from input file and generate network data.
        """
        print("=" * 60)
        print("🕸️  Hyperlink Network Crawler")
        print("=" * 60)
        
        # Read input URLs
        urls_to_crawl = []
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'URL' in row:
                        urls_to_crawl.append(row['URL'].strip())
        except Exception as e:
            print(f"❌ Error reading input file: {e}")
            sys.exit(1)
        
        print(f"\n📋 Found {len(urls_to_crawl)} URLs to crawl")
        
        # Collect all network edges
        network_edges = []
        
        # Crawl each URL
        for idx, source_url in enumerate(urls_to_crawl, 1):
            print(f"\n[{idx}/{len(urls_to_crawl)}]")
            
            link_data = self.extract_hyperlinks(source_url)
            
            # Create edges for each unique target URL
            for target_url, anchor_texts in link_data.items():
                weight = len(anchor_texts)
                # Use the most common anchor text or combine them
                label = anchor_texts[0] if anchor_texts else "No label"
                
                # If there are multiple different anchor texts, combine them
                unique_anchors = list(set(anchor_texts))
                if len(unique_anchors) > 1:
                    label = " | ".join(unique_anchors[:3])  # Max 3 labels
                    if len(label) > 150:
                        label = label[:147] + "..."
                
                network_edges.append({
                    'Source': source_url,
                    'Target': target_url,
                    'Weight': weight,
                    'Label': label
                })
            
            # Respectful delay between requests
            if idx < len(urls_to_crawl):
                time.sleep(self.delay)
        
        # Write results to CSV
        self.write_output(network_edges)
        
        return network_edges
    
    def write_output(self, network_edges):
        """Write network edges to CSV file."""
        if not network_edges:
            print("\n⚠️  No network edges found. No output file created.")
            return
        
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['Source', 'Target', 'Weight', 'Label']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(network_edges)
            
            print("\n" + "=" * 60)
            print(f"✅ SUCCESS! Network data saved to: {self.output_file}")
            print(f"📊 Total edges: {len(network_edges)}")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error writing output file: {e}")
            sys.exit(1)


def main():
    """Main function to run the crawler."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Crawl hyperlinks from URLs and generate network analysis data.'
    )
    parser.add_argument(
        '-i', '--input',
        default='url_input.txt',
        help='Input CSV file with URLs (default: url_input.txt)'
    )
    parser.add_argument(
        '-o', '--output',
        default='hyperlink_network.csv',
        help='Output CSV file for network data (default: hyperlink_network.csv)'
    )
    parser.add_argument(
        '-d', '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    # Create and run crawler
    crawler = HyperlinkNetworkCrawler(
        input_file=args.input,
        output_file=args.output,
        delay=args.delay
    )
    
    crawler.crawl_all()


if __name__ == '__main__':
    main()

