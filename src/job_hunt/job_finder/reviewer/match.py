"""Reviewer module to evaluate job descriptions against candidate Resume."""

from pathlib import Path

from loguru import logger
from tqdm import tqdm

from job_hunt.job_finder.reviewer.llm import analyze_resume, get_checked_passed, get_match_percentage
from job_hunt.job_finder.utils.caching_utils import get_cached_value, get_hashsum
from job_hunt.job_finder.utils.models import Job, JobMatch

_RESUME_TEXT = (Path(__file__).resolve().parent.parent / "data/private/cv.txt").read_text(encoding="utf-8")


def _match_resume_and_job_desc(job_desc: Job) -> JobMatch:
    """Evaluate a single job description against the candidate's Resume.

    Args:
        job_desc: The job description model to evaluate.

    Returns:
        A JobMatch containing match metadata.

    """

    def _get() -> JobMatch:
        """Call the LLM to get the Resume evaluation."""
        res = analyze_resume(_RESUME_TEXT, job_desc.description)
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
            llm_text=res.model_dump_json(indent=2),
            check_passed=check_passed,
        )

    hs = get_hashsum(job_desc.url, "match")
    try:
        return get_cached_value(hs, _get)
    except Exception as e:
        logger.error(f"Error matching Resume and job description from {job_desc.url}: {e}")
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
    return [_match_resume_and_job_desc(jd) for jd in tqdm(jobs)]
