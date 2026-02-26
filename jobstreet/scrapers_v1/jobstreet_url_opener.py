#!/usr/bin/env python3
"""
JobStreet URL Browser Opener - DEMO/SIMULATION VERSION
Opens job URLs from CSV in browser for video recording purposes.

Author: Research Assistant
Date: February 2026
"""

import csv
import time
import logging
from pathlib import Path
from typing import List, Optional
from playwright.sync_api import sync_playwright, Page, Browser

# =============================================================================
# CONFIGURATION
# =============================================================================

# Input file
INPUT_FILE = "job_vacancies/data/jobstreet_vacancies.csv"

# Browser settings
HEADLESS_MODE = False  # Show browser window
BROWSER_VIEWPORT_WIDTH = 1920
BROWSER_VIEWPORT_HEIGHT = 1080
BROWSER_LOCALE = "id-ID"
BROWSER_TIMEZONE = "Asia/Jakarta"
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"

# Navigation settings
PAGE_LOAD_TIMEOUT = 30000  # milliseconds
PAGE_WAIT_TIME = 2.0  # seconds to wait after page load
URL_DELAY = 0.5  # seconds between URLs

# Video recording settings
SCROLL_DELAY = 0.5  # seconds to wait between scroll actions

# Scraping limits
MAX_URLS = None  # Maximum number of URLs to open (None = all URLs)

# =============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class URLOpener:
    """
    Opens URLs from CSV in browser for demo/video purposes.
    """

    BASE_URL = "https://id.jobstreet.com"

    def __init__(
        self,
        input_file: str = None,
        headless: bool = None,
        max_urls: int = None,
        page_load_timeout: int = None,
        page_wait_time: float = None,
        url_delay: float = None,
    ):
        """Initialize the URL opener."""
        self.input_file = Path(input_file if input_file is not None else INPUT_FILE)
        self.headless = headless if headless is not None else HEADLESS_MODE
        self.max_urls = max_urls if max_urls is not None else MAX_URLS
        self.page_load_timeout = (
            page_load_timeout if page_load_timeout is not None else PAGE_LOAD_TIMEOUT
        )
        self.page_wait_time = (
            page_wait_time if page_wait_time is not None else PAGE_WAIT_TIME
        )
        self.url_delay = url_delay if url_delay is not None else URL_DELAY

        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # Session statistics
        self.session_stats = {
            "urls_opened": 0,
            "urls_failed": 0,
            "total_time": 0,
        }

        logger.info(f"URL opener initialized. Input: {self.input_file}")
        logger.info(f"Max URLs: {self.max_urls if self.max_urls else 'All'}")

    def _load_urls(self) -> List[str]:
        """Load job URLs from input CSV."""
        urls = []

        if not self.input_file.exists():
            logger.error(f"Input file not found: {self.input_file}")
            return urls

        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    job_url = row.get("job_url", "").strip()
                    # Skip invalid URLs (must be a valid JobStreet URL pattern)
                    if job_url and (
                        "jobstreet.com" in job_url or job_url.startswith("/job/")
                    ):
                        # Clean URL
                        if "?" in job_url:
                            job_url = job_url.split("?")[0]
                        if job_url.startswith("/"):
                            job_url = f"{self.BASE_URL}{job_url}"
                        urls.append(job_url)

            logger.info(f"Loaded {len(urls)} valid URLs from {self.input_file}")
        except Exception as e:
            logger.error(f"Error loading URLs from CSV: {e}")

        return urls

        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    job_url = row.get("job_url", "").strip()
                    # Skip invalid URLs (must be a valid URL pattern)
                    if job_url and (
                        job_url.startswith("http") or job_url.startswith("/")
                    ):
                        # Clean URL
                        if "?" in job_url:
                            job_url = job_url.split("?")[0]
                        if job_url.startswith("/"):
                            job_url = f"{self.BASE_URL}{job_url}"
                        urls.append(job_url)

            logger.info(f"Loaded {len(urls)} valid URLs from {self.input_file}")
        except Exception as e:
            logger.error(f"Error loading URLs from CSV: {e}")

        return urls

    def open_urls(self) -> None:
        """Open URLs one by one in browser."""
        urls = self._load_urls()

        if not urls:
            logger.error("No URLs to open!")
            return

        if self.max_urls and self.max_urls < len(urls):
            urls = urls[: self.max_urls]
            logger.info(f"Limiting to {self.max_urls} URLs")

        logger.info(f"Opening {len(urls)} URLs in browser...")
        logger.info(f"Delay between URLs: {self.url_delay}s")
        logger.info(f"Wait after page load: {self.page_wait_time}s")

        start_time = time.time()

        try:
            with sync_playwright() as p:
                # Launch browser once
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-infobars",
                    ],
                    ignore_default_args=["--enable-automation"],
                )

                context = browser.new_context(
                    viewport={
                        "width": BROWSER_VIEWPORT_WIDTH,
                        "height": BROWSER_VIEWPORT_HEIGHT,
                    },
                    user_agent=BROWSER_USER_AGENT,
                    locale=BROWSER_LOCALE,
                    timezone_id=BROWSER_TIMEZONE,
                    extra_http_headers={
                        "Accept-Language": f"{BROWSER_LOCALE},id;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="143", "Chromium";v="143"',
                        "Sec-Ch-Ua-Mobile": "?0",
                        "Sec-Ch-Ua-Platform": '"macOS"',
                    },
                )

                page = context.new_page()

                try:
                    # Visit main page first
                    logger.info("Establishing session...")
                    page.goto(
                        self.BASE_URL,
                        wait_until="domcontentloaded",
                        timeout=self.page_load_timeout,
                    )
                    time.sleep(self.page_wait_time)

                    # Open each URL
                    for i, url in enumerate(urls, 1):
                        logger.info(f"[{i}/{len(urls)}] Opening: {url}")

                        try:
                            url_start_time = time.time()

                            # Navigate to job URL
                            page.goto(
                                url,
                                wait_until="domcontentloaded",
                                timeout=self.page_load_timeout,
                            )
                            time.sleep(self.page_wait_time)

                            # Scroll down for visual effect
                            try:
                                page.evaluate(
                                    "window.scrollTo(0, document.body.scrollHeight / 3)"
                                )
                                time.sleep(SCROLL_DELAY)
                                page.evaluate(
                                    "window.scrollTo(0, document.body.scrollHeight * 2 / 3)"
                                )
                                time.sleep(SCROLL_DELAY)
                                page.evaluate(
                                    "window.scrollTo(0, document.body.scrollHeight)"
                                )
                                time.sleep(SCROLL_DELAY)
                                page.evaluate("window.scrollTo(0, 0)")
                            except:
                                pass

                            url_time = time.time() - url_start_time
                            self.session_stats["total_time"] += url_time
                            self.session_stats["urls_opened"] += 1
                            logger.info(f"  ✓ Opened in {url_time:.1f}s")

                        except Exception as e:
                            self.session_stats["urls_failed"] += 1
                            logger.warning(f"  ✗ Failed to open: {e}")

                        # Delay between URLs
                        if i < len(urls):
                            time.sleep(self.url_delay)

                finally:
                    # Clean up
                    if context:
                        context.close()
                    if browser:
                        browser.close()
                    logger.info("Browser closed")

        except Exception as e:
            logger.error(f"Error opening URLs: {e}")
            import traceback

            traceback.print_exc()
        finally:
            elapsed = time.time() - start_time

            logger.info(f"\n=== Summary ===")
            logger.info(f"Completed in {elapsed:.1f} seconds")
            logger.info(f"Total URLs opened: {self.session_stats['urls_opened']}")
            logger.info(f"Failed to open: {self.session_stats['urls_failed']}")
            logger.info(
                f"Average time per URL: {self.session_stats['total_time'] / max(1, self.session_stats['urls_opened']):.1f}s"
            )


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="DEMO: Open job URLs from CSV in browser (for video recording)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Open all URLs with default settings
  python jobstreet_url_opener.py

  # Open only 20 URLs
  python jobstreet_url_opener.py -n 20

  # Set custom delay between URLs (2 seconds)
  python jobstreet_url_opener.py --delay 2.0

  # Run in headless mode
  python jobstreet_url_opener.py --headless
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        default=None,
        help=f"Input CSV file with job URLs (default: {INPUT_FILE})",
    )
    parser.add_argument(
        "-n",
        "--max-urls",
        type=int,
        default=None,
        help="Maximum number of URLs to open (default: all URLs)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help=f"Delay between URLs in seconds (default: {URL_DELAY})",
    )
    parser.add_argument(
        "--page-wait",
        type=float,
        default=None,
        help=f"Wait time after page load in seconds (default: {PAGE_WAIT_TIME})",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no window)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=f"Page load timeout in milliseconds (default: {PAGE_LOAD_TIMEOUT})",
    )

    args = parser.parse_args()

    opener = URLOpener(
        input_file=args.input,
        headless=args.headless,
        max_urls=args.max_urls,
        page_load_timeout=args.timeout,
        page_wait_time=args.page_wait,
        url_delay=args.delay,
    )

    opener.open_urls()


if __name__ == "__main__":
    main()
