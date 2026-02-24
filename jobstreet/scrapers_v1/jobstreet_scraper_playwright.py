#!/usr/bin/env python3
"""
JobStreet Indonesia Scraper - Playwright Version

Uses Playwright for reliable browser automation.

Author: Research Assistant
Date: January 2026
"""

import csv
import json
import logging
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sys

# Platform-specific imports
if sys.platform == 'win32':
    import msvcrt
else:
    import fcntl

from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup
from tqdm import tqdm

# =============================================================================
# SCRAPING PARAMETERS - CONFIGURE THESE AT THE TOP
# =============================================================================

# Search locations (cities in Indonesia)
SEARCH_LOCATIONS = [
    "Jakarta",
    # "Surabaya",
    # "Bandung",
    # "Medan",
    # "Semarang",
    # "Makassar",
    # "Yogyakarta",
    # "Tangerang",
    # "Bekasi",
    # "Bali",
]

# Search keywords (job categories to search for)
SEARCH_KEYWORDS = [
    "",  # All jobs
    # "fresh-graduate",
    # "entry-level",
    # "junior",
    # "staff",
    # "admin",
    # "marketing",
    # "it",
    # "software",
    # "engineer",
]

# Date range/period for job postings
# Options: 1 (last day), 7 (last week), 30 (last month), 365 (last year)
# Or specify custom date range as: "2024-01-01_2024-12-31"
DATE_RANGE = 373  # Default: last 365 days

# Maximum jobs to scrape per keyword-location combination
MAX_JOBS_PER_SEARCH = 10000

# Number of keywords to use from the list (to limit search scope)
MAX_KEYWORDS_TO_USE = 3

# Maximum total jobs to collect across all searches (overall session limit)
MAX_TOTAL_JOBS = 10000

# Maximum pages to scrape per keyword-location combination (to prevent infinite loops)
MAX_PAGES_PER_SEARCH = 100

# Browser and scraping configuration
PAGE_LOAD_TIMEOUT = 30000  # milliseconds
BROWSER_VIEWPORT_WIDTH = 1920
BROWSER_VIEWPORT_HEIGHT = 1080
BROWSER_LOCALE = "id-ID"
BROWSER_TIMEZONE = "Asia/Jakarta"

# User agent string for browser
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Scraping behavior
PAGE_SCROLL_DELAY = 4.0  # seconds to wait after page load
ELEMENT_SCROLL_DELAY = 0.5  # seconds between scroll actions
CONSECUTIVE_EMPTY_PAGE_LIMIT = 2  # stop after this many empty pages
INITIAL_PAGE_LOAD_MULTIPLIER = 1.5  # multiplier for initial page delay

# =============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@dataclass
class JobVacancy:
    """Data class representing a job vacancy."""
    job_id: str = ""
    job_title: str = ""
    company_name: str = ""
    company_id: str = ""
    location: str = ""
    city: str = ""
    province: str = ""
    country: str = "Indonesia"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "IDR"
    salary_type: str = ""
    work_type: str = ""
    work_arrangement: str = ""
    experience_level: str = ""
    education_level: str = ""
    job_category: str = ""
    job_subcategory: str = ""
    industry: str = ""
    job_description: str = ""
    requirements: str = ""
    skills: str = ""
    posted_date: str = ""
    closing_date: str = ""
    scraped_at: str = ""
    job_url: str = ""
    company_url: str = ""
    is_featured: bool = False
    is_urgent: bool = False
    applicants_count: Optional[int] = None


class JobStreetPlaywrightScraper:
    """
    Playwright-based scraper for JobStreet Indonesia.
    """

    BASE_URL = "https://id.jobstreet.com"
    
    def __init__(
        self,
        output_file: str = "job_vacancies/data/jobstreet_vacancies.csv",
        max_jobs: Optional[int] = None,
        headless: bool = False,
        delay_range: tuple = (2.0, 4.0),
        locations: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        date_range: Optional[int] = None,
        max_jobs_per_search: Optional[int] = None,
        max_keywords_to_use: Optional[int] = None,
        max_pages_per_search: Optional[int] = None,
        page_load_timeout: Optional[int] = None,
        viewport_size: Optional[tuple] = None,
        browser_locale: Optional[str] = None,
        browser_timezone: Optional[str] = None,
        user_agent: Optional[str] = None,
        page_scroll_delay: Optional[float] = None,
        consecutive_empty_limit: Optional[int] = None,
        initial_load_multiplier: Optional[float] = None,
    ):
        """Initialize the Playwright scraper."""
        self.output_file = Path(output_file)
        self.max_jobs = max_jobs if max_jobs is not None else MAX_TOTAL_JOBS
        self.headless = headless
        self.delay_range = delay_range

        # Use provided parameters or defaults from configuration
        self.locations = locations if locations is not None else SEARCH_LOCATIONS
        self.keywords = keywords if keywords is not None else SEARCH_KEYWORDS
        self.date_range = date_range if date_range is not None else DATE_RANGE
        self.max_jobs_per_search = max_jobs_per_search if max_jobs_per_search is not None else MAX_JOBS_PER_SEARCH
        self.max_keywords_to_use = max_keywords_to_use if max_keywords_to_use is not None else MAX_KEYWORDS_TO_USE
        self.max_pages_per_search = max_pages_per_search if max_pages_per_search is not None else MAX_PAGES_PER_SEARCH

        # Browser and scraping configuration
        self.page_load_timeout = page_load_timeout if page_load_timeout is not None else PAGE_LOAD_TIMEOUT
        self.viewport_size = viewport_size if viewport_size is not None else (BROWSER_VIEWPORT_WIDTH, BROWSER_VIEWPORT_HEIGHT)
        self.browser_locale = browser_locale if browser_locale is not None else BROWSER_LOCALE
        self.browser_timezone = browser_timezone if browser_timezone is not None else BROWSER_TIMEZONE
        self.user_agent = user_agent if user_agent is not None else BROWSER_USER_AGENT
        self.page_scroll_delay = page_scroll_delay if page_scroll_delay is not None else PAGE_SCROLL_DELAY
        self.consecutive_empty_limit = consecutive_empty_limit if consecutive_empty_limit is not None else CONSECUTIVE_EMPTY_PAGE_LIMIT
        self.initial_load_multiplier = initial_load_multiplier if initial_load_multiplier is not None else INITIAL_PAGE_LOAD_MULTIPLIER

        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        self.scraped_job_ids: set = set()
        self.jobs_collected: List[JobVacancy] = []
        self.session_stats = {
            'pages_scraped': 0,
            'pages_with_errors': 0,
            'csv_writes': 0,
            'csv_write_errors': 0,
            'pages_skipped': 0,
            'jobs_skipped_by_filter': 0,
        }

        # Load existing job IDs from CSV if it exists
        self._load_existing_job_ids()

        logger.info(f"Scraper initialized. Target: {max_jobs} jobs")
        logger.info(f"Output file: {self.output_file}")
        logger.info(f"Locations: {len(self.locations)}, Keywords: {len(self.keywords[:self.max_keywords_to_use])}")
        logger.info(f"Date range: {self.date_range} days")
        logger.info(f"Existing jobs in CSV: {len(self.scraped_job_ids)}")
        if len(self.scraped_job_ids) > 0:
            logger.info(f"✓ Optimization enabled: Will skip {len(self.scraped_job_ids)} known jobs during extraction")
    
    def _random_delay(self, multiplier: float = 1.0) -> None:
        """Add random delay."""
        delay = random.uniform(*self.delay_range) * multiplier
        time.sleep(delay)
    
    def _build_search_url(self, keyword: str = "", location: str = "", page: int = 1) -> str:
        """Build the search URL."""
        keyword = keyword.strip().lower().replace(" ", "-")
        location = location.strip()

        if keyword:
            path = f"/{keyword}-jobs"
        else:
            path = "/jobs"

        if location:
            path += f"/in-{location}"

        params = f"?daterange={self.date_range}&page={page}"

        return f"{self.BASE_URL}{path}{params}"
    
    def _extract_job_ids_only(self) -> List[str]:
        """Quickly extract only job IDs from current page (for filtering duplicates)."""
        job_ids = []

        try:
            # Get page content (quick, no scrolling needed)
            content = self.page.content()
            soup = BeautifulSoup(content, 'lxml')

            # First try __NEXT_DATA__ - fastest method
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.string)
                    page_props = data.get("props", {}).get("pageProps", {})

                    # Try different paths to find jobs
                    search_results = page_props.get("searchResults", {})
                    jobs_data = search_results.get("jobs", [])

                    if not jobs_data:
                        jobs_data = page_props.get("jobs", [])

                    if not jobs_data:
                        results = page_props.get("results", {})
                        jobs_data = results.get("jobs", results.get("data", []))

                    for job in jobs_data:
                        job_id = str(job.get("id", job.get("jobId", "")))
                        if job_id:
                            job_ids.append(job_id)

                    if job_ids:
                        return job_ids

                except json.JSONDecodeError:
                    pass

            # Fallback: Extract job IDs from links - faster than full parsing
            job_links = soup.select('a[data-automation="jobTitle"], a[id^="job-title-"]')
            for link in job_links:
                try:
                    # Extract from id attribute
                    elem_id = link.get("id", "")
                    if elem_id and elem_id.startswith("job-title-"):
                        job_ids.append(elem_id.replace("job-title-", ""))
                        continue

                    # Extract from URL
                    href = link.get("href", "")
                    match = re.search(r'/job/(\d+)', href)
                    if match:
                        job_ids.append(match.group(1))
                except:
                    pass

        except Exception as e:
            logger.debug(f"Error extracting job IDs only: {e}")

        return job_ids

    def _extract_jobs_from_page(self, filter_job_ids: Optional[set] = None) -> List[Dict[str, Any]]:
        """Extract job listings from current page, optionally filtering by job IDs."""
        jobs = []
        skipped_count = 0

        # If we have a filter set, first do a quick ID-only extraction to skip known jobs
        if filter_job_ids:
            all_job_ids = self._extract_job_ids_only()
            new_job_ids = [jid for jid in all_job_ids if jid not in filter_job_ids]

            if not new_job_ids:
                logger.debug("All jobs on this page are already scraped, skipping full extraction")
                return []

            if len(new_job_ids) < len(all_job_ids):
                skipped = len(all_job_ids) - len(new_job_ids)
                skipped_count = skipped
                self.session_stats['jobs_skipped_by_filter'] += skipped
                logger.debug(f"Skipping {skipped} already-scraped jobs on this page")

        try:
            # Wait for page to be interactive
            time.sleep(self.page_scroll_delay)

            # Scroll to load lazy content
            try:
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                time.sleep(ELEMENT_SCROLL_DELAY)
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(ELEMENT_SCROLL_DELAY)
                self.page.evaluate("window.scrollTo(0, 0)")
            except:
                pass

            # Get page content
            content = self.page.content()

            # Debug: Check if we have content
            if len(content) < 1000:
                logger.warning(f"Page content is very short: {len(content)} chars")
                # Save screenshot for debugging
                try:
                    self.page.screenshot(path="debug_screenshot.png")
                    logger.info("Saved debug screenshot")
                except:
                    pass
            soup = BeautifulSoup(content, 'lxml')

            # First try __NEXT_DATA__
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.string)
                    page_props = data.get("props", {}).get("pageProps", {})

                    # Try different paths to find jobs
                    search_results = page_props.get("searchResults", {})
                    jobs_data = search_results.get("jobs", [])

                    if not jobs_data:
                        jobs_data = page_props.get("jobs", [])

                    if not jobs_data:
                        results = page_props.get("results", {})
                        jobs_data = results.get("jobs", results.get("data", []))

                    for job in jobs_data:
                        job_id = str(job.get("id", job.get("jobId", "")))
                        # Skip if we have a filter and this job is already known
                        if filter_job_ids and job_id in filter_job_ids:
                            continue

                        parsed = self._parse_job_json(job)
                        if parsed:
                            jobs.append(parsed)

                    if jobs:
                        logger.debug(f"Extracted {len(jobs)} jobs from __NEXT_DATA__")
                        return jobs

                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse __NEXT_DATA__: {e}")

            # Fallback: Parse HTML directly
            job_cards = soup.select('article, [data-automation="job-card"], [data-search-sol-meta]')

            for card in job_cards:
                try:
                    job_data = self._parse_job_card_html(card)
                    job_id = job_data.get("job_id") if job_data else ""

                    # Skip if we have a filter and this job is already known
                    if filter_job_ids and job_id in filter_job_ids:
                        continue

                    if job_data and job_id:
                        jobs.append(job_data)
                except Exception as e:
                    logger.debug(f"Failed to parse job card: {e}")

            # If still no jobs, try finding job title links
            if not jobs:
                job_links = soup.select('a[data-automation="jobTitle"], a[id^="job-title-"]')
                for link in job_links:
                    try:
                        job_data = self._parse_job_link(link)
                        job_id = job_data.get("job_id") if job_data else ""

                        # Skip if we have a filter and this job is already known
                        if filter_job_ids and job_id in filter_job_ids:
                            continue

                        if job_data and job_id:
                            jobs.append(job_data)
                    except Exception as e:
                        logger.debug(f"Failed to parse job link: {e}")

        except Exception as e:
            logger.error(f"Error extracting jobs: {e}")

        return jobs
    
    def _parse_job_json(self, job: Dict) -> Optional[Dict[str, Any]]:
        """Parse job data from JSON."""
        try:
            job_id = str(job.get("id", job.get("jobId", "")))
            if not job_id:
                return None
            
            # Parse salary
            salary = job.get("salary") or job.get("salaryRange") or {}
            salary_min = None
            salary_max = None
            
            if isinstance(salary, dict):
                salary_min = salary.get("min") or salary.get("minimum")
                salary_max = salary.get("max") or salary.get("maximum")
            elif isinstance(salary, str):
                numbers = re.findall(r'[\d,]+', salary.replace('.', ''))
                if numbers:
                    try:
                        salary_min = float(numbers[0].replace(',', ''))
                        if len(numbers) > 1:
                            salary_max = float(numbers[1].replace(',', ''))
                    except ValueError:
                        pass
            
            # Parse location
            location = job.get("location") or job.get("jobLocation") or {}
            if isinstance(location, dict):
                location_str = location.get("label", location.get("name", ""))
            else:
                location_str = str(location) if location else ""
            
            # Parse work type
            work_type = job.get("workType") or job.get("employmentType") or ""
            if isinstance(work_type, dict):
                work_type = work_type.get("label", work_type.get("name", ""))
            
            # Build job URL
            job_url = job.get("jobUrl") or job.get("url") or ""
            if not job_url:
                job_url = f"{self.BASE_URL}/job/{job_id}"
            elif job_url.startswith("/"):
                job_url = f"{self.BASE_URL}{job_url}"
            
            # Get description
            description = job.get("teaser") or job.get("description") or ""
            bullet_points = job.get("bulletPoints") or job.get("highlights") or []
            if bullet_points:
                description += "\n" + "\n".join(f"• {bp}" for bp in bullet_points)
            
            return {
                "job_id": job_id,
                "job_title": job.get("title", job.get("jobTitle", "")),
                "company_name": job.get("companyName") or job.get("advertiser", {}).get("description", ""),
                "company_id": str(job.get("companyId") or job.get("advertiserId", "")),
                "location": location_str,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "work_type": work_type,
                "work_arrangement": job.get("workArrangement", ""),
                "job_description": description,
                "posted_date": job.get("postedDate") or job.get("listingDate", ""),
                "job_url": job_url,
                "is_featured": job.get("isFeatured", False),
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse job JSON: {e}")
            return None
    
    def _parse_job_card_html(self, card: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Parse job card from HTML."""
        try:
            # Find title link
            title_elem = card.select_one('a[data-automation="jobTitle"], a[id^="job-title-"], h1 a, h2 a, h3 a')
            if not title_elem:
                return None
            
            job_title = title_elem.get_text(strip=True)
            job_url = title_elem.get("href", "")
            if job_url.startswith("/"):
                job_url = f"{self.BASE_URL}{job_url}"
            
            # Extract job ID
            job_id = ""
            elem_id = title_elem.get("id", "")
            if elem_id and elem_id.startswith("job-title-"):
                job_id = elem_id.replace("job-title-", "")
            else:
                match = re.search(r'/job/(\d+)', job_url)
                if match:
                    job_id = match.group(1)
            
            if not job_id:
                return None
            
            # Company
            company_elem = card.select_one('a[data-automation="jobCompany"], [data-automation="company-name"]')
            company_name = company_elem.get_text(strip=True) if company_elem else ""
            
            # Location
            location_elem = card.select_one('a[data-automation="jobLocation"], [data-automation="job-location"]')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Posted date
            card_text = card.get_text()
            posted_date = ""
            date_match = re.search(r'(\d+[dhm]\s*ago|\d+\+?\s*days?\s*ago)', card_text, re.IGNORECASE)
            if date_match:
                posted_date = date_match.group(1)
            
            return {
                "job_id": job_id,
                "job_title": job_title,
                "company_name": company_name,
                "location": location,
                "posted_date": posted_date,
                "job_url": job_url,
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse job card HTML: {e}")
            return None
    
    def _parse_job_link(self, link: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Parse job from a link element."""
        try:
            job_title = link.get_text(strip=True)
            job_url = link.get("href", "")
            if job_url.startswith("/"):
                job_url = f"{self.BASE_URL}{job_url}"
            
            # Extract job ID
            job_id = ""
            elem_id = link.get("id", "")
            if elem_id and elem_id.startswith("job-title-"):
                job_id = elem_id.replace("job-title-", "")
            else:
                match = re.search(r'/job/(\d+)', job_url)
                if match:
                    job_id = match.group(1)
            
            if not job_id:
                return None
            
            return {
                "job_id": job_id,
                "job_title": job_title,
                "job_url": job_url,
            }
            
        except Exception as e:
            return None
    
    def _has_next_page(self) -> bool:
        """Check if there's a next page."""
        try:
            content = self.page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.string)
                    page_props = data.get("props", {}).get("pageProps", {})
                    search_results = page_props.get("searchResults", {})
                    
                    pagination = search_results.get("pagination", {})
                    if pagination:
                        current = pagination.get("currentPage", pagination.get("page", 1))
                        total = pagination.get("totalPages", pagination.get("pages", 1))
                        return current < total
                    
                    if search_results.get("hasNextPage"):
                        return True
                except:
                    pass
            
            # Check for next button
            next_btn = soup.select_one('a[data-automation="page-next"], [aria-label*="Next"]')
            return next_btn is not None
            
        except:
            return False

    def _load_existing_job_ids(self) -> None:
        """Load existing job IDs from CSV file."""
        if not self.output_file.exists():
            return

        try:
            with open(self.output_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    job_id = row.get('job_id', '').strip()
                    if job_id:
                        self.scraped_job_ids.add(job_id)
            logger.info(f"Loaded {len(self.scraped_job_ids)} existing job IDs from {self.output_file}")
        except Exception as e:
            logger.warning(f"Could not load existing job IDs: {e}")

    def _create_csv_if_not_exists(self) -> None:
        """Create CSV file with headers if it doesn't exist."""
        if self.output_file.exists():
            return

        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(JobVacancy.__dataclass_fields__.keys())

        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

        logger.info(f"Created new CSV file: {self.output_file}")

    def append_job_to_csv(self, job: JobVacancy) -> bool:
        """Append a single job to the CSV file with file locking. Returns True if successful."""
        # Create CSV if it doesn't exist
        self._create_csv_if_not_exists()

        fieldnames = list(JobVacancy.__dataclass_fields__.keys())

        try:
            # Open with exclusive lock to prevent concurrent writes
            with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
                # Try to acquire lock (platform-specific)
                if sys.platform == 'win32':
                    # Windows file locking
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    except (AttributeError, OSError, IOError):
                        # Locking not supported or failed, proceed without it
                        pass
                else:
                    # Unix file locking
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    except (AttributeError, OSError):
                        # Locking not supported, proceed without it
                        pass

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(asdict(job))

                # Release lock (platform-specific)
                if sys.platform == 'win32':
                    try:
                        f.seek(0)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except (AttributeError, OSError, IOError):
                        pass
                else:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except (AttributeError, OSError):
                        pass

            self.session_stats['csv_writes'] += 1
            return True
        except Exception as e:
            logger.error(f"Failed to append job {job.job_id} to CSV: {e}")
            self.session_stats['csv_write_errors'] += 1
            return False

    def scrape(self) -> None:
        """Main scraping method."""
        logger.info("Starting Playwright scraper...")

        self.browser = None
        self.page = None
        context = None

        try:
            with sync_playwright() as p:
                # Launch browser
                self.browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ]
                )

                # Create context with realistic settings
                context = self.browser.new_context(
                    viewport={"width": self.viewport_size[0], "height": self.viewport_size[1]},
                    user_agent=self.user_agent,
                    locale=self.browser_locale,
                    timezone_id=self.browser_timezone,
                )

                self.page = context.new_page()

                # Don't block resources - let the page load fully
                # self.page.route("**/*.{png,jpg,jpeg,gif,svg,ico}", lambda route: route.abort())

                # First visit main page
                logger.info("Visiting main page to establish session...")
                self.page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=self.page_load_timeout)
                self._random_delay(self.initial_load_multiplier)

                with tqdm(total=self.max_jobs, desc="Scraping jobs") as pbar:
                    for location in self.locations:
                        if len(self.jobs_collected) >= self.max_jobs:
                            break

                        for keyword in self.keywords[:self.max_keywords_to_use]:
                            if len(self.jobs_collected) >= self.max_jobs:
                                break

                            search_desc = f"'{keyword}'" if keyword else "(all jobs)"
                            logger.info(f"Searching {search_desc} in {location}")

                            page_num = 1
                            consecutive_empty = 0
                            jobs_for_this_search = 0

                            while (page_num <= self.max_pages_per_search and
                                   len(self.jobs_collected) < self.max_jobs and
                                   jobs_for_this_search < self.max_jobs_per_search):
                                url = self._build_search_url(keyword=keyword, location=location, page=page_num)

                                try:
                                    self.page.goto(url, wait_until="domcontentloaded", timeout=self.page_load_timeout)
                                    self._random_delay()

                                    # Quick check: if we have existing IDs, first extract only job IDs
                                    # This allows us to skip full page parsing if all jobs are duplicates
                                    if self.scraped_job_ids and consecutive_empty == 0:
                                        page_job_ids = self._extract_job_ids_only()
                                        if page_job_ids:
                                            new_jobs_on_page = sum(1 for jid in page_job_ids if jid not in self.scraped_job_ids)

                                            # If page has no new jobs, skip it entirely
                                            if new_jobs_on_page == 0:
                                                self.session_stats['pages_skipped'] += 1
                                                logger.debug(f"  Page {page_num}: All jobs already scraped, skipping")
                                                consecutive_empty += 1
                                                if consecutive_empty >= self.consecutive_empty_limit:
                                                    break
                                                page_num += 1
                                                continue

                                            logger.debug(f"  Page {page_num}: Found {new_jobs_on_page} new jobs out of {len(page_job_ids)} total")

                                    # Pass existing job IDs to filter out duplicates during extraction
                                    jobs = self._extract_jobs_from_page(filter_job_ids=self.scraped_job_ids)

                                    if not jobs:
                                        consecutive_empty += 1
                                        if consecutive_empty >= self.consecutive_empty_limit:
                                            break
                                        page_num += 1
                                        continue

                                    consecutive_empty = 0
                                    jobs_added = 0
                                    csv_write_success = True
                                    self.session_stats['pages_scraped'] += 1

                                    for job_data in jobs:
                                        job_id = job_data.get("job_id", "")
                                        # Job ID already filtered during extraction, but double-check
                                        if not job_id or job_id in self.scraped_job_ids:
                                            continue

                                        self.scraped_job_ids.add(job_id)

                                        job = JobVacancy(
                                            job_id=job_id,
                                            job_title=job_data.get("job_title", ""),
                                            company_name=job_data.get("company_name", ""),
                                            company_id=job_data.get("company_id", ""),
                                            location=job_data.get("location", ""),
                                            city=location,
                                            salary_min=job_data.get("salary_min"),
                                            salary_max=job_data.get("salary_max"),
                                            work_type=job_data.get("work_type", ""),
                                            work_arrangement=job_data.get("work_arrangement", ""),
                                            job_category=keyword if keyword else "",
                                            job_description=job_data.get("job_description", ""),
                                            posted_date=job_data.get("posted_date", ""),
                                            scraped_at=datetime.now().isoformat(),
                                            job_url=job_data.get("job_url", ""),
                                            is_featured=job_data.get("is_featured", False),
                                        )

                                        # Save job immediately to CSV
                                        if self.append_job_to_csv(job):
                                            self.jobs_collected.append(job)
                                            jobs_added += 1
                                            jobs_for_this_search += 1
                                            pbar.update(1)
                                        else:
                                            csv_write_success = False

                                        if (len(self.jobs_collected) >= self.max_jobs or
                                            jobs_for_this_search >= self.max_jobs_per_search):
                                            break

                                    status_msg = f"  Page {page_num}: +{jobs_added} jobs (Total: {len(self.jobs_collected)})"
                                    if not csv_write_success:
                                        status_msg += " [⚠ CSV write errors]"
                                    logger.info(status_msg)

                                    # If we're finding very few new jobs per page, we might be past the new job range
                                    if jobs_added == 0 and page_num > 5:
                                        self.session_stats['pages_skipped'] += 1
                                        logger.info("  No new jobs found on this page, likely reached already-scraped content")
                                        break

                                    if not self._has_next_page():
                                        break

                                    page_num += 1

                                except Exception as e:
                                    logger.error(f"Error on page {page_num}: {e}")
                                    self.session_stats['pages_with_errors'] += 1
                                    consecutive_empty += 1
                                    if consecutive_empty >= self.consecutive_empty_limit:
                                        break
                                    page_num += 1
                                    continue

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise
        finally:
            # Clean up resources properly
            cleanup_errors = []
            if context:
                try:
                    context.close()
                except Exception as e:
                    cleanup_errors.append(f"Context close error: {e}")
            if self.browser:
                try:
                    self.browser.close()
                except Exception as e:
                    cleanup_errors.append(f"Browser close error: {e}")
            if cleanup_errors:
                logger.warning(f"Cleanup errors: {'; '.join(cleanup_errors)}")
            else:
                logger.info("Browser closed")
    
    def save_to_csv(self) -> None:
        """Save any remaining collected jobs to CSV (for interrupted sessions)."""
        jobs_to_save = [job for job in self.jobs_collected if job.job_id not in self.scraped_job_ids]

        if not jobs_to_save:
            logger.info("All jobs already saved to CSV")
            return

        logger.info(f"Saving {len(jobs_to_save)} remaining jobs to CSV...")

        for job in jobs_to_save:
            self.append_job_to_csv(job)
            self.scraped_job_ids.add(job.job_id)

        logger.info(f"Saved {len(jobs_to_save)} additional jobs to {self.output_file}")
    
    def run(self) -> None:
        """Run the complete scraping process."""
        start_time = time.time()

        try:
            self.scrape()
            # Note: Jobs are saved incrementally during scraping, but we call save_to_csv()
            # in case any jobs weren't saved due to errors
            self.save_to_csv()
        except KeyboardInterrupt:
            logger.info("Interrupted by user - saving any remaining jobs...")
            self.save_to_csv()
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            import traceback
            traceback.print_exc()
            if self.jobs_collected:
                logger.info("Saving collected jobs despite error...")
                self.save_to_csv()
        finally:
            elapsed = time.time() - start_time
            logger.info(f"Completed in {elapsed:.1f} seconds")
            logger.info(f"Total jobs collected: {len(self.jobs_collected)}")
            logger.info(f"Total unique jobs saved: {len(self.scraped_job_ids)}")
            logger.info(f"Pages scraped: {self.session_stats['pages_scraped']}")
            logger.info(f"Pages with errors: {self.session_stats['pages_with_errors']}")
            logger.info(f"Pages skipped (all duplicate): {self.session_stats.get('pages_skipped', 0)}")
            logger.info(f"Jobs skipped by filter: {self.session_stats.get('jobs_skipped_by_filter', 0)}")
            logger.info(f"CSV writes: {self.session_stats['csv_writes']}")
            if self.session_stats['csv_write_errors'] > 0:
                logger.warning(f"CSV write errors: {self.session_stats['csv_write_errors']}")
            logger.info(f"Output file: {self.output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="JobStreet Indonesia Scraper (Playwright)")
    parser.add_argument("-o", "--output", default="job_vacancies/data/jobstreet_vacancies.csv",
                       help="Output CSV file path")
    parser.add_argument("-n", "--max-jobs", type=int, default=MAX_TOTAL_JOBS,
                       help=f"Maximum total jobs to scrape. Default: {MAX_TOTAL_JOBS}")
    parser.add_argument("--headless", action="store_true",
                       help="Run in headless mode (no browser window)")

    # New configurable parameters
    parser.add_argument("--locations", nargs='+',
                       help="Locations to search (space-separated). Default: use configured SEARCH_LOCATIONS")
    parser.add_argument("--keywords", nargs='+',
                       help="Keywords to search (space-separated). Default: use configured SEARCH_KEYWORDS")
    parser.add_argument("--date-range", type=int,
                       help=f"Date range in days (1,7,30,365). Default: {DATE_RANGE}")
    parser.add_argument("--max-jobs-per-search", type=int,
                       help=f"Max jobs per keyword-location combo. Default: {MAX_JOBS_PER_SEARCH}")
    parser.add_argument("--max-keywords", type=int,
                       help=f"Max keywords to use from list. Default: {MAX_KEYWORDS_TO_USE}")
    parser.add_argument("--max-pages", type=int,
                       help=f"Max pages per keyword-location combo. Default: {MAX_PAGES_PER_SEARCH}")
    parser.add_argument("--timeout", type=int,
                       help=f"Page load timeout in milliseconds. Default: {PAGE_LOAD_TIMEOUT}")
    parser.add_argument("--delay", type=float,
                       help=f"Delay between requests in seconds. Default: {PAGE_SCROLL_DELAY}")

    args = parser.parse_args()

    # Convert locations and keywords if provided
    locations = args.locations if args.locations else None
    keywords = args.keywords if args.keywords else None

    scraper = JobStreetPlaywrightScraper(
        output_file=args.output,
        max_jobs=args.max_jobs,
        headless=args.headless,
        locations=locations,
        keywords=keywords,
        date_range=args.date_range,
        max_jobs_per_search=args.max_jobs_per_search,
        max_keywords_to_use=args.max_keywords,
        max_pages_per_search=args.max_pages,
        page_load_timeout=args.timeout,
        page_scroll_delay=args.delay,
    )

    scraper.run()


if __name__ == "__main__":
    main()
