#!/usr/bin/env python3
"""
Script to find skipped/missing article IDs in the turnbackhoax CSV file.
Checks each skipped URL to determine the HTTP status code.
Outputs a CSV file with the URLs and their status.

Features:
- Incremental checking: if output CSV exists, only checks new IDs
- Saves progress after each batch of URL checks
"""

import pandas as pd
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set
import argparse


def check_url(article_id: int, base_url: str = "https://turnbackhoax.id/articles/") -> Dict:
    """
    Check a URL and return its status.
    
    Args:
        article_id: The article ID to check
        base_url: The base URL pattern
    
    Returns:
        Dictionary with article_id, url, status_code, and status_description
    """
    url = f"{base_url}{article_id}"
    
    try:
        response = requests.get(url, timeout=30, allow_redirects=True)
        status_code = response.status_code
        
        # Map common status codes to descriptions
        status_descriptions = {
            200: "OK",
            301: "Moved Permanently",
            302: "Found (Redirect)",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            410: "Gone",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
        }
        
        status_description = status_descriptions.get(status_code, f"HTTP {status_code}")
        
    except requests.exceptions.Timeout:
        status_code = 0
        status_description = "Timeout"
    except requests.exceptions.ConnectionError:
        status_code = 0
        status_description = "Connection Error"
    except requests.exceptions.RequestException as e:
        status_code = 0
        status_description = f"Request Error: {str(e)[:50]}"
    
    return {
        "article_id": article_id,
        "url": url,
        "status_code": status_code,
        "status_description": status_description
    }


def check_urls_concurrently(article_ids: List[int], max_workers: int = 5) -> List[Dict]:
    """
    Check multiple URLs concurrently.
    
    Args:
        article_ids: List of article IDs to check
        max_workers: Maximum number of concurrent threads
    
    Returns:
        List of dictionaries with URL status information
    """
    results = []
    total = len(article_ids)
    
    print(f"\nChecking {total} URLs...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_id = {executor.submit(check_url, aid): aid for aid in article_ids}
        
        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_id), 1):
            result = future.result()
            results.append(result)
            
            # Progress update every 5 URLs or at the end
            if i % 5 == 0 or i == total:
                print(f"  Progress: {i}/{total} URLs checked", end="\r")
    
    print()  # New line after progress
    
    # Sort results by article_id
    results.sort(key=lambda x: x["article_id"])
    
    return results


def load_existing_results(output_csv: str) -> Dict[int, Dict]:
    """
    Load existing results from output CSV if it exists.
    
    Args:
        output_csv: Path to the output CSV file
    
    Returns:
        Dictionary mapping article_id to its full record
    """
    output_path = Path(output_csv)
    if not output_path.exists():
        return {}
    
    try:
        df = pd.read_csv(output_csv)
        existing = {}
        for _, row in df.iterrows():
            existing[int(row['article_id'])] = {
                "article_id": int(row['article_id']),
                "url": row['url'],
                "status_code": row['status_code'],
                "status_description": row['status_description']
            }
        return existing
    except Exception as e:
        print(f"Warning: Could not read existing output file: {e}")
        return {}


def find_skipped_ids(input_csv: str, output_csv: str = "skipped_article_ids.csv", check_urls: bool = True):
    """
    Find skipped article IDs in the CSV and output their URLs to a new CSV.
    
    Args:
        input_csv: Path to the input CSV file containing article data
        output_csv: Path to the output CSV file for skipped article URLs
        check_urls: Whether to check each URL for its HTTP status
    """
    print(f"Reading CSV file: {input_csv}")
    
    # Read the CSV file
    df = pd.read_csv(input_csv)
    
    # Get all article IDs from the CSV
    existing_ids = set(df['article_id'].dropna().astype(int))
    
    # Find min and max IDs
    min_id = min(existing_ids)
    max_id = max(existing_ids)
    
    print(f"Total articles in CSV: {len(existing_ids)}")
    print(f"Article ID range: {min_id} to {max_id}")
    print(f"Expected count if sequential: {max_id - min_id + 1}")
    
    # Generate the complete set of IDs that should exist
    expected_ids = set(range(min_id, max_id + 1))
    
    # Find missing/skipped IDs
    skipped_ids = sorted(expected_ids - existing_ids)
    
    print(f"Number of skipped IDs: {len(skipped_ids)}")
    
    if not skipped_ids:
        print("\nNo skipped IDs found! All IDs are sequential.")
        return skipped_ids
    
    # Load existing results from output file
    existing_results = load_existing_results(output_csv)
    
    if existing_results:
        print(f"\nFound existing output file with {len(existing_results)} records")
    
    # Determine which IDs need to be checked
    already_checked_ids = set(existing_results.keys())
    new_ids_to_check = [aid for aid in skipped_ids if aid not in already_checked_ids]
    
    # IDs that were previously in output but are now scraped (no longer skipped)
    ids_now_scraped = already_checked_ids - set(skipped_ids)
    if ids_now_scraped:
        print(f"Removing {len(ids_now_scraped)} IDs that are now in the main CSV")
        for aid in ids_now_scraped:
            del existing_results[aid]
    
    print(f"IDs already checked: {len(already_checked_ids & set(skipped_ids))}")
    print(f"New IDs to check: {len(new_ids_to_check)}")
    
    # Prepare final data
    skipped_data = []
    
    # Add existing results for IDs that are still skipped
    for aid in skipped_ids:
        if aid in existing_results:
            skipped_data.append(existing_results[aid])
    
    # Check new URLs if requested
    if check_urls and new_ids_to_check:
        new_results = check_urls_concurrently(new_ids_to_check)
        skipped_data.extend(new_results)
    elif not check_urls and new_ids_to_check:
        # Just create URLs without checking
        base_url = "https://turnbackhoax.id/articles/"
        for article_id in new_ids_to_check:
            skipped_data.append({
                "article_id": article_id,
                "url": f"{base_url}{article_id}",
                "status_code": "",
                "status_description": "Not checked"
            })
    
    # Sort by article_id
    skipped_data.sort(key=lambda x: x["article_id"])
    
    # Save to CSV
    skipped_df = pd.DataFrame(skipped_data)
    skipped_df.to_csv(output_csv, index=False)
    
    print(f"\nSkipped IDs saved to: {output_csv}")
    
    # Print summary of status codes
    print("\n--- Status Summary ---")
    status_counts = {}
    for item in skipped_data:
        desc = str(item.get("status_description", "Unknown"))
        status_counts[desc] = status_counts.get(desc, 0) + 1
    
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")
    
    # Print first 20 skipped IDs
    print(f"\nFirst 20 skipped IDs:")
    for item in skipped_data[:20]:
        status_info = f"[{item['status_code']}] {item['status_description']}"
        print(f"  ID {item['article_id']}: {item['url']} {status_info}")
    
    if len(skipped_data) > 20:
        print(f"\n  ... and {len(skipped_data) - 20} more")
    
    return skipped_ids


def main():
    parser = argparse.ArgumentParser(description="Find skipped article IDs in turnbackhoax CSV")
    parser.add_argument("--no-check", action="store_true", 
                        help="Skip URL checking, only identify skipped IDs")
    parser.add_argument("--input", type=str, default=None,
                        help="Input CSV file path")
    parser.add_argument("--output", type=str, default=None,
                        help="Output CSV file path")
    
    args = parser.parse_args()
    
    # Define input and output paths
    script_dir = Path(__file__).parent
    input_csv = args.input or str(script_dir / "../data/turnbackhoax_articles_by_id.csv")
    output_csv = args.output or str(script_dir / "../data/skipped_article_ids.csv")
    
    # Find and save skipped IDs
    check_urls = not args.no_check
    skipped_ids = find_skipped_ids(input_csv, output_csv, check_urls=check_urls)
    
    print(f"\nComplete! Total skipped IDs: {len(skipped_ids)}")


if __name__ == "__main__":
    main()
