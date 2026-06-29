"""LLM integration for CV and job description screening and analysis."""

from pydantic import BaseModel, Field
from helpers.llm.ollama import get_agent as get_ollama_agent
from helpers.llm.gemini import get_agent as get_gemini_agent
from helpers.llm_helper import get_eval_model, get_model_names as get_gemini_model_names

MODEL = get_eval_model()


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

"""
SYSTEM_PROMPT_CANDIDATE = f"""
{HEADER_PROMPT}

Analyze the CV against the job description.

All percentages are integers 0-100. Every field must be populated — use null only if the
information is genuinely absent. Base every judgment strictly on the provided documents.
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


class Screening(BaseModel):
    """Pydantic model holding screening results for a job description."""

    reasoning: str = Field(description="Briefly state your findings for the 6 rules above.")
    is_german_text: bool = Field(
        description="Is more than 80% of the text written in requirements/responsibilities in German?"
    )
    is_german_required: bool = Field(
        description="Is German language listed as a must-have, required, or essential skill?"
    )
    is_manager: bool = Field(description="Is the position for a manager role?")
    is_staff: bool = Field(description="Is 'staff engineer' or 'lead engineer' mentioned explicitly?")
    is_contract: bool = Field(description="Is the position temporary, contract-based, or for freelancers?")
    is_excluded_role: bool = Field(
        description="Is the role a Data Scientist, intern, Werkstudent, or trainee position?"
    )
    gate_passed: bool = Field(description="Set to true only if ALL flags are false.")
    gate_failed_reasons: list[str] = Field(description="List of names of any flags that are true.")

    model_config = {
        "populate_by_name": True,
    }


class Analysis(BaseModel):
    """Pydantic model holding the CV-to-JD fit analysis details."""

    match_percentage: int = Field(description="Candidate match percentage (0-100).")
    fit_label: str = Field(description="Excellent | Strong | Moderate | Weak | Poor.")
    summary: str = Field(description="2-3 sentence explanation of candidate fit.")
    matched_skills: list[str] = Field(description="Skills requested in JD that are matched in the CV.")
    missing_skills: list[str] = Field(description="Skills requested in JD but missing in the CV.")
    strengths: list[str] = Field(description="Candidate's strengths for the role.")
    gaps: list[str] = Field(description="Candidate's gaps for the role.")

    model_config = {
        "populate_by_name": True,
    }


class JobMatchResult(BaseModel):
    """Result object combining screening and match analysis."""

    screening: Screening | None = None
    analysis: Analysis | None = None
    error: str | None = None

    model_config = {
        "populate_by_name": True,
    }


def get_agent(model_name: str, output_type: type[BaseModel], instructions: str):
    if model_name in get_gemini_model_names():
        return get_gemini_agent(model_name, output_type, instructions)
    return get_ollama_agent(model_name, output_type, instructions)


def _get_screening(job_description: str, model: str = MODEL) -> Screening:
    agent = get_agent(
        model_name=model,
        output_type=Screening,
        instructions=SYSTEM_PROMPT_SCREENING,
    )
    result = agent.run_sync(JD_PROMPT.format(job_description=job_description.strip()))
    return result.output


def _get_analysis(cv: str, job_description: str, model: str = MODEL) -> Analysis:
    agent = get_agent(
        model_name=model,
        output_type=Analysis,
        instructions=SYSTEM_PROMPT_CANDIDATE,
    )
    user_prompt = f"{CV_PROMPT.format(cv=cv.strip())}\n{JD_PROMPT.format(job_description=job_description.strip())}"
    result = agent.run_sync(user_prompt)
    return result.output


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
    return -1


def get_checked_passed(result: JobMatchResult) -> bool:
    """Return whether the screening gate passed."""
    if result.screening:
        return result.screening.gate_passed
    return False
