#!/usr/bin/env python3
"""
Data cleansing script for goodnews_id_details.jsonl
Cleans article data by removing CTAs, splitting date/time, and cleaning URLs
"""

import json
import os
from pathlib import Path


def clean_article_content(content: str) -> str:
    """
    Remove CTA phrase and strip trailing newlines from article content.

    Args:
        content: Original article content

    Returns:
        Cleaned article content
    """
    if not content:
        return content

    # Remove CTA phrase (using actual newline characters, not escaped)
    cta_phrase = "\nCek berita, artikel, dan konten yang lain di\nGoogle News"
    content = content.replace(cta_phrase, "")

    # Strip trailing newlines
    content = content.rstrip("\n")

    return content


def split_datetime(date_time: str) -> tuple[str, str]:
    """
    Split date_time field into separate date and time fields.

    Args:
        date_time: Original datetime string like "31 Desember 2025 11.00 WIB • 2 menit"

    Returns:
        Tuple of (date, time) like ("31 Desember 2025", "11.00 WIB")
    """
    if not date_time:
        return "", ""

    # Split by " • " to separate datetime from reading length
    parts = date_time.split(" • ")

    # The first part should be "DD Month YYYY HH.MM WIB"
    datetime_part = parts[0].strip()

    # Find the time part (last space-separated portion before the split)
    # Format is "DD Month YYYY HH.MM WIB"
    # We need to split after the date part
    time_parts = datetime_part.rsplit(maxsplit=2)  # Split into max 3 parts from right
    # time_parts should be like ["31 Desember 2025", "11.00", "WIB"]

    if len(time_parts) >= 3:
        date = " ".join(time_parts[:-2])  # Everything except last 2 parts
        time = " ".join(time_parts[-2:])   # Last 2 parts: time and WIB
        return date, time

    # Fallback: return original as date, empty as time
    return datetime_part, ""


def clean_cover_image_url(url: str) -> str:
    """
    Remove URL parameters from cover_image_url.

    Args:
        url: Original URL with possible query parameters

    Returns:
        Cleaned URL without parameters
    """
    if not url:
        return url

    # Remove everything after ?
    return url.split("?")[0]


def clean_article(article: dict) -> dict:
    """
    Apply all cleansing transformations to a single article.

    Args:
        article: Original article dictionary

    Returns:
        Cleansed article dictionary
    """
    cleaned = article.copy()

    # Clean article content
    cleaned["full_article_content"] = clean_article_content(
        article.get("full_article_content", "")
    )

    # Split date_time into date and time
    date_time = article.get("date_time", "")
    date, time = split_datetime(date_time)
    cleaned["date"] = date
    cleaned["time"] = time

    # Remove old date_time field
    if "date_time" in cleaned:
        del cleaned["date_time"]

    # Clean cover_image_url
    cleaned["cover_image_url"] = clean_cover_image_url(
        article.get("cover_image_url", "")
    )

    return cleaned


def main():
    """Main function to process the JSONL file."""

    # File paths
    input_file = Path("goodnews_id/data/goodnews_id_details.jsonl")
    output_file = Path("goodnews_id/data/goodnews_id_details_cleaned.jsonl")
    backup_file = Path("goodnews_id/data/goodnews_id_details_backup.jsonl")

    # Check if input file exists
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return

    # Counters for statistics
    total_articles = 0
    cleaned_articles = 0
    cta_removed = 0
    content_stripped = 0
    url_cleaned = 0

    print(f"Processing: {input_file}")
    print(f"Output to: {output_file}")
    print()

    # Process each line
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            line = line.strip()
            if not line:
                continue

            try:
                article = json.loads(line)
                total_articles += 1

                # Store original values for statistics
                original_content = article.get("full_article_content", "")
                original_url = article.get("cover_image_url", "")
                original_datetime = article.get("date_time", "")

                # Clean the article
                cleaned_article = clean_article(article)

                # Track statistics
                cta_phrase = "\nCek berita, artikel, dan konten yang lain di\nGoogle News"
                if cta_phrase in original_content:
                    cta_removed += 1

                if original_content.endswith("\n"):
                    content_stripped += 1

                if "?" in original_url:
                    url_cleaned += 1

                # Write cleaned article to output file
                outfile.write(json.dumps(cleaned_article, ensure_ascii=False) + "\n")
                cleaned_articles += 1

            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {total_articles + 1}: {e}")
                continue

    # Print statistics
    print("=" * 60)
    print("Cleansing Complete!")
    print("=" * 60)
    print(f"Total articles processed: {total_articles}")
    print(f"Articles successfully cleaned: {cleaned_articles}")
    print()
    print("Transformations applied:")
    print(f"  - CTA phrase removed: {cta_removed} articles")
    print(f"  - Trailing newlines stripped: {content_stripped} articles")
    print(f"  - Cover image URLs cleaned: {url_cleaned} articles")
    print(f"  - Date/time split: {cleaned_articles} articles")
    print()
    print(f"Output saved to: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
