#!/usr/bin/env python3
"""
Test script for CSV parsing functionality.
"""

import os
import sys
import csv
import tempfile

# Add parent directory to path to import the downloader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_docs.google_docs_downloader import GoogleDocsDownloader


def create_test_csv():
    """Create a test CSV file with sample data."""
    test_data = [
        ["ID", "URL"],
        ["test1", "https://docs.google.com/document/d/1LWFVmL9HR-pQglcPwX6DchAp_0AaozlD/edit?usp=drivesdk"],
        ["test2", "https://docs.google.com/document/d/1temB1bSqRGv_ZlokG_NbnAOwpz7WdW_wy8-93_gc638/edit?usp=sharing"],
        ["test3", "https://docs.google.com/document/d/1RUaw6pQ-_3JCuitube9VmkwYcpUfFZXur1uvfJxfSc0/edit?usp=sharing"],
        ["invalid", "https://example.com/not-a-google-doc"],
        ["quoted", '"https://docs.google.com/document/d/1NTTk-KPnkG_XXkOigLEPz2s_57iV3aLi-sBA5GPH5DE/edit?tab=t.2juyi8y0te7f"']
    ]

    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(test_data)
        return f.name


def test_csv_parsing():
    """Test the CSV parsing functionality."""
    print("Testing CSV parsing functionality...")

    # Create test CSV
    csv_file = create_test_csv()
    print(f"Created test CSV: {csv_file}")

    try:
        # Initialize downloader
        downloader = GoogleDocsDownloader()

        # Test CSV loading
        documents = downloader.load_csv_urls(csv_file)

        print(f"\nLoaded {len(documents)} documents from CSV:")

        expected_doc_ids = [
            "1LWFVmL9HR-pQglcPwX6DchAp_0AaozlD",
            "1temB1bSqRGv_ZlokG_NbnAOwpz7WdW_wy8-93_gc638",
            "1RUaw6pQ-_3JCuitube9VmkwYcpUfFZXur1uvfJxfSc0",
            "1NTTk-KPnkG_XXkOigLEPz2s_57iV3aLi-sBA5GPH5DE"
        ]

        for i, doc in enumerate(documents):
            print(f"  {i+1}. ID: {doc['id']}, Doc ID: {doc['doc_id']}")
            if doc['doc_id'] in expected_doc_ids:
                print("     ✓ Valid Google Docs URL")
            else:
                print("     ✗ Unexpected document ID")

        # Verify we got the expected number of valid documents
        valid_docs = [doc for doc in documents if doc['doc_id'] in expected_doc_ids]
        if len(valid_docs) == 4:
            print(f"\n✓ SUCCESS: Parsed {len(valid_docs)} valid Google Docs URLs")
        else:
            print(f"\n✗ FAILURE: Expected 4 valid documents, got {len(valid_docs)}")

        # Test URL extraction
        test_urls = [
            ("https://docs.google.com/document/d/1abc123/edit", "1abc123"),
            ("https://docs.google.com/document/d/1def456/view", "1def456"),
            ("https://docs.google.com/document/d/1ghi789/edit?usp=sharing", "1ghi789"),
            ("https://example.com/not-google", None),
        ]

        print("\nTesting URL extraction:")
        for url, expected in test_urls:
            result = downloader.extract_doc_id(url)
            status = "✓" if result == expected else "✗"
            print(f"  {status} '{url}' -> '{result}' (expected: '{expected}')")

    finally:
        # Clean up
        os.unlink(csv_file)
        print(f"\nCleaned up test file: {csv_file}")


if __name__ == "__main__":
    test_csv_parsing()
