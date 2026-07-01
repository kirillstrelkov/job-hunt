"""Reviewer module to evaluate job descriptions against candidate CV."""

from dataclasses import dataclass
from pathlib import Path
from pprint import pformat

from loguru import logger
from job_finder.scraper.base import Job
from tqdm import tqdm
from job_finder.utils.caching_utils import get_cached_value, get_hashsum

from reviewer.llm import analyze_cv, get_checked_passed, get_match_percentage

_CV_TEXT = (Path(__file__).resolve().parent.parent / "data/private/cv.txt").read_text(encoding="utf-8")


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
            llm_text=pformat(res),
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
