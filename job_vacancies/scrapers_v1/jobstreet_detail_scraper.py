#!/usr/bin/env python3
"""
JobStreet Job Detail Scraper

Opens each job URL from the scraped CSV and extracts full job details.

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
from dataclasses import dataclass, asdict, fields

from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup
from tqdm import tqdm

# =============================================================================
# SCRAPING PARAMETERS - CONFIGURE THESE AT THE TOP
# =============================================================================

# Input/Output files
INPUT_FILE = "job_vacancies/data/jobstreet_vacancies.csv"
OUTPUT_FILE = "job_vacancies/data/jobstreet_details.csv"

# Delay between requests (in seconds) - random delay between min and max
MIN_DELAY = 2.0
MAX_DELAY = 4.0

# Browser configuration
HEADLESS_MODE = False  # Set to True to run without browser window
PAGE_LOAD_TIMEOUT = 30000  # milliseconds
BROWSER_VIEWPORT_WIDTH = 1920
BROWSER_VIEWPORT_HEIGHT = 1080
BROWSER_LOCALE = "id-ID"
BROWSER_TIMEZONE = "Asia/Jakarta"
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Scraping limits
MAX_JOBS = None  # Maximum number of jobs to process (None = all jobs)
MAX_RETRIES = 3  # Retry failed jobs N times
RETRY_DELAY_MULTIPLIER = 2.0  # Multiply delay on each retry
JOB_PAGE_TIMEOUT = 60000  # Timeout per job page (milliseconds)

# Page loading behavior
PAGE_WAIT_TIME = 3.0  # seconds to wait after page load for dynamic content
SCROLL_WAIT_TIME = 0.3  # seconds to wait between scroll actions
INITIAL_DELAY_MULTIPLIER = 1.5  # multiplier for initial session setup delay

# Batch processing
BATCH_SIZE = 10  # Save CSV every N jobs

# =============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@dataclass
class JobDetail:
    """Data class representing detailed job information."""
    job_id: str = ""
    job_title: str = ""
    company_name: str = ""
    location: str = ""
    job_category: str = ""
    job_subcategory: str = ""
    work_type: str = ""  # Full time, Part time, Contract, etc.
    work_arrangement: str = ""  # Remote, Hybrid, On-site
    posted_date: str = ""
    application_status: str = ""  # e.g., "High application volume"
    
    # Salary
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "IDR"
    salary_period: str = ""  # per month, per year
    
    # Requirements
    experience_level: str = ""
    education_level: str = ""
    qualifications: str = ""
    skills_required: str = ""
    
    # Description
    job_description: str = ""
    key_responsibilities: str = ""
    benefits: str = ""
    
    # Company info
    company_size: str = ""
    company_industry: str = ""
    company_description: str = ""
    company_rating: str = ""  # e.g., "4.2"
    company_review_count: str = ""  # e.g., "46 reviews"
    company_logo_url: str = ""
    
    # Application details
    employer_questions: str = ""  # List of screening questions, separated by |
    perks_benefits: str = ""  # Structured perks/benefits (separate from description)
    
    # Metadata
    job_url: str = ""
    scraped_at: str = ""


class JobDetailScraper:
    """
    Scrapes full job details from JobStreet job pages.
    """

    BASE_URL = "https://id.jobstreet.com"
    
    def __init__(
        self,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        delay_range: Optional[tuple] = None,
        headless: Optional[bool] = None,
        max_jobs: Optional[int] = None,
        page_load_timeout: Optional[int] = None,
        viewport_size: Optional[tuple] = None,
        browser_locale: Optional[str] = None,
        browser_timezone: Optional[str] = None,
        user_agent: Optional[str] = None,
        page_wait_time: Optional[float] = None,
        scroll_wait_time: Optional[float] = None,
        initial_delay_multiplier: Optional[float] = None,
    ):
        """Initialize the detail scraper."""
        # Use provided parameters or defaults from configuration
        self.input_file = Path(input_file if input_file is not None else INPUT_FILE)
        self.output_file = Path(output_file if output_file is not None else OUTPUT_FILE)
        self.delay_range = delay_range if delay_range is not None else (MIN_DELAY, MAX_DELAY)
        self.headless = headless if headless is not None else HEADLESS_MODE
        self.max_jobs = max_jobs if max_jobs is not None else MAX_JOBS
        
        # Browser and scraping configuration
        self.page_load_timeout = page_load_timeout if page_load_timeout is not None else PAGE_LOAD_TIMEOUT
        self.viewport_size = viewport_size if viewport_size is not None else (BROWSER_VIEWPORT_WIDTH, BROWSER_VIEWPORT_HEIGHT)
        self.browser_locale = browser_locale if browser_locale is not None else BROWSER_LOCALE
        self.browser_timezone = browser_timezone if browser_timezone is not None else BROWSER_TIMEZONE
        self.user_agent = user_agent if user_agent is not None else BROWSER_USER_AGENT
        self.page_wait_time = page_wait_time if page_wait_time is not None else PAGE_WAIT_TIME
        self.scroll_wait_time = scroll_wait_time if scroll_wait_time is not None else SCROLL_WAIT_TIME
        self.initial_delay_multiplier = initial_delay_multiplier if initial_delay_multiplier is not None else INITIAL_DELAY_MULTIPLIER
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # Track processed job IDs
        self.scraped_job_ids: set = set()
        self.jobs_processed: List[JobDetail] = []

        # Session statistics
        self.session_stats = {
            'pages_loaded': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'retry_attempts': 0,
            'csv_writes': 0,
            'total_time': 0,
        }

        # Load existing job IDs from CSV if it exists
        self._load_existing_job_ids()

        logger.info(f"Detail scraper initialized. Input: {self.input_file}")
        logger.info(f"Output: {self.output_file}")
        logger.info(f"Existing jobs in CSV: {len(self.scraped_job_ids)}")
    
    def _random_delay(self, multiplier: float = 1.0) -> None:
        """Add random delay."""
        delay = random.uniform(*self.delay_range) * multiplier
        time.sleep(delay)
    
    def _clean_job_url(self, url: str) -> str:
        """Clean job URL to just the base job URL."""
        # Remove query parameters
        if "?" in url:
            url = url.split("?")[0]
        
        # Ensure it's a full URL
        if url.startswith("/"):
            url = f"{self.BASE_URL}{url}"
        
        return url
    
    def _load_job_urls(self) -> List[Dict[str, str]]:
        """Load job URLs from input CSV."""
        jobs = []
        
        if not self.input_file.exists():
            logger.error(f"Input file not found: {self.input_file}")
            return jobs
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                job_url = row.get("job_url", "").strip()
                if job_url:
                    jobs.append({
                        "job_id": row.get("job_id", ""),
                        "job_url": self._clean_job_url(job_url),
                    })
        
        logger.info(f"Loaded {len(jobs)} jobs from {self.input_file}")
        return jobs
    
    def _load_existing_job_ids(self) -> None:
        """Load existing job IDs from output CSV file."""
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
        fieldnames = [f.name for f in fields(JobDetail)]
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
        
        logger.info(f"Created new CSV file: {self.output_file}")
    
    def append_job_to_csv(self, job: JobDetail) -> None:
        """Append a single job detail to the CSV file."""
        # Create CSV if it doesn't exist
        self._create_csv_if_not_exists()
        
        fieldnames = [f.name for f in fields(JobDetail)]
        
        try:
            # Clean up multiline fields to prevent CSV issues
            job_dict = asdict(job)
            for key, value in job_dict.items():
                if isinstance(value, str) and '\n' in value:
                    # Replace newlines with pipe separator for better CSV compatibility
                    job_dict[key] = value.replace('\n', ' | ')
            
            with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writerow(job_dict)
        except Exception as e:
            logger.error(f"Failed to append job {job.job_id} to CSV: {e}")
    
    def _extract_job_details(self, job_id: str, job_url: str, retry_count: int = 0) -> Optional[JobDetail]:
        """Extract full details from a job page with retry logic."""
        try:
            job_start_time = time.time()

            # Navigate to job page with timeout
            try:
                self.page.goto(job_url, wait_until="domcontentloaded", timeout=JOB_PAGE_TIMEOUT)
            except Exception as e:
                if "timeout" in str(e).lower():
                    logger.warning(f"Timeout loading {job_id}, attempt {retry_count + 1}/{MAX_RETRIES}")
                    self.session_stats['failed_extractions'] += 1
                    if retry_count < MAX_RETRIES - 1:
                        self.session_stats['retry_attempts'] += 1
                        delay = random.uniform(*self.delay_range) * RETRY_DELAY_MULTIPLIER ** retry_count
                        time.sleep(delay)
                        return self._extract_job_details(job_id, job_url, retry_count + 1)
                    return None
                raise

            self.session_stats['pages_loaded'] += 1
            time.sleep(self.page_wait_time)  # Wait for dynamic content

            # Scroll to load all content
            try:
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                time.sleep(self.scroll_wait_time)
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(self.scroll_wait_time)
                self.page.evaluate("window.scrollTo(0, 0)")
            except:
                pass

            content = self.page.content()
            soup = BeautifulSoup(content, 'lxml')

            # Initialize job detail
            job = JobDetail(
                job_id=job_id,
                job_url=job_url,
                scraped_at=datetime.now().isoformat(),
            )

            # Try to extract from __NEXT_DATA__ first (structured JSON)
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.string)
                    page_props = data.get("props", {}).get("pageProps", {})
                    job_detail = page_props.get("jobDetail", {})

                    if job_detail:
                        job = self._parse_job_detail_json(job_detail, job)
                        if self._validate_job_detail(job):
                            self.session_stats['successful_extractions'] += 1
                            job_time = time.time() - job_start_time
                            self.session_stats['total_time'] += job_time
                            logger.debug(f"✓ Extracted {job_id}: {job.job_title[:40]}... in {job_time:.1f}s")
                            return job
                except Exception as e:
                    logger.debug(f"Failed to parse __NEXT_DATA__: {e}")

            # Fallback: Parse HTML directly
            job = self._parse_job_detail_html(soup, job)
            if self._validate_job_detail(job):
                self.session_stats['successful_extractions'] += 1
                job_time = time.time() - job_start_time
                self.session_stats['total_time'] += job_time
                logger.debug(f"✓ Extracted {job_id}: {job.job_title[:40]}... in {job_time:.1f}s")
                return job
            else:
                logger.warning(f"⚠ Validation failed for {job_id}")
                self.session_stats['failed_extractions'] += 1
                return None

        except Exception as e:
            self.session_stats['failed_extractions'] += 1
            error_msg = str(e)
            logger.error(f"Error extracting details from {job_url}: {error_msg[:100]}")

            # Retry on network/transient errors
            if retry_count < MAX_RETRIES - 1 and any(
                kw in error_msg.lower() for kw in ['timeout', 'network', 'connection', 'reset', 'blocked']
            ):
                self.session_stats['retry_attempts'] += 1
                delay = random.uniform(*self.delay_range) * RETRY_DELAY_MULTIPLIER ** retry_count
                logger.info(f"Retrying {job_id} (attempt {retry_count + 2}/{MAX_RETRIES})...")
                time.sleep(delay)
                return self._extract_job_details(job_id, job_url, retry_count + 1)

            return None
    
    def _parse_job_detail_json(self, job_data: Dict, job: JobDetail) -> JobDetail:
        """Parse job details from JSON data."""
        try:
            # Basic info
            job.job_title = job_data.get("title", job_data.get("jobTitle", ""))
            job.company_name = job_data.get("companyName", "")
            
            # Location
            location = job_data.get("location", {})
            if isinstance(location, dict):
                job.location = location.get("label", location.get("name", ""))
            else:
                job.location = str(location) if location else ""
            
            # Work type
            work_type = job_data.get("workType", {})
            if isinstance(work_type, dict):
                job.work_type = work_type.get("label", work_type.get("name", ""))
            else:
                job.work_type = str(work_type) if work_type else ""
            
            # Work arrangement
            work_arr = job_data.get("workArrangement", {})
            if isinstance(work_arr, dict):
                job.work_arrangement = work_arr.get("label", work_arr.get("name", ""))
            else:
                job.work_arrangement = str(work_arr) if work_arr else ""
            
            # Classification/Category
            classification = job_data.get("classification", {})
            if isinstance(classification, dict):
                job.job_category = classification.get("description", classification.get("name", ""))
                subclass = classification.get("subClassification", {})
                if isinstance(subclass, dict):
                    job.job_subcategory = subclass.get("description", "")
            
            # Salary
            salary = job_data.get("salary", {})
            if isinstance(salary, dict):
                job.salary_min = salary.get("min") or salary.get("minimum")
                job.salary_max = salary.get("max") or salary.get("maximum")
                job.salary_currency = salary.get("currency", "IDR")
                job.salary_period = salary.get("type", salary.get("period", ""))
            
            # Description
            job.job_description = job_data.get("jobDescription", job_data.get("description", ""))
            
            # Posted date
            job.posted_date = job_data.get("postedDate", job_data.get("listingDate", ""))
            
            # Skills
            skills = job_data.get("skills", [])
            if skills:
                job.skills_required = ", ".join(skills) if isinstance(skills, list) else str(skills)
            
            # Experience/Education
            job.experience_level = job_data.get("experienceLevel", "")
            job.education_level = job_data.get("educationLevel", "")
            
            # Company info
            advertiser = job_data.get("advertiser", {})
            if advertiser:
                job.company_description = advertiser.get("description", "")
            
            # Company rating and reviews (from advertiser data if available)
            if isinstance(advertiser, dict):
                rating_data = advertiser.get("rating", {})
                if isinstance(rating_data, dict):
                    rating = rating_data.get("average") or rating_data.get("value")
                    if rating:
                        job.company_rating = str(rating)
                    review_count = rating_data.get("count") or rating_data.get("total")
                    if review_count:
                        job.company_review_count = str(review_count)
            
        except Exception as e:
            logger.debug(f"Error parsing JSON: {e}")
        
        return job
    
    def _parse_job_detail_html(self, soup: BeautifulSoup, job: JobDetail) -> JobDetail:
        """Parse job details from HTML."""
        try:
            # Job title - usually in h1
            title_elem = soup.select_one('h1[data-automation="job-detail-title"], h1')
            if title_elem:
                job.job_title = title_elem.get_text(strip=True)
            
            # Company name
            company_elem = soup.select_one('[data-automation="advertiser-name"], a[data-automation="jobCompany"]')
            if company_elem:
                job.company_name = company_elem.get_text(strip=True)
            
            # Location
            location_elem = soup.select_one('[data-automation="job-detail-location"], span[data-automation="jobLocation"]')
            if location_elem:
                job.location = location_elem.get_text(strip=True)
            
            # Job category/type
            category_elem = soup.select_one('[data-automation="job-detail-classifications"]')
            if category_elem:
                job.job_category = category_elem.get_text(strip=True)
            
            # Work type (Full time, Part time, etc.)
            work_type_elem = soup.select_one('[data-automation="job-detail-work-type"]')
            if work_type_elem:
                job.work_type = work_type_elem.get_text(strip=True)
            
            # Posted date
            date_elem = soup.select_one('[data-automation="job-detail-date"], time')
            if date_elem:
                job.posted_date = date_elem.get_text(strip=True)
            
            # Application status (e.g., "High application volume")
            status_elem = soup.select_one('[data-automation="job-detail-apply-status"]')
            if status_elem:
                job.application_status = status_elem.get_text(strip=True)
            
            # Salary
            salary_elem = soup.select_one('[data-automation="job-detail-salary"]')
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
                # Try to parse salary
                numbers = re.findall(r'[\d,]+', salary_text.replace('.', ''))
                if numbers:
                    try:
                        job.salary_min = float(numbers[0].replace(',', ''))
                        if len(numbers) > 1:
                            job.salary_max = float(numbers[1].replace(',', ''))
                    except:
                        pass
            
            # Job description - main content area
            desc_elem = soup.select_one('[data-automation="jobAdDetails"], [data-automation="jobDescription"]')
            if desc_elem:
                # Get full text with structure
                full_text = desc_elem.get_text(separator="\n", strip=True)
                job.job_description = full_text
                
                # Try to extract sections
                self._extract_sections_from_description(full_text, job)
            
            # Extract company rating and review count
            rating_elem = soup.select_one('[data-automation="company-rating"]')
            if not rating_elem:
                # Try finding rating by text pattern
                rating_text_elem = soup.find(string=re.compile(r'^\d+\.\d+$'))
                if rating_text_elem:
                    job.company_rating = rating_text_elem.strip()
            else:
                job.company_rating = rating_elem.get_text(strip=True)
            
            # Review count - often appears as a link
            review_elem = soup.find('a', string=re.compile(r'\d+\s*reviews?', re.IGNORECASE))
            if review_elem:
                job.company_review_count = review_elem.get_text(strip=True)
            
            # Company logo
            logo_elem = soup.select_one('img[alt*="Company Logo"], img[alt*="Logo for"]')
            if logo_elem:
                logo_url = logo_elem.get('src', '')
                if logo_url:
                    job.company_logo_url = logo_url
            
            # Extract employer questions
            questions_section = soup.find('h2', string=re.compile(r'Employer questions?', re.IGNORECASE))
            if questions_section:
                questions_container = questions_section.find_next('div')
                if questions_container:
                    questions_list = questions_container.find_all('li') or questions_container.find_all(['div', 'p'])
                    questions = []
                    for q in questions_list:
                        q_text = q.get_text(strip=True)
                        # Filter out non-question text
                        if q_text and len(q_text) > 10 and ('?' in q_text or any(kw in q_text.lower() for kw in ['experience', 'qualification', 'willing', 'available', 'salary'])):
                            questions.append(q_text)
                    if questions:
                        job.employer_questions = " | ".join(questions)
            
            # Extract perks and benefits (structured section)
            perks_section = soup.find(['h2', 'h3', 'h4'], string=re.compile(r'Perks and benefits?', re.IGNORECASE))
            if perks_section:
                perks_container = perks_section.find_next(['div', 'ul'])
                if perks_container:
                    perks_items = perks_container.find_all(['li', 'div', 'span'])
                    perks = []
                    for item in perks_items:
                        perk_text = item.get_text(strip=True)
                        if perk_text and len(perk_text) > 2 and perk_text not in perks:
                            # Remove bullet points
                            perk_text = perk_text.lstrip('•').strip()
                            if perk_text:
                                perks.append(perk_text)
                    if perks:
                        job.perks_benefits = " | ".join(perks)
            
            # Also try structured data
            ld_json = soup.find('script', type='application/ld+json')
            if ld_json:
                try:
                    structured = json.loads(ld_json.string)
                    if structured.get("@type") == "JobPosting":
                        if not job.job_title:
                            job.job_title = structured.get("title", "")
                        if not job.job_description:
                            job.job_description = structured.get("description", "")
                        if not job.posted_date:
                            job.posted_date = structured.get("datePosted", "")
                        
                        # Salary from structured data
                        base_salary = structured.get("baseSalary", {})
                        if base_salary:
                            value = base_salary.get("value", {})
                            if isinstance(value, dict):
                                job.salary_min = value.get("minValue")
                                job.salary_max = value.get("maxValue")
                            job.salary_currency = base_salary.get("currency", "IDR")
                        
                        # Skills
                        skills = structured.get("skills", [])
                        if skills and not job.skills_required:
                            job.skills_required = ", ".join(skills) if isinstance(skills, list) else str(skills)
                        
                        # Experience
                        exp = structured.get("experienceRequirements", "")
                        if exp and not job.experience_level:
                            job.experience_level = str(exp)
                        
                        # Education
                        edu = structured.get("educationRequirements", {})
                        if edu:
                            if isinstance(edu, dict):
                                job.education_level = edu.get("credentialCategory", "")
                            else:
                                job.education_level = str(edu)
                        
                        # Company rating from structured data
                        hiring_org = structured.get("hiringOrganization", {})
                        if isinstance(hiring_org, dict):
                            agg_rating = hiring_org.get("aggregateRating", {})
                            if isinstance(agg_rating, dict):
                                if not job.company_rating:
                                    rating = agg_rating.get("ratingValue")
                                    if rating:
                                        job.company_rating = str(rating)
                                if not job.company_review_count:
                                    review_count = agg_rating.get("reviewCount")
                                    if review_count:
                                        job.company_review_count = f"{review_count} reviews"
                except:
                    pass
            
        except Exception as e:
            logger.debug(f"Error parsing HTML: {e}")
        
        return job
    
    def _extract_sections_from_description(self, text: str, job: JobDetail) -> None:
        """Try to extract qualifications and responsibilities from description text."""
        lines = text.split('\n')
        
        current_section = None
        qualifications = []
        responsibilities = []
        benefits = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            # Detect section headers
            if any(kw in line_lower for kw in ['qualification', 'requirement', 'kualifikasi', 'persyaratan']):
                current_section = 'qualifications'
                continue
            elif any(kw in line_lower for kw in ['responsibilit', 'tanggung jawab', 'job description', 'deskripsi']):
                current_section = 'responsibilities'
                continue
            elif any(kw in line_lower for kw in ['benefit', 'keuntungan', 'offering']):
                current_section = 'benefits'
                continue
            
            # Add to current section
            if current_section == 'qualifications':
                qualifications.append(line)
            elif current_section == 'responsibilities':
                responsibilities.append(line)
            elif current_section == 'benefits':
                benefits.append(line)
        
        if qualifications:
            job.qualifications = '\n'.join(qualifications)
        if responsibilities:
            job.key_responsibilities = '\n'.join(responsibilities)
        if benefits:
            job.benefits = '\n'.join(benefits)

    def _validate_job_detail(self, job: JobDetail) -> bool:
        """Validate that minimum required fields are present."""
        # Check required fields
        if not job.job_id:
            logger.warning("  ✗ Missing job_id")
            return False

        if not job.job_url:
            logger.warning("  ✗ Missing job_url")
            return False

        if not job.job_title or len(job.job_title) < 3:
            logger.warning("  ✗ Missing or invalid job_title")
            return False

        if not job.company_name:
            logger.warning("  ✗ Missing company_name")

        # Check description length
        if not job.job_description or len(job.job_description) < 10:
            logger.warning("  ✗ Missing or too short job_description")
            return False

        return True
    
    def scrape(self) -> None:
        """Main scraping method."""
        all_jobs = self._load_job_urls()

        if not all_jobs:
            logger.error("No jobs to scrape!")
            return

        # Filter out already scraped jobs
        jobs_to_scrape = [job for job in all_jobs if job["job_id"] not in self.scraped_job_ids]

        logger.info(f"Total jobs in input: {len(all_jobs)}")
        logger.info(f"Already scraped: {len(self.scraped_job_ids)}")
        logger.info(f"Remaining to scrape: {len(jobs_to_scrape)}")

        if not jobs_to_scrape:
            logger.info("All jobs have been scraped!")
            return

        if self.max_jobs and self.max_jobs < len(jobs_to_scrape):
            jobs_to_scrape = jobs_to_scrape[:self.max_jobs]
            logger.info(f"Limiting to {self.max_jobs} jobs")

        logger.info(f"Starting detail scraper for {len(jobs_to_scrape)} jobs...")
        logger.info(f"Config: Batch size={BATCH_SIZE}, Max retries={MAX_RETRIES}, Timeout={JOB_PAGE_TIMEOUT/1000}s")

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
                    ]
                )

                context = self.browser.new_context(
                    viewport={"width": self.viewport_size[0], "height": self.viewport_size[1]},
                    user_agent=self.user_agent,
                    locale=self.browser_locale,
                    timezone_id=self.browser_timezone,
                )

                self.page = context.new_page()

                try:
                    # Visit main page first
                    logger.info("Establishing session...")
                    self.page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=self.page_load_timeout)
                    self._random_delay(self.initial_delay_multiplier)

                    batch_count = 0

                    for job_info in tqdm(jobs_to_scrape, desc="Fetching job details"):
                        job_id = job_info["job_id"]
                        job_url = job_info["job_url"]

                        job_detail = self._extract_job_details(job_id, job_url)

                        if job_detail:
                            # Add to processed list
                            self.jobs_processed.append(job_detail)
                            self.scraped_job_ids.add(job_id)
                            batch_count += 1

                            # Save job immediately to CSV
                            self.append_job_to_csv(job_detail)

                            # Save batch checkpoint
                            if batch_count % BATCH_SIZE == 0:
                                avg_time = self.session_stats['total_time'] / max(1, self.session_stats['successful_extractions'])
                                logger.info(f"  Batch {batch_count // BATCH_SIZE}: Saved {batch_count} jobs (avg: {avg_time:.1f}s/job)")
                        else:
                            logger.warning(f"✗ Failed to scrape job {job_id}")

                        self._random_delay()

                        # Clear processed jobs periodically to manage memory
                        if len(self.jobs_processed) > BATCH_SIZE * 10:
                            logger.debug(f"  Memory: Keeping last {BATCH_SIZE * 10} jobs in memory")
                            self.jobs_processed = self.jobs_processed[-BATCH_SIZE * 10:]

                finally:
                    # Clean up properly with error handling
                    cleanup_errors = []
                    if context:
                        try:
                            context.close()
                        except Exception as e:
                            cleanup_errors.append(f"Context close: {e}")
                    if self.browser:
                        try:
                            self.browser.close()
                        except Exception as e:
                            cleanup_errors.append(f"Browser close: {e}")

                    if cleanup_errors:
                        logger.warning(f"Cleanup errors: {'; '.join(cleanup_errors)}")
                    else:
                        logger.info("Browser closed")

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise
    
    def save_to_csv(self) -> None:
        """Save any remaining job details to CSV (for interrupted sessions)."""
        # Filter jobs that haven't been saved yet
        # (in case some jobs were processed but not saved due to errors)
        unsaved_jobs = []
        for job in self.jobs_processed:
            if job.job_id not in self.scraped_job_ids:
                unsaved_jobs.append(job)
        
        if not unsaved_jobs:
            logger.info("All job details already saved to CSV")
            return
        
        logger.info(f"Saving {len(unsaved_jobs)} remaining job details to CSV...")
        
        for job in unsaved_jobs:
            self.append_job_to_csv(job)
            self.scraped_job_ids.add(job.job_id)
        
        logger.info(f"Saved {len(unsaved_jobs)} additional job details to {self.output_file}")
    
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
            if self.jobs_processed:
                logger.info("Saving collected jobs despite error...")
                self.save_to_csv()
        finally:
            elapsed = time.time() - start_time
            logger.info(f"Completed in {elapsed:.1f} seconds")

            # Calculate success rate
            total_attempts = self.session_stats['successful_extractions'] + self.session_stats['failed_extractions']
            success_rate = (self.session_stats['successful_extractions'] / total_attempts * 100) if total_attempts > 0 else 0

            avg_time = self.session_stats['total_time'] / max(1, self.session_stats['successful_extractions'])

            logger.info(f"Total job details collected: {len(self.jobs_processed)}")
            logger.info(f"Total unique jobs saved: {len(self.scraped_job_ids)}")
            logger.info(f"Success rate: {success_rate:.1f}% ({self.session_stats['successful_extractions']}/{total_attempts})")
            logger.info(f"Pages loaded: {self.session_stats['pages_loaded']}")
            logger.info(f"Failed extractions: {self.session_stats['failed_extractions']}")
            logger.info(f"Retry attempts: {self.session_stats['retry_attempts']}")
            logger.info(f"CSV writes: {self.session_stats['csv_writes']}")
            logger.info(f"Average time per job: {avg_time:.1f}s")
            logger.info(f"Output file: {self.output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scrape full job details from JobStreet job pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape details from default input file
  python jobstreet_detail_scraper.py
  
  # Specify input and output files
  python jobstreet_detail_scraper.py -i jobs.csv -o details.csv
  
  # Limit number of jobs
  python jobstreet_detail_scraper.py -n 100
  
  # Run in headless mode (no browser window)
  python jobstreet_detail_scraper.py --headless
  
  # Custom delays
  python jobstreet_detail_scraper.py --min-delay 1.0 --max-delay 3.0
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        default=None,
        help=f"Input CSV file with job URLs (default: {INPUT_FILE})"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help=f"Output CSV file for job details (default: {OUTPUT_FILE})"
    )
    parser.add_argument(
        "-n", "--max-jobs",
        type=int,
        default=None,
        help="Maximum number of jobs to process (default: all jobs)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=None,
        help=f"Run browser in headless mode (default: {HEADLESS_MODE})"
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=None,
        help=f"Minimum delay between requests in seconds (default: {MIN_DELAY})"
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=None,
        help=f"Maximum delay between requests in seconds (default: {MAX_DELAY})"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=f"Page load timeout in milliseconds (default: {PAGE_LOAD_TIMEOUT})"
    )
    parser.add_argument(
        "--page-wait",
        type=float,
        default=None,
        help=f"Wait time after page load in seconds (default: {PAGE_WAIT_TIME})"
    )
    
    args = parser.parse_args()
    
    # Build delay range
    delay_range = None
    if args.min_delay is not None or args.max_delay is not None:
        min_delay = args.min_delay if args.min_delay is not None else MIN_DELAY
        max_delay = args.max_delay if args.max_delay is not None else MAX_DELAY
        delay_range = (min_delay, max_delay)
    
    scraper = JobDetailScraper(
        input_file=args.input,
        output_file=args.output,
        delay_range=delay_range,
        headless=args.headless if args.headless is not None else None,
        max_jobs=args.max_jobs,
        page_load_timeout=args.timeout,
        page_wait_time=args.page_wait,
    )
    
    scraper.run()


if __name__ == "__main__":
    main()
