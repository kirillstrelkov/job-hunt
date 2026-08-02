"""Scraper coordinator to fetch job postings from specified URLs."""

from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd
from loguru import logger

from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.job_finder.scraper.base import Job, browser_context
from job_hunt.job_finder.scraper.indeed import IndeedBoard
from job_hunt.job_finder.scraper.linkedin import LinkedinBoard
from job_hunt.job_finder.scraper.stepstone import StepstoneBoard

_SCRAPER = DEFAULT_CONFIG.scraper
_EXCLUDED_COMPANIES = set(_SCRAPER.excluded_companies)
_EXCLUDED_TITLE_KEYWORDS = set(_SCRAPER.excluded_title_keywords)


def _load_scraped_jobs(jobs_path: Path) -> list[Job]:
    """Load and return the list of previously scraped jobs from the CSV file."""
    if not jobs_path.exists():
        return []

    df = pd.read_csv(jobs_path).fillna("")
    return [Job(**row) for row in df.to_dict(orient="records")]


def _filter_jobs(jobs: list[Job]) -> list[Job]:
    """Remove duplicates, filter out jobs from excluded companies/keywords, and skip already scraped jobs by URL.

    Args:
        jobs: List of Job instances.

    Returns:
        A list of unique Job instances not belonging to excluded companies/keywords or already scraped.

    """
    logger.debug("Total jobs: {}", len(jobs))
    uniq_jobs = list(set(jobs))
    logger.debug("Unique jobs: {}", len(uniq_jobs))

    # Load already scraped jobs to filter by URL
    scraped_jobs = _load_scraped_jobs(Path(_SCRAPER.jobs_path))
    scraped_urls = {j.url for j in scraped_jobs}

    # filter for excluded companies, keywords, and already scraped URLs
    skipped_by_url_count = 0

    for job in uniq_jobs:
        if job.url in scraped_urls:
            skipped_by_url_count += 1
            continue

    logger.debug("Skipped {} jobs already present in scraped_jobs", skipped_by_url_count)

    return uniq_jobs


def get_jobs(*urls: str, limit: None | int = None, use_cache: bool = False) -> list[Job]:
    """Retrieve job descriptions from a list of URLs using respective scrapers.

    Args:
        *urls: One or more job listing/search URLs.
        limit: Maximum number of jobs to fetch per site.
        use_cache: If True, use cached job details if available.

    Returns:
        A list of unique Job instances fetched from the URLs.

    """
    jobs = []
    loc_and_urls = [(urlsplit(url).netloc, url) for url in urls]

    grouped_url = defaultdict(list)
    for loc, url in loc_and_urls:
        grouped_url[loc].append(url)

    page_classes = {
        "www.linkedin.com": LinkedinBoard,
        "www.stepstone.de": StepstoneBoard,
        "de.indeed.com": IndeedBoard,
    }

    with browser_context() as browser:
        # first login to apply manual interactions if needed
        location_and_pages = {}
        for loc in grouped_url:
            # login via constructor
            page = page_classes[loc](
                browser,
                use_cache=use_cache,
                excluded_companies=_EXCLUDED_COMPANIES,
                excluded_title_keywords=_EXCLUDED_TITLE_KEYWORDS,
            )
            location_and_pages[loc] = page
            if "linkedin" in loc:
                logger.warning(
                    "Linkedin is dynamic website so browser window should be in "
                    "front otherwise it would fail to get description"
                )

        loc_order = [
            "www.linkedin.com",
            "www.stepstone.de",
            "de.indeed.com",
        ]

        for loc in loc_order:
            loc_urls = grouped_url.get(loc)
            if not loc_urls:
                continue

            page = location_and_pages[loc]
            for url in loc_urls:
                url_jobs = page.get_all_jobs(url=url, limit=limit)
                logger.info("{} jobs found for {}", len(url_jobs), url)
                jobs += url_jobs

    return _filter_jobs(jobs)
