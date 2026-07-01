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

    # remove duplicates
    uniq_jobs = list(set(jobs))
    logger.debug("Total jobs: {}, unique jobs: {}", len(jobs), len(uniq_jobs))

    # filter for excluded companies
    filtered_jobs = []
    for job in uniq_jobs:
        is_excluded = False
        for company in EXCLUDED_COMPANIES:
            if company in job.company.lower():
                logger.warning(
                    "Job '{}' from company '{}' was skipped because '{}' is in the excluded companies list.",
                    job.title,
                    job.company,
                    company,
                )
                is_excluded = True
                break
        if not is_excluded:
            filtered_jobs.append(job)

    logger.debug("Unique jobs: {}, filtered jobs: {}", len(uniq_jobs), len(filtered_jobs))

    return filtered_jobs
