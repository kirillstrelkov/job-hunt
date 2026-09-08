"""LLM integration using direct Ollama chat for Resume and job description screening."""

import json
from pathlib import Path

import ollama
from loguru import logger
from opentelemetry.trace import StatusCode
from phoenix.otel import SpanAttributes
from pydantic import BaseModel

from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.core.ollama_helper import get_model_options
from job_hunt.core.telemetry import get_tracer

from .models import Analysis, JobMatchResult, Screening

tracer = get_tracer("job-finder-reviewer")


def _read_prompt(filename: str, schema_model: type[BaseModel] | None = None) -> str:
    """Read a markdown prompt file and optionally inject the model JSON schema."""
    content = (Path(__file__).parent / "prompts" / filename).read_text(encoding="utf-8")
    if schema_model:
        content = content.format(schema=json.dumps(schema_model.model_json_schema()))
    return content.strip() + "\n"


SYSTEM_PROMPT_SCREENING = _read_prompt("screening_system.md", Screening)
SYSTEM_PROMPT_CANDIDATE = _read_prompt("candidate_system.md", Analysis)
JD_PROMPT = _read_prompt("jd.md")
RESUME_PROMPT = _read_prompt("resume.md")

MODEL = DEFAULT_CONFIG.llm.fix_model


def _create_prompt(system: str | None = None, user: str | None = None) -> dict:
    if system:
        return {"role": "system", "content": system}
    if user:
        return {"role": "user", "content": user}
    msg = "system or user should be used"
    raise ValueError(msg)


def llm_send(*prompts: dict, model: str = MODEL) -> str:
    """Send a prompt + content to Ollama."""
    with tracer.start_as_current_span("llm_send") as span:
        options = get_model_options(model)
        span.set_attributes(
            {
                SpanAttributes.LLM_MODEL_NAME: model,
                SpanAttributes.INPUT_VALUE: str(prompts),
                SpanAttributes.LLM_INVOCATION_PARAMETERS: str(options),
            }
        )
        try:
            response = ollama.chat(
                model=model,
                messages=prompts,
                options=options,
            )
            response_content = response["message"]["content"]
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, response_content)
            span.set_status(StatusCode.OK)
            return response_content
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            logger.error(f"LLM Error: {e}")
            return ""


def _get_screening(job_description: str, model: str = MODEL) -> Screening:
    prompts = [
        _create_prompt(system=SYSTEM_PROMPT_SCREENING),
        _create_prompt(user=JD_PROMPT.format(job_description=job_description.strip())),
    ]
    raw = llm_send(*prompts, model=model)
    return Screening.model_validate_json(raw)


def _get_analysis(resume: str, job_description: str, model: str = MODEL) -> Analysis:
    user_content = (
        f"{RESUME_PROMPT.format(resume=resume.strip())}\n{JD_PROMPT.format(job_description=job_description.strip())}"
    )
    prompts = [
        _create_prompt(system=SYSTEM_PROMPT_CANDIDATE),
        _create_prompt(user=user_content),
    ]
    raw = llm_send(*prompts, model=model)
    return Analysis.model_validate_json(raw)


def analyze_resume(resume: str, job_description: str, model: str = MODEL, use_pydantic: bool = False) -> JobMatchResult:
    """Analyze a Resume against a job description using LLM.

    Args:
        resume: Full Resume text
        job_description: Full job description text
        model: Optional model override
        use_pydantic: If True, delegate to the Pydantic AI (run_model) pipeline.

    Returns:
        Parsed result with screening and (if gate passed) analysis sections

    """
    if use_pydantic:
        from . import llm_with_pydantic

        return llm_with_pydantic.analyze_resume(resume, job_description, model=model)

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


def review_job(
    job_description: str,
    resume: str | None = None,
    model: str = MODEL,
    use_pydantic: bool = False,
) -> int:
    """Review role match for a single job description and return match score."""
    if resume is None:
        resume = DEFAULT_CONFIG.composer.body.read_text(encoding="utf-8")
    result = analyze_resume(resume, job_description, model=model, use_pydantic=use_pydantic)
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
    "llm_send",
    "review_job",
]
