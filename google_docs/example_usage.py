#!/usr/bin/env python3
"""
Example usage of the Google Docs downloader.
This script demonstrates how to download documents from the docs_url.csv file.
"""

import os
import sys

# Add parent directory to path to import the downloader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_docs.google_docs_downloader import GoogleDocsDownloader


def main():
    """Example usage of the Google Docs downloader."""

    # Path to your CSV file (adjust if needed)
    csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs_url.csv')

    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found at {csv_file}")
        print("Make sure docs_url.csv is in the parent directory.")
        return 1

    print("Google Docs to Markdown Downloader")
    print("=" * 40)
    print(f"CSV file: {csv_file}")
    print()

    # Initialize the downloader
    downloader = GoogleDocsDownloader()

    try:
        # Download all documents
        # This will:
        # 1. Authenticate with Google (first time only)
        # 2. Parse the CSV file
        # 3. Download each document as plain text
        # 4. Convert to markdown
        # 5. Save files to 'downloads/' directory
        successful_downloads = downloader.download_all_documents(
            csv_file=csv_file,
            output_dir='downloads',  # Change this to your preferred output directory
            delay=2  # 2 second delay between downloads (be respectful to Google's API)
        )

        print(f"\nDownloaded {len(successful_downloads)} documents successfully!")

        return 0

    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
