"""LLM integration for CV and job description screening and analysis."""

import json
import os
import tempfile
from pathlib import Path

import ollama
from loguru import logger

from .llm_with_pydantic import Analysis, JobMatchResult, Screening

from helpers.telemetry import OpenInferenceSpanKindValues, SpanAttributes, StatusCode, get_tracer

tracer = get_tracer("job-finder-reviewer")


# Fallback model: "gemma4:e2b"
MODEL = "gemma4:e4b-it-qat"

_DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

HEADER_PROMPT = """
You are a professional technical reverse recruiter.

Return ONLY valid JSON — no markdown fences, no commentary.

"""
SYSTEM_PROMPT_SCREENING = f"""
{HEADER_PROMPT}

Analyze the job description.

Evaluate the following:
1. is_german_text        — Is more than 80%% of the text written in Requirements and
   Responsibilities sections, in German?
2. is_german_required    — Is German language listed as a must-have, required, or essential skill?
   (Ignore if listed as a plus or advantage.)
3. is_manager            — Is the position for a manager role? (Select true for any roles with "Manager"
   in the title, such as Product Manager, Marketing Manager)
4. is_staff              — Is "staff engineer" or "lead engineer" (case-insensitive, e.g., "Staff Engineer")
   mentioned explicitly? Do NOT imply or infer — only mark true if stated verbatim.
5. is_contract           — Is the position temporary, contract-based, or for freelancers?
6. is_excluded_role      — Is the role a Data Scientist, intern, internship, Werkstudent, or trainee
   position? Match case-insensitively.

After evaluating, produce this object. Use the "reasoning" field to briefly explain your
findings before outputting the boolean flags:

```json

{json.dumps(Screening.model_json_schema())}

```

Set "gate_passed" to true only if ALL flags are false.
Populate "gate_failed_reasons" with the names of any flags that are true
(e.g. ["is_german_required", "is_excluded_role"]).
"""
SYSTEM_PROMPT_CANDIDATE = f"""
{HEADER_PROMPT}

Analyze the CV against the job description.

All percentages are integers 0-100. Every field must be populated — use null only if the
information is genuinely absent. Base every judgment strictly on the provided documents.

The final JSON output must be:

```json
{json.dumps(Analysis.model_json_schema())}
```
"""

CV_PROMPT = """
CV:
<cv>
{cv}
</cv>
"""
JD_PROMPT = """
Job description:
<job_description>
{job_description}
</job_description>
"""


def _create_prompt(system: None | str = None, user: str | None = None) -> dict:
    if system:
        return {"role": "system", "content": system}

    if user:
        return {"role": "user", "content": user}

    msg = "system or user should be used"
    raise ValueError(msg)


def llm_send(*prompts: dict, model: str = MODEL) -> str:
    """Send a prompt + content to Ollama."""
    content = "-----\n".join([p["content"] for p in prompts])
    path = Path(tempfile.gettempdir()) / "llm_prompt_debug.txt"
    path.write_text(content)

    with tracer.start_as_current_span("llm_send") as span:
        options = {
            "temperature": 0,
            "num_ctx": 16384,
            "num_predict": 3072,
            "seed": 42,
        }

        span.set_attributes(
            {
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
                SpanAttributes.LLM_MODEL_NAME: model,
                SpanAttributes.INPUT_VALUE: str(prompts),
                SpanAttributes.LLM_INVOCATION_PARAMETERS: str(options),
                SpanAttributes.LLM_REQUEST_INPUT_TEXT: str(prompts),
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
        except Exception as e:  # noqa: BLE001
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


def _get_analysis(cv: str, job_description: str, model: str = MODEL) -> Analysis:
    prompts = [
        _create_prompt(system=SYSTEM_PROMPT_CANDIDATE),
        _create_prompt(user=CV_PROMPT.format(cv=cv.strip())),
        _create_prompt(user=JD_PROMPT.format(job_description=job_description.strip())),
    ]
    raw = llm_send(*prompts, model=model)

    return Analysis.model_validate_json(raw)


def analyze_cv(cv: str, job_description: str, model: str = MODEL) -> JobMatchResult:
    """Analyze a CV against a job description using LLM.

    Args:
        cv: Full CV text
        job_description: Full job description text
        model: Optional model override

    Returns:
        Parsed JSON result with screening and (if gate passed) analysis sections

    """
    try:
        screening = _get_screening(job_description, model=model)
    except Exception as e:  # noqa: BLE001
        return JobMatchResult(error=str(e))

    if screening.gate_passed:
        try:
            analysis = _get_analysis(cv, job_description, model=model)
        except Exception as e:  # noqa: BLE001
            return JobMatchResult(error=str(e))
    else:
        analysis = None

    return JobMatchResult(screening=screening, analysis=analysis)


def get_match_percentage(result: JobMatchResult) -> int:
    """Return percentage from analyzed data."""
    if result.analysis:
        return result.analysis.match_percentage
    return 0


def get_checked_passed(result: JobMatchResult) -> bool:
    """Return whether the screening gate passed."""
    if result.screening:
        return result.screening.gate_passed
    return False
