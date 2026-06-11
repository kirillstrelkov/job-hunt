"""Main command-line interface for running the CV-job matching pipeline."""

import argparse
import json
import sys
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from urllib.parse import urlsplit

# Add parent directory to path so relative imports work when executed directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import yaml
from loguru import logger
from tqdm import tqdm

from caching_utils import get_cached_value, get_hashsum
from llm import analyze_cv, get_checked_passed, get_match_percentage
from pages.base import Job, browser_context
from pages.indeed import IndeedPage
from pages.linkedin import LinkedinPage
from pages.stepstone import StepstonePage

_CV_TEXT = (Path(__file__).parent.parent / "data/private/cv.txt").read_text(encoding="utf-8")
_OUTPUT_PATH = Path(tempfile.gettempdir()) / "job_matches.csv"

EXCLUDED_COMPANIES = {
    "mindrift",
    "turing",
}


@dataclass
class JobMatch:
    """Dataclass holding the results of a CV-to-job match assessment."""

    url: str
    title: str
    company: str
    description: str
    match_percentage: int
    llm_text: str
    check_passed: bool


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

    return filtered_jobs


def _match_cv_and_job_desc(job_desc: Job) -> JobMatch:
    """Evaluate a single job description against the candidate's CV.

    Args:
        job_desc: The job description model to evaluate.

    Returns:
        A JobMatch containing match metadata.

    """

    def _get() -> JobMatch:
        """Call the LLM to get the CV evaluation."""
        res = analyze_cv(_CV_TEXT, job_desc.description)
        match = get_match_percentage(res)
        check_passed = get_checked_passed(res)

        return JobMatch(
            title=job_desc.title,
            company=job_desc.company,
            url=job_desc.url,
            description=job_desc.description,
            match_percentage=match,
            llm_text=json.dumps(res, indent=2, ensure_ascii=False),
            check_passed=check_passed,
        )

    hs = get_hashsum(job_desc.url, "match")
    try:
        return get_cached_value(hs, _get)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error matching CV and job description from {job_desc.url}: {e}")
        return JobMatch(
            title=job_desc.title,
            company=job_desc.company,
            url=job_desc.url,
            description=job_desc.description,
            match_percentage=-1,
            llm_text="",
            check_passed=False,
        )


def get_job_matches(jobs: list[Job]) -> list[JobMatch]:
    """Assess matches for a list of job descriptions.

    Args:
        jobs: List of job descriptions to check.

    Returns:
        List of match assessments.

    """
    return [_match_cv_and_job_desc(jd) for jd in tqdm(jobs)]


def create_save_df(objects: list[Job | JobMatch], sort_by: str, output: Path, *, ascending: bool = True) -> None:
    """Create a DataFrame from a list of objects, sort, and save it to a CSV file.

    Args:
        objects: List of objects (Job or JobMatch).
        sort_by: Column name to sort the DataFrame by.
        output: CSV destination file path.
        ascending: True to sort ascending, False for descending.

    """
    if not objects:
        msg = "No matches found"
        raise ValueError(msg)

    data = [asdict(item) if is_dataclass(item) else item for item in objects]
    df = pd.DataFrame(data).sort_values(by=sort_by, ascending=ascending)
    df.to_csv(output, index=False)
    logger.info(f"Saved to {output}")


def _main(urls: list[str], output: Path = _OUTPUT_PATH, *, use_cache: bool = True) -> None:
    """Execute the matching pipeline from a list of URLs to CSV output.

    Args:
        urls: List of job/search URLs.
        output: Path to save the CSV matches.
        use_cache: If True, use cached matches/jobs.

    """
    jobs_file = output.with_name("jobs.csv")

    if jobs_file.exists():
        logger.info(f"Loading jobs from {jobs_file}")
        df = pd.read_csv(jobs_file).fillna("")
        jobs = [Job(**row) for row in df.to_dict(orient="records")]
    else:
        logger.info("Fetching jobs...")
        jobs = get_jobs(*urls, use_cache=use_cache)
        create_save_df(jobs, sort_by="url", output=jobs_file, ascending=True)

    if output.exists():
        logger.info(f"Output file {output} already exists, skipping match analysis.")
    else:
        logger.info("Analyzing matches...")
        # filter failed ones and sort by url - to have proper hash
        jobs = sorted([j for j in jobs if j.description.strip()], key=lambda j: j.url)
        matches = get_job_matches(jobs)
        create_save_df(matches, sort_by="match_percentage", output=output, ascending=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some job URLs from a YAML file.")
    parser.add_argument("yaml_path", type=str, help="Path to the YAML file containing job URLs")
    parser.add_argument("--no-cache", action="store_true", help="Do not cache results")
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set log level"
    )

    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level=args.log_level)

    urls = yaml.safe_load(Path(args.yaml_path).read_text(encoding="utf-8"))

    _main(urls, use_cache=not args.no_cache)
