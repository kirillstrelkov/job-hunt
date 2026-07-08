"""Reviewer module to evaluate job descriptions against candidate CV."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from pprint import pformat

from loguru import logger
from reviewer.llm import analyze_cv, get_checked_passed, get_match_percentage
from tqdm import tqdm

from job_finder.scraper.base import Job
from job_finder.utils.caching_utils import get_cached_value, get_hashsum

_CV_TEXT = (Path(__file__).resolve().parent.parent / "data/private/cv.txt").read_text(encoding="utf-8")


@dataclass(frozen=True)
class JobMatch(Job):
    """Dataclass holding the results of a CV-to-job match assessment."""

    match_percentage: int = -1
    llm_text: str = ""
    check_passed: bool = False
    processed_at: datetime = field(default_factory=lambda: datetime.now(UTC), compare=False)


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
            error=job_desc.error,
            created_at=job_desc.created_at,
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
            error=job_desc.error,
            created_at=job_desc.created_at,
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
