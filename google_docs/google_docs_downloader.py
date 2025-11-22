#!/usr/bin/env python3
"""
Google Docs to Markdown Downloader.
Downloads Google Docs from a CSV file containing URLs and converts them to Markdown format.
"""

import csv
import os
import re
import json
import argparse
import time
from datetime import datetime
from pathlib import Path
import pickle

# Google API imports
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class GoogleDocsDownloader:
    def __init__(self, credentials_path=None, token_path=None):
        """
        Initialize the Google Docs downloader.

        Parameters:
        - credentials_path (str): Path to the client_secret_*.json file from Google Cloud Console
        - token_path (str): Path to store/retrieve the OAuth token
        """
        # Look for credentials.json first, then client_secret_*.json files
        if not credentials_path:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # Look in the script directory first
            creds_in_script_dir = os.path.join(script_dir, 'credentials.json')
            if os.path.exists(creds_in_script_dir):
                credentials_path = creds_in_script_dir
            else:
                # Look for client_secret_*.json files in script directory
                import glob
                client_secret_pattern = os.path.join(script_dir, 'client_secret_*.json')
                client_secret_files = glob.glob(client_secret_pattern)
                if client_secret_files:
                    credentials_path = client_secret_files[0]  # Use the first one found
                    print(f"Found credentials file: {os.path.basename(credentials_path)}")
                else:
                    # As a fallback, look in current directory
                    if os.path.exists('credentials.json'):
                        credentials_path = 'credentials.json'
                    else:
                        client_secret_files = glob.glob('client_secret_*.json')
                        if client_secret_files:
                            credentials_path = client_secret_files[0]
                        else:
                            credentials_path = 'credentials.json'  # Default fallback

        self.credentials_path = credentials_path
        self.token_path = token_path or 'token.pickle'
        self.service = None
        self.scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']

    def authenticate(self):
        """Authenticate with Google Docs API using OAuth2."""
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file '{self.credentials_path}' not found. "
                        "Please download it from Google Cloud Console and place it in the current directory."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        # Build the service (use Drive API for exporting)
        self.service = build('drive', 'v3', credentials=creds)
        print("✓ Successfully authenticated with Google Docs API")

    def extract_doc_id(self, url):
        """
        Extract document ID from Google Docs URL.

        Parameters:
        - url (str): Google Docs URL

        Returns:
        - str: Document ID or None if not found
        """
        # Match patterns like:
        # https://docs.google.com/document/d/DOC_ID/edit?...
        # https://docs.google.com/document/d/DOC_ID/...
        pattern = r'/document/d/([a-zA-Z0-9_-]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None

    def load_csv_urls(self, csv_file):
        """
        Load URLs from CSV file.

        Parameters:
        - csv_file (str): Path to CSV file with ID and URL columns

        Returns:
        - list: List of dictionaries with 'id' and 'url' keys
        """
        documents = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Try both 'NPM' and 'ID' column names
                    npm_id = row.get('NPM', row.get('ID', '')).strip()
                    url = row.get('URL', '').strip()

                    # Remove quotes if present
                    url = url.strip('"')

                    if url and url.startswith('https://docs.google.com/document/'):
                        documents.append({
                            'id': npm_id,
                            'url': url,
                            'doc_id': self.extract_doc_id(url)
                        })
                    else:
                        print(f"Warning: Skipping invalid URL: {url}")

        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file '{csv_file}' not found.")
        except Exception as e:
            raise Exception(f"Error reading CSV file: {e}")

        return documents

    def download_document(self, doc_id, output_dir='downloads'):
        """
        Download a Google Doc as plain text using Drive API.

        Parameters:
        - doc_id (str): Google Document ID
        - output_dir (str): Directory to save the downloaded content

        Returns:
        - dict: Document metadata and content
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")

        try:
            # Get document metadata first to get the title
            doc_metadata = self.service.files().get(fileId=doc_id, fields='name').execute()
            title = doc_metadata.get('name', f'untitled_{doc_id}')
            print(f"Downloading: {title}")

            # Export as plain text using Drive API
            request = self.service.files().export_media(
                fileId=doc_id,
                mimeType='text/plain'
            )

            # Get the content
            content = request.execute()

            # Clean up the title for filename
            safe_title = re.sub(r'[^\w\-_\.]', '_', title)
            safe_title = safe_title[:100]  # Limit length

            # Create output directory
            Path(output_dir).mkdir(exist_ok=True)

            # Handle content encoding (don't save .txt file, just keep in memory)
            if isinstance(content, bytes):
                text_content = content.decode('utf-8', errors='replace')
            else:
                text_content = str(content)

            return {
                'doc_id': doc_id,
                'title': title,
                'content': text_content
            }

        except Exception as e:
            print(f"Error downloading document {doc_id}: {e}")
            return None

    def convert_text_to_markdown(self, text_content, title=""):
        """
        Convert plain text content to basic markdown format.

        Parameters:
        - text_content (str): Plain text content
        - title (str): Document title

        Returns:
        - str: Markdown formatted content
        """
        lines = text_content.split('\n')
        markdown_lines = []

        # Add title as header
        if title:
            markdown_lines.append(f"# {title}")
            markdown_lines.append("")

        in_list = False
        in_code_block = False

        for line in lines:
            line = line.rstrip()
            if not line:
                # Empty line
                markdown_lines.append("")
                in_list = False
                continue

            # Check for code blocks (basic detection)
            if line.startswith('```') or line.startswith('    ') or line.startswith('\t'):
                if not in_code_block:
                    markdown_lines.append("```")
                    in_code_block = True
                markdown_lines.append(line.strip())
            elif in_code_block:
                markdown_lines.append("```")
                markdown_lines.append("")
                in_code_block = False
                # Re-process the current line
                continue

            # Check for headers (lines that are all caps or have specific patterns)
            elif line.isupper() and len(line) > 10:
                markdown_lines.append(f"## {line.title()}")
                in_list = False

            # Check for list items
            elif re.match(r'^\s*[\-\*\+]\s+', line) or re.match(r'^\s*\d+\.\s+', line):
                markdown_lines.append(line)
                in_list = True

            # Check for potential headers (short lines followed by content)
            elif len(line) < 80 and not in_list and len(lines) > 1:
                # Look ahead to see if next line has content
                next_idx = len(markdown_lines) + 1
                if next_idx < len(lines) and lines[next_idx].strip():
                    markdown_lines.append(f"## {line}")
                    in_list = False
                else:
                    markdown_lines.append(line)

            else:
                # Regular paragraph
                markdown_lines.append(line)
                in_list = False

        # Close any open code block
        if in_code_block:
            markdown_lines.append("```")

        return '\n'.join(markdown_lines)

    def save_as_markdown(self, doc_data, output_dir='downloads', filename=None):
        """
        Save document content as markdown file.

        Parameters:
        - doc_data (dict): Document data from download_document
        - output_dir (str): Output directory
        - filename (str): Custom filename (optional, will use doc_id if not provided)
        """
        if not doc_data or 'content' not in doc_data:
            return None

        title = doc_data.get('title', f'untitled_{doc_data["doc_id"]}')
        content = doc_data['content']

        # Convert to markdown
        markdown_content = self.convert_text_to_markdown(content, title)

        # Use custom filename if provided, otherwise use document ID
        if filename:
            safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        else:
            safe_filename = doc_data["doc_id"]

        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)

        # Save markdown file
        md_filename = f"{safe_filename}.md"
        md_filepath = os.path.join(output_dir, md_filename)

        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"✓ Saved as markdown: {md_filepath}")
        return md_filepath

    def download_all_documents(self, csv_file, output_dir='downloads', delay=1):
        """
        Download all documents from CSV file as markdown.

        Parameters:
        - csv_file (str): Path to CSV file
        - output_dir (str): Output directory for markdown files
        - delay (int): Delay between downloads in seconds

        Returns:
        - list: List of successfully downloaded documents
        """
        # Load document URLs
        documents = self.load_csv_urls(csv_file)
        if not documents:
            print("No valid documents found in CSV file.")
            return []

        print(f"Found {len(documents)} documents to download.")

        # Authenticate if not already done
        if not self.service:
            self.authenticate()

        successful_downloads = []
        failed_downloads = []

        for i, doc in enumerate(documents, 1):
            doc_id = doc['doc_id']
            original_id = doc['id']
            url = doc['url']

            print(f"\n[{i}/{len(documents)}] Processing document: {original_id}")

            if not doc_id:
                print(f"✗ Could not extract document ID from URL: {url}")
                failed_downloads.append({'id': original_id, 'url': url, 'error': 'Invalid URL'})
                continue

            try:
                # Download document
                doc_data = self.download_document(doc_id, output_dir)

                if doc_data:
                    # Convert and save as markdown using the ID as filename
                    md_file = self.save_as_markdown(doc_data, output_dir, filename=original_id)

                    if md_file:
                        successful_downloads.append({
                            'id': original_id,
                            'doc_id': doc_id,
                            'title': doc_data['title'],
                            'md_file': md_file,
                            'url': url
                        })
                    else:
                        failed_downloads.append({
                            'id': original_id,
                            'url': url,
                            'error': 'Failed to save markdown'
                        })
                else:
                    failed_downloads.append({
                        'id': original_id,
                        'url': url,
                        'error': 'Failed to download'
                    })

            except Exception as e:
                print(f"✗ Error processing document {original_id}: {e}")
                failed_downloads.append({
                    'id': original_id,
                    'url': url,
                    'error': str(e)
                })

            # Add delay between requests
            if delay > 0 and i < len(documents):
                time.sleep(delay)

        # Print summary
        print(f"\n{'='*50}")
        print(f"DOWNLOAD SUMMARY")
        print(f"{'='*50}")
        print(f"Total documents: {len(documents)}")
        print(f"Successful: {len(successful_downloads)}")
        print(f"Failed: {len(failed_downloads)}")

        if successful_downloads:
            print("\nSuccessful downloads:")
            for doc in successful_downloads:
                print(f"  ✓ {doc['id']}: {doc['title']} -> {doc['md_file']}")

        if failed_downloads:
            print("\nFailed downloads:")
            for doc in failed_downloads:
                print(f"  ✗ {doc['id']}: {doc['error']}")

        # Save summary to JSON
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_documents': len(documents),
            'successful': successful_downloads,
            'failed': failed_downloads
        }

        summary_file = os.path.join(output_dir, 'download_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\nSummary saved to: {summary_file}")

        return successful_downloads


def main():
    parser = argparse.ArgumentParser(
        description='Download Google Docs from CSV file and convert to Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python google_docs_downloader.py docs_url.csv
  python google_docs_downloader.py docs_url.csv --output my_docs --delay 2
  python google_docs_downloader.py docs_url.csv --credentials my_credentials.json

Setup:
1. Create a Google Cloud Project at https://console.cloud.google.com/
2. Enable the Google Docs API
3. Create OAuth 2.0 credentials (Desktop application)
4. Download the credentials.json file
5. Run the script - it will open a browser for authentication
        """
    )

    parser.add_argument('csv_file', help='CSV file containing document URLs')
    parser.add_argument(
        '--output', '-o',
        default='downloads',
        help='Output directory for markdown files (default: downloads)'
    )
    parser.add_argument(
        '--credentials',
        default='credentials.json',
        help='Path to Google API credentials.json file (default: credentials.json)'
    )
    parser.add_argument(
        '--token',
        default='token.pickle',
        help='Path to OAuth token file (default: token.pickle)'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=1,
        help='Delay between downloads in seconds (default: 1)'
    )

    args = parser.parse_args()

    # Create downloader
    downloader = GoogleDocsDownloader(
        credentials_path=args.credentials,
        token_path=args.token
    )

    try:
        # Download all documents
        downloader.download_all_documents(
            csv_file=args.csv_file,
            output_dir=args.output,
            delay=args.delay
        )

    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
