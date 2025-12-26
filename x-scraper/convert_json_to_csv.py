#!/usr/bin/env python3
import json
import csv
import sys

def flatten_links(links):
    """Convert links array to a flattened string"""
    if not links:
        return ""
    return "; ".join([f"{link.get('text', '')}: {link.get('url', '')}" for link in links])

def flatten_media(media):
    """Convert media array to a flattened string"""
    if not media:
        return ""
    return "; ".join([f"{m.get('type', '')}: {m.get('url', '')} ({m.get('alt', '')})" for m in media])

def flatten_array(arr):
    """Convert array to a semicolon-separated string"""
    if not arr:
        return ""
    return "; ".join(str(item) for item in arr)

def convert_json_to_csv(json_file, csv_file):
    """Convert JSON array of tweets to CSV format"""

    # Read JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not data:
        print("No data found in JSON file")
        return

    # Get field names from the first item
    # We'll include all fields, handling nested structures
    sample = data[0]

    # Define the CSV columns
    csv_columns = [
        'id', 'url', 'date', 'content', 'username', 'display_name', 'user_id',
        'verified', 'followers_count', 'following_count', 'reply_count',
        'retweet_count', 'like_count', 'quote_count', 'view_count', 'lang',
        'source', 'hashtags', 'mentioned_users', 'links', 'media'
    ]

    # Write to CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()

        for tweet in data:
            # Process each tweet
            row = {}
            for col in csv_columns:
                value = tweet.get(col, '')

                # Handle special cases for arrays and nested objects
                if col == 'hashtags':
                    value = flatten_array(value)
                elif col == 'mentioned_users':
                    value = flatten_array(value)
                elif col == 'links':
                    value = flatten_links(value)
                elif col == 'media':
                    value = flatten_media(value)
                elif col == 'verified':
                    # Convert boolean to string
                    value = str(value).lower()

                row[col] = value

            writer.writerow(row)

    print(f"Successfully converted {len(data)} tweets to CSV: {csv_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_json_to_csv.py <input_json_file> <output_csv_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    csv_file = sys.argv[2]

    convert_json_to_csv(json_file, csv_file)
