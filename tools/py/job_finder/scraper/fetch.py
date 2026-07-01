"""Scraper coordinator to fetch job postings from specified URLs."""

from collections import defaultdict
from urllib.parse import urlsplit

from loguru import logger

from scraper.base import Job, browser_context
from scraper.indeed import IndeedPage
from scraper.linkedin import LinkedinPage
from scraper.stepstone import StepstonePage

EXCLUDED_COMPANIES = {
    "mindrift",
    "turing",
}

EXCLUDED_TITLE_KEYWORDS = {
    "intern",
    "student",
    "manager",
    "marketing",
}


def _filter_jobs(jobs: list[Job]) -> list[Job]:
    """Remove duplicates and filter out jobs from excluded companies and keywords.

    Args:
        jobs: List of Job instances.

    Returns:
        A list of unique Job instances not belonging to excluded companies/keywords.

    """
    logger.debug("Total jobs: {}", len(jobs))
    uniq_jobs = list(set(jobs))
    logger.debug("Unique jobs: {}", len(uniq_jobs))

    # filter for excluded companies and keywords
    filtered_jobs = []
    excluded_jobs = defaultdict(list)
    for job in uniq_jobs:
        is_excluded = False
        for company in EXCLUDED_COMPANIES:
            if company in job.company.lower():
                excluded_jobs[company].append(job)
                is_excluded = True
                break

        if is_excluded:
            continue

        for keyword in EXCLUDED_TITLE_KEYWORDS:
            if keyword in job.title.lower():
                excluded_jobs[keyword].append(job)
                is_excluded = True
                break

        if not is_excluded:
            filtered_jobs.append(job)

    for trigger, ex_jobs in excluded_jobs.items():
        logger.warning("Jobs {} excluded due to {}", len(ex_jobs), trigger)

    logger.debug("Excluded jobs count: {}", len(excluded_jobs))
    logger.debug("Filtered jobs count: {}", len(filtered_jobs))

    return filtered_jobs


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
        "www.linkedin.com": LinkedinPage,
        "www.stepstone.de": StepstonePage,
        "de.indeed.com": IndeedPage,
    }

    with browser_context() as browser:
        # first login to apply manual interactions if needed
        location_and_pages = {}
        for loc in grouped_url:
            # login via constructor
            page = page_classes[loc](browser, use_cache=use_cache)
            location_and_pages[loc] = page
            if "linkedin" in loc:
                logger.warning(
                    "Linkedin is dynamic website so browser window should be in "
                    "front otherwise it would fail to get description"
                )

        for loc, loc_urls in grouped_url.items():
            page = location_and_pages[loc]
            for url in loc_urls:
                url_jobs = page.get_jobs(url=url, limit=limit)
                logger.info("{} jobs found for {}", len(url_jobs), url)
                jobs += url_jobs

    return _filter_jobs(jobs)
