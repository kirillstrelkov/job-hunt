"""LLM integration using Pydantic AI (run_model) for Resume and job description screening and analysis."""

from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.core.llm import run_model
from job_hunt.core.llm_helper import get_eval_model

from .llm import (
    JD_PROMPT,
    RESUME_PROMPT,
    SYSTEM_PROMPT_CANDIDATE,
    SYSTEM_PROMPT_SCREENING,
)
from .models import Analysis, JobMatchResult, Screening

MODEL = get_eval_model()


def _get_screening(job_description: str, model: str = MODEL) -> Screening:
    result = run_model(
        model_name=model,
        output_type=Screening,
        user_prompt=JD_PROMPT.format(job_description=job_description.strip()),
        system_prompt=SYSTEM_PROMPT_SCREENING,
    )
    return result.output


def _get_analysis(resume: str, job_description: str, model: str = MODEL) -> Analysis:
    user_prompt = (
        f"{RESUME_PROMPT.format(resume=resume.strip())}\n{JD_PROMPT.format(job_description=job_description.strip())}"
    )
    result = run_model(
        model_name=model,
        output_type=Analysis,
        user_prompt=user_prompt,
        system_prompt=SYSTEM_PROMPT_CANDIDATE,
    )
    return result.output


def analyze_resume(resume: str, job_description: str, model: str = MODEL) -> JobMatchResult:
    """Analyze a Resume against a job description using Pydantic AI.

    Args:
        resume: Full Resume text
        job_description: Full job description text
        model: Optional model override

    Returns:
        Parsed result with screening and (if gate passed) analysis sections

    """
    try:
        screening = _get_screening(job_description, model=model)
    except Exception as e:
        return JobMatchResult(error=str(e))

    if screening.gate_passed:
        try:
            analysis = _get_analysis(resume, job_description, model=model)
        except Exception as e:
            return JobMatchResult(error=str(e))
    else:
        analysis = None

    return JobMatchResult(screening=screening, analysis=analysis)


def get_match_percentage(result: JobMatchResult) -> int:
    """Return match percentage from analyzed data, or -1 if analysis is absent."""
    if result.analysis:
        return result.analysis.match_percentage
    return -1


def get_checked_passed(result: JobMatchResult) -> bool:
    """Return whether the screening gate passed."""
    if result.screening:
        return result.screening.gate_passed
    return False


def review_job(job_description: str, resume: str | None = None, model: str = MODEL) -> int:
    """Review role match for a single job description using Pydantic AI."""
    if resume is None:
        resume = DEFAULT_CONFIG.composer.body.read_text(encoding="utf-8")
    result = analyze_resume(resume, job_description, model=model)
    return get_match_percentage(result)


__all__ = [
    "Analysis",
    "JD_PROMPT",
    "JobMatchResult",
    "MODEL",
    "RESUME_PROMPT",
    "SYSTEM_PROMPT_CANDIDATE",
    "SYSTEM_PROMPT_SCREENING",
    "Screening",
    "_get_analysis",
    "_get_screening",
    "analyze_resume",
    "get_checked_passed",
    "get_match_percentage",
    "review_job",
]
