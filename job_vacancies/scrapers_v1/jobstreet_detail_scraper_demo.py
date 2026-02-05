#!/usr/bin/env python3
"""
JobStreet Job Detail Scraper - DEMO/SIMULATION VERSION
This is a simulated version for video recording purposes.
It copies data from an existing CSV to create a realistic-looking scraping process.

Author: Research Assistant
Date: January 2026
"""

import csv
import random
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm

# =============================================================================
# SIMULATION PARAMETERS - CONFIGURE THESE AT THE TOP
# =============================================================================

# Input/Output files
INPUT_FILE = "job_vacancies/data/jobstreet_details.csv"
OUTPUT_FILE = "job_vacancies/data/jobstreet_details_demo.csv"
FAILED_FILE = "job_vacancies/data/jobstreet_details_demo_failed.csv"

# Delay between requests (in seconds) - random delay between min and max
MIN_DELAY = 0.1
MAX_DELAY = 0.5

# Simulation settings
SUCCESS_RATE = 0.85  # 85% success rate
MIN_DELAY_PER_JOB = 0.3  # Minimum time to simulate "scraping" a job
MAX_DELAY_PER_JOB = 1.5  # Maximum time to simulate "scraping" a job
BATCH_SIZE = 10  # Save CSV every N jobs

# Batch processing mode
BATCH_MODE = True  # If True, process in batches; if False, process one by one
BATCH_MIN_SIZE = 3  # Minimum batch size
BATCH_MAX_SIZE = 8  # Maximum batch size

# Browser configuration (for display purposes)
HEADLESS_MODE = False

# =============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class JobDetailScraperDemo:
    """
    Simulated scraper that copies data from existing CSV for demo/video purposes.
    """

    def __init__(
        self,
        input_file: str = None,
        output_file: str = None,
        delay_range: tuple = None,
        max_jobs: int = None,
        headless: bool = None,
        failed_log: str = None,
        success_rate: float = SUCCESS_RATE,
        batch_mode: bool = BATCH_MODE,
    ):
        """Initialize the demo scraper."""
        self.input_file = Path(input_file if input_file is not None else INPUT_FILE)
        self.output_file = Path(output_file if output_file is not None else OUTPUT_FILE)
        self.failed_file = Path(failed_log if failed_log is not None else FAILED_FILE)

        self.delay_range = (
            delay_range if delay_range is not None else (MIN_DELAY, MAX_DELAY)
        )
        self.headless = headless if headless is not None else HEADLESS_MODE
        self.max_jobs = max_jobs
        self.success_rate = success_rate
        self.batch_mode = batch_mode

        # Track processed job IDs
        self.scraped_job_ids: set = set()
        self.failed_job_ids: set = set()
        self.jobs_processed: List[Dict] = []

        # Session statistics
        self.session_stats = {
            "pages_loaded": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "expired_jobs": 0,
            "validation_failures": 0,
            "retry_attempts": 0,
            "total_time": 0,
        }

        # Load existing job IDs from CSV if it exists
        self._load_existing_job_ids()
        self._load_failed_job_ids()

        logger.info(f"Demo scraper initialized. Input: {self.input_file}")
        logger.info(f"Output: {self.output_file}")
        logger.info(f"Failed job log: {self.failed_file}")
        logger.info(f"Existing jobs in CSV: {len(self.scraped_job_ids)}")
        logger.info(f"Previously failed jobs: {len(self.failed_job_ids)}")

    def _random_delay(self, multiplier: float = 1.0) -> None:
        """Add random delay."""
        delay = random.uniform(*self.delay_range) * multiplier
        time.sleep(delay)

    def _load_existing_job_ids(self) -> None:
        """Load existing job IDs from output CSV file."""
        if not self.output_file.exists():
            return

        try:
            with open(self.output_file, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    job_id = row.get("job_id", "").strip()
                    if job_id:
                        self.scraped_job_ids.add(job_id)
            logger.info(
                f"Loaded {len(self.scraped_job_ids)} existing job IDs from {self.output_file}"
            )
        except Exception as e:
            logger.warning(f"Could not load existing job IDs: {e}")

    def _load_failed_job_ids(self) -> None:
        """Load previously failed job IDs from failed jobs file."""
        if not self.failed_file.exists():
            logger.debug(f"No failed jobs file found: {self.failed_file}")
            return

        try:
            with open(self.failed_file, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    job_id = row.get("job_id", "").strip()
                    if job_id:
                        self.failed_job_ids.add(job_id)
            logger.info(f"Loaded {len(self.failed_job_ids)} previously failed job IDs")
        except Exception as e:
            logger.warning(f"Could not load failed job IDs: {e}")

    def _create_csv_if_not_exists(self) -> None:
        """Create CSV file with headers if it doesn't exist."""
        if self.output_file.exists():
            return

        # Read headers from input file
        if not self.input_file.exists():
            logger.error(f"Input file not found: {self.input_file}")
            return

        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        with open(self.output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

        logger.info(f"Created new CSV file: {self.output_file}")

    def _create_failed_csv_if_not_exists(self) -> None:
        """Create failed jobs CSV file with headers if it doesn't exist."""
        if self.failed_file.exists():
            return

        self.failed_file.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["job_id", "job_url", "failure_reason", "failed_at"]

        with open(self.failed_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

        logger.debug(f"Created failed jobs file: {self.failed_file}")

    def append_job_to_csv(self, job: Dict) -> None:
        """Append a single job detail to the CSV file."""
        self._create_csv_if_not_exists()

        # Read headers from input file
        with open(self.input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        try:
            # Clean up multiline fields to prevent CSV issues
            job_dict = job.copy()
            for key, value in job_dict.items():
                if isinstance(value, str) and "\n" in value:
                    job_dict[key] = value.replace("\n", " | ")

            with open(self.output_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writerow(job_dict)
        except Exception as e:
            logger.error(f"Failed to append job {job.get('job_id')} to CSV: {e}")

    def _save_failed_job(self, job_id: str, job_url: str, reason: str) -> None:
        """Save a failed job to the failed jobs CSV."""
        self._create_failed_csv_if_not_exists()

        try:
            with open(self.failed_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["job_id", "job_url", "failure_reason", "failed_at"],
                    quoting=csv.QUOTE_ALL,
                )
                writer.writerow(
                    {
                        "job_id": job_id,
                        "job_url": job_url,
                        "failure_reason": reason,
                        "failed_at": datetime.now().isoformat(),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to save failed job {job_id}: {e}")

    def _simulate_job_scraping(self, job_id: str, job_url: str) -> Dict:
        """Simulate the process of scraping a single job."""
        job_start_time = time.time()

        # Simulate page load time
        self.session_stats["pages_loaded"] += 1
        load_delay = random.uniform(MIN_DELAY_PER_JOB, MAX_DELAY_PER_JOB)
        time.sleep(load_delay)

        # Determine if this job should "succeed" or "fail"
        success = random.random() < self.success_rate

        if success:
            # Simulate successful extraction
            self.session_stats["successful_extractions"] += 1
            job_time = time.time() - job_start_time
            self.session_stats["total_time"] += job_time

            # Find and return the job data from input file
            job_data = self._find_job_by_id(job_id)
            if job_data:
                logger.debug(
                    f"✓ Extracted {job_id}: {job_data.get('job_title', '')[:40]}... in {job_time:.1f}s"
                )
                return job_data
            else:
                logger.warning(f"Job {job_id} not found in input file")
                self.session_stats["failed_extractions"] += 1
                return None
        else:
            # Simulate failure
            self.session_stats["failed_extractions"] += 1
            error_type = random.choice(["timeout", "network", "validation", "expired"])
            error_msgs = {
                "timeout": "Timeout waiting for page to load",
                "network": "Network connection reset",
                "validation": "Validation failed: missing required fields",
                "expired": "Job has expired or been removed (404)",
            }

            error_msg = error_msgs[error_type]
            logger.warning(f"✗ Failed to scrape {job_id}: {error_msg}")

            if error_type == "expired":
                self.session_stats["expired_jobs"] += 1
            elif error_type == "validation":
                self.session_stats["validation_failures"] += 1

            # Log to failed jobs file
            self._save_failed_job(job_id, job_url, error_msg)
            return None

    def _find_job_by_id(self, job_id: str) -> Dict:
        """Find a job by ID in the input CSV."""
        if not self.input_file.exists():
            return None

        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("job_id") == job_id:
                        return row
        except Exception as e:
            logger.error(f"Error reading input file: {e}")

        return None

    def _load_job_data(self) -> List[Dict]:
        """Load all job data from input CSV."""
        jobs = []

        if not self.input_file.exists():
            logger.error(f"Input file not found: {self.input_file}")
            return jobs

        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    job_id = row.get("job_id", "").strip()
                    job_url = row.get("job_url", "").strip()
                    if job_id and job_url:
                        jobs.append({"job_id": job_id, "job_url": job_url, "data": row})

            logger.info(f"Loaded {len(jobs)} jobs from {self.input_file}")
        except Exception as e:
            logger.error(f"Error loading jobs from CSV: {e}")

        return jobs

    def scrape(self) -> None:
        """Main scraping simulation method."""
        all_jobs = self._load_job_data()

        if not all_jobs:
            logger.error("No jobs to process!")
            return

        # Filter out already processed jobs
        jobs_to_process = [
            job
            for job in all_jobs
            if job["job_id"] not in self.scraped_job_ids
            and job["job_id"] not in self.failed_job_ids
        ]

        logger.info(f"Total jobs in input: {len(all_jobs)}")
        logger.info(f"Already processed: {len(self.scraped_job_ids)}")
        logger.info(f"Previously failed: {len(self.failed_job_ids)}")
        logger.info(f"Total candidate jobs: {len(jobs_to_process)}")

        if not jobs_to_process:
            logger.info("All jobs have been processed!")
            return

        if self.max_jobs and self.max_jobs < len(jobs_to_process):
            jobs_to_process = jobs_to_process[: self.max_jobs]
            logger.info(f"Limiting to {self.max_jobs} jobs")

        logger.info(f"Starting demo scraper for {len(jobs_to_process)} jobs...")
        logger.info(
            f"Config: Success rate={self.success_rate * 100}%, Batch size={BATCH_SIZE}"
        )
        logger.info(
            f"Mode: {'Batch processing' if self.batch_mode else 'Sequential processing'}"
        )

        batch_count = 0

        if self.batch_mode:
            # Process in batches
            progress_bar = tqdm(jobs_to_process, desc="Processing job batches")
            remaining_jobs = jobs_to_process.copy()

            while remaining_jobs:
                # Random batch size
                batch_size = random.randint(BATCH_MIN_SIZE, BATCH_MAX_SIZE)
                current_batch = remaining_jobs[:batch_size]
                remaining_jobs = remaining_jobs[batch_size:]

                logger.info(f"Processing batch of {len(current_batch)} jobs...")

                for job_info in current_batch:
                    job_id = job_info["job_id"]
                    job_url = job_info["job_url"]

                    job_data = self._simulate_job_scraping(job_id, job_url)

                    if job_data:
                        self.jobs_processed.append(job_data)
                        self.scraped_job_ids.add(job_id)
                        batch_count += 1

                        # Save job immediately to CSV
                        self.append_job_to_csv(job_data)

                        # Save batch checkpoint
                        if batch_count % BATCH_SIZE == 0:
                            avg_time = self.session_stats["total_time"] / max(
                                1, self.session_stats["successful_extractions"]
                            )
                            logger.info(
                                f"  Batch {batch_count // BATCH_SIZE}: Saved {batch_count} jobs (avg: {avg_time:.1f}s/job)"
                            )

                        progress_bar.update(1)

                # Delay between batches
                if remaining_jobs:
                    self._random_delay()

            progress_bar.close()
        else:
            # Process one by one
            for job_info in tqdm(jobs_to_process, desc="Fetching job details"):
                job_id = job_info["job_id"]
                job_url = job_info["job_url"]

                job_data = self._simulate_job_scraping(job_id, job_url)

                if job_data:
                    self.jobs_processed.append(job_data)
                    self.scraped_job_ids.add(job_id)
                    batch_count += 1

                    # Save job immediately to CSV
                    self.append_job_to_csv(job_data)

                    # Save batch checkpoint
                    if batch_count % BATCH_SIZE == 0:
                        avg_time = self.session_stats["total_time"] / max(
                            1, self.session_stats["successful_extractions"]
                        )
                        logger.info(
                            f"  Batch {batch_count // BATCH_SIZE}: Saved {batch_count} jobs (avg: {avg_time:.1f}s/job)"
                        )

                self._random_delay()

                # Clear processed jobs periodically to manage memory
                if len(self.jobs_processed) > BATCH_SIZE * 10:
                    logger.debug(
                        f"  Memory: Keeping last {BATCH_SIZE * 10} jobs in memory"
                    )
                    self.jobs_processed = self.jobs_processed[-BATCH_SIZE * 10 :]

    def save_to_csv(self) -> None:
        """Save any remaining job details to CSV (for interrupted sessions)."""
        unsaved_jobs = []
        for job in self.jobs_processed:
            if job.get("job_id") not in self.scraped_job_ids:
                unsaved_jobs.append(job)

        if not unsaved_jobs:
            logger.info("All job details already saved to CSV")
            return

        logger.info(f"Saving {len(unsaved_jobs)} remaining job details to CSV...")

        for job in unsaved_jobs:
            self.append_job_to_csv(job)
            self.scraped_job_ids.add(job.get("job_id"))

        logger.info(
            f"Saved {len(unsaved_jobs)} additional job details to {self.output_file}"
        )

    def run(self) -> None:
        """Run the complete scraping process."""
        start_time = time.time()

        try:
            self.scrape()
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

            # Calculate success rate
            total_attempts = (
                self.session_stats["successful_extractions"]
                + self.session_stats["failed_extractions"]
            )
            success_rate = (
                (self.session_stats["successful_extractions"] / total_attempts * 100)
                if total_attempts > 0
                else 0
            )

            avg_time = self.session_stats["total_time"] / max(
                1, self.session_stats["successful_extractions"]
            )

            logger.info(f"Completed in {elapsed:.1f} seconds")
            logger.info(f"Total job details collected: {len(self.jobs_processed)}")
            logger.info(f"Total unique jobs saved: {len(self.scraped_job_ids)}")
            logger.info(
                f"Success rate: {success_rate:.1f}% ({self.session_stats['successful_extractions']}/{total_attempts})"
            )
            logger.info(f"Expired/removed jobs: {self.session_stats['expired_jobs']}")
            logger.info(
                f"Validation failures: {self.session_stats['validation_failures']}"
            )
            logger.info(f"Pages loaded: {self.session_stats['pages_loaded']}")
            logger.info(
                f"Failed extractions: {self.session_stats['failed_extractions']}"
            )
            logger.info(f"Retry attempts: {self.session_stats['retry_attempts']}")
            logger.info(f"Average time per job: {avg_time:.1f}s")
            logger.info(f"Output file: {self.output_file}")
            logger.info(f"Failed jobs log: {self.failed_file}")
            if self.session_stats["expired_jobs"] > 0:
                logger.info(
                    f"  Note: Expired jobs logged to {self.failed_file} and will be skipped in future runs"
                )


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="DEMO/SIMULATION: Copy job data from existing CSV (for video recording)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run demo with default settings
  python jobstreet_detail_scraper_demo.py

  # Specify input and output files
  python jobstreet_detail_scraper_demo.py -i input.csv -o output.csv

  # Limit number of jobs
  python jobstreet_detail_scraper_demo.py -n 50

  # Set success rate (lower means more failures)
  python jobstreet_detail_scraper_demo.py --success-rate 0.70

  # Use sequential processing (no batches)
  python jobstreet_detail_scraper_demo.py --no-batch
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        default=None,
        help=f"Input CSV file with job data (default: {INPUT_FILE})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help=f"Output CSV file for job details (default: {OUTPUT_FILE})",
    )
    parser.add_argument(
        "-n",
        "--max-jobs",
        type=int,
        default=None,
        help="Maximum number of jobs to process (default: all jobs)",
    )
    parser.add_argument(
        "--success-rate",
        type=float,
        default=SUCCESS_RATE,
        help=f"Success rate for simulation (default: {SUCCESS_RATE})",
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=None,
        help=f"Minimum delay between requests in seconds (default: {MIN_DELAY})",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=None,
        help=f"Maximum delay between requests in seconds (default: {MAX_DELAY})",
    )
    parser.add_argument(
        "--no-batch",
        action="store_true",
        help="Disable batch processing, process one by one",
    )
    parser.add_argument(
        "--batch-mode", action="store_true", help="Force batch processing mode"
    )
    parser.add_argument(
        "--failed-log",
        type=str,
        default=None,
        help=f"Failed jobs CSV file (default: {FAILED_FILE})",
    )

    args = parser.parse_args()

    # Build delay range
    delay_range = None
    if args.min_delay is not None or args.max_delay is not None:
        min_delay = args.min_delay if args.min_delay is not None else MIN_DELAY
        max_delay = args.max_delay if args.max_delay is not None else MAX_DELAY
        delay_range = (min_delay, max_delay)

    # Determine batch mode
    batch_mode = BATCH_MODE
    if args.no_batch:
        batch_mode = False
    elif args.batch_mode:
        batch_mode = True

    scraper = JobDetailScraperDemo(
        input_file=args.input,
        output_file=args.output,
        delay_range=delay_range,
        max_jobs=args.max_jobs,
        headless=False,
        failed_log=args.failed_log,
        success_rate=args.success_rate,
        batch_mode=batch_mode,
    )

    scraper.run()


if __name__ == "__main__":
    main()
