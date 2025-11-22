# Google Docs to Markdown Downloader

This script downloads Google Docs from a CSV file and converts them to Markdown format.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Cloud Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Docs API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Docs API" and enable it

4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Select "Desktop application" as the application type
   - Download the credentials file (usually named `client_secret_*.json`) and place it in the `google_docs/` directory

### 3. Prepare Your CSV File

Your CSV file should have at least two columns:
- `ID`: A unique identifier for each document
- `URL`: The Google Docs URL

Example CSV format:
```csv
ID,URL
202310040311042,https://docs.google.com/document/d/1LWFVmL9HR-pQglcPwX6DchAp_0AaozlD/edit?usp=drivesdk&ouid=...
202310040311044,https://docs.google.com/document/d/1temB1bSqRGv_ZlokG_NbnAOwpz7WdW_wy8-93_gc638/edit?usp=sharing
```

## Usage

### Basic Usage

```bash
python google_docs_downloader.py docs_url.csv
```

This will:
- Download all documents from the CSV file
- Convert them to Markdown format
- Save them in a `downloads/` directory
- Create a summary file `downloads/download_summary.json`

### Advanced Usage

```bash
# Specify output directory
python google_docs_downloader.py docs_url.csv --output my_documents

# Use custom credentials file (if script doesn't find it automatically)
python google_docs_downloader.py docs_url.csv --credentials google_docs/client_secret_xxx.json

# Add delay between downloads (to be respectful to Google's API)
python google_docs_downloader.py docs_url.csv --delay 2
```

### Command Line Options

- `csv_file`: Path to your CSV file (required)
- `--output`, `-o`: Output directory for markdown files (default: `downloads`)
- `--credentials`: Path to Google API credentials.json file (default: `credentials.json`)
- `--token`: Path to OAuth token file (default: `token.pickle`)
- `--delay`: Delay between downloads in seconds (default: 1)

## Authentication

On the first run, the script will:
1. Open a browser window
2. Ask you to sign in with your Google account (raihankalla@gmail.com)
3. Request permission to access your Google Docs
4. Save an authentication token for future use

The token is saved as `token.pickle` and will be reused in subsequent runs.

## Output

The script creates:
- **Markdown files**: One `.md` file per document in the output directory
- **Summary file**: `download_summary.json` with details about successful and failed downloads
- **Plain text files**: Temporary `.txt` files (can be deleted after conversion)

## Troubleshooting

### Common Issues

1. **"credentials.json not found"**
   - Make sure you've downloaded the credentials file from Google Cloud Console
   - Place it in the correct location or specify the path with `--credentials`

2. **Authentication errors**
   - Delete `token.pickle` and re-run to re-authenticate
   - Make sure you're signed in with the correct Google account

3. **Permission denied**
   - Ensure you have access to all the documents in the CSV file
   - The account must be able to view all documents

4. **API quota exceeded**
   - Google has API limits; add longer delays with `--delay`
   - Wait a few hours before retrying

### File Structure

```
google_docs/
├── google_docs_downloader.py  # Main script
├── README.md                  # This file
├── credentials.json          # Google API credentials (you provide)
└── token.pickle              # OAuth token (created automatically)
```

## CSV File Format

The script expects a CSV file with headers. The URL column should contain valid Google Docs URLs. The script will automatically extract document IDs from URLs matching these patterns:

- `https://docs.google.com/document/d/DOCUMENT_ID/edit?...`
- `https://docs.google.com/document/d/DOCUMENT_ID/...`

Invalid URLs will be skipped with a warning message.
