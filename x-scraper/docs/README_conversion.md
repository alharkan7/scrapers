# JSON to CSV Converter for X (Twitter) Scraper Data

This script converts the JSON output from the X scraper into CSV format for easier analysis and processing.

## Usage

```bash
python3 convert_json_to_csv.py <input_json_file> <output_csv_file>
```

## Example

```bash
python3 convert_json_to_csv.py output/search_Makan_Bergizi_Gratis.json output/search_Makan_Bergizi_Gratis.csv
```

## CSV Structure

The CSV file contains the following columns:

- `id`: Tweet ID
- `url`: Tweet URL
- `date`: Tweet date (ISO format)
- `content`: Tweet text content
- `username`: Twitter username
- `display_name`: Display name
- `user_id`: User ID
- `verified`: Verification status (true/false)
- `followers_count`: Number of followers
- `following_count`: Number of following
- `reply_count`: Number of replies
- `retweet_count`: Number of retweets
- `like_count`: Number of likes
- `quote_count`: Number of quotes
- `view_count`: Number of views
- `lang`: Language code
- `source`: Tweet source (e.g., "Twitter for iPhone")
- `hashtags`: Hashtags (semicolon-separated)
- `mentioned_users`: Mentioned users (semicolon-separated)
- `links`: Links with text (format: "text: url; text: url")
- `media`: Media information (format: "type: url (alt); type: url (alt)")

## Notes

- Array fields (hashtags, mentioned_users, links, media) are flattened into semicolon-separated strings
- Nested objects in links and media arrays are converted to readable string format
- Multi-line content in tweets is properly handled with CSV quoting
- The script handles UTF-8 encoding for international characters
