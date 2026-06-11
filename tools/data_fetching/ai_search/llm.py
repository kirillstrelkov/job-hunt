from pathlib import Path
from loguru import logger
import ollama
import json
import sys
from typing import Any

# _MODEL = "llama3.1:8b"
_MODEL = "gemma4:e2b"
_MODEL = "gemma4:e2b-it-qat"
# _MODEL = "deepseek-r1:8b" # Also works well

EXCLUDED_COMPANIES = [
    "Mindrift",
    "Turing",
]
SYSTEM_PROMPT = """
You are a tech reverse recruiter. Follow the two stages below in order. Return ONLY valid JSON — no markdown fences, no commentary outside the JSON.

════════════════════════════════════════
STAGE 1 — JOB DESCRIPTION PRE-SCREENING
════════════════════════════════════════

Analyze the job description.

Evaluate the following. For rule 6, if the word appears at all, treat it as 100%% confidence:
1. is_german_text        — Is more than 80%% of the text written in Requirements and Responsibilities sections, in German?
2. is_german_required    — Is German language listed as a must-have, required, or essential skill? (Ignore if listed as a plus or advantage.)
3. is_manager            — Does the experience demonstrate ownership over a feature or product lifecycle rather than just executing assigned tasks?
4. is_staff              — Is "staff engineer" or "lead engineer" mentioned explicitly? Do NOT imply or infer — only mark true if stated verbatim.
5. is_contract           — Is the position temporary, contract-based, or for freelancers?
6. is_excluded_company   — Does the job description mention any company from this list: {excluded_companies}? Match case-insensitively if the name appears ANYWHERE in the text.
7. is_excluded_role      — Is the role a Data Scientist, intern, internship, Werkstudent, or trainee position? Match case-insensitively.

After evaluating, produce this object. Use the "reasoning" field to briefly explain your findings before outputting the boolean flags:

{{
  "screening": {{
    "reasoning": "Briefly state your findings for the 7 rules above.",
    "is_german_text": boolean,
    "is_german_required": boolean,
    "is_manager": boolean,
    "is_staff": boolean,
    "is_contract": boolean,
    "is_excluded_company": boolean,
    "is_excluded_role": boolean,
    "gate_passed": boolean,
    "gate_failed_reasons":[]
  }}
}}

Set "gate_passed" to true only if ALL flags are false.
Populate "gate_failed_reasons" with the names of any flags that are true (e.g. ["is_german_required", "is_excluded_company"]).

════════════════════════════════════════
STAGE 2 — CANDIDATE FIT ANALYSIS
════════════════════════════════════════

IMPORTANT: If gate_passed is false, stop here. Return ONLY the "screening" object above — do not analyze the CV.

If gate_passed is true, analyze the CV against the job description and append an "analysis" key to the same JSON object.

The final JSON structure must be:

{{
  "screening": {{ ... }},
  "analysis": {{
    "candidate_name": "string | null",
    "job_title": "string",
    "overall_fit": {{
      "percentage": 0,
      "label": "Excellent | Strong | Moderate | Weak | Poor",
      "summary": "2–3 sentence explanation"
    }},
    "score_breakdown": {{
      "skills_match": {{
        "percentage": 0,
        "matched_skills": [""],
        "missing_skills": [""],
        "notes": ""
      }},
      "experience_relevance": {{
        "percentage": 0,
        "years_required": 0,
        "years_candidate_has": 0,
        "notes": ""
      }},
      "education_and_certifications": {{
        "percentage": 0,
        "required": "",
        "candidate_has": "",
        "notes": ""
      }},
      "soft_skills_and_culture": {{
        "percentage": 0,
        "notes": ""
      }},
      "seniority_alignment": {{
        "percentage": 0,
        "required_level": "",
        "candidate_level": "",
        "notes": ""
      }}
    }},
    "strengths": [
      {{ "point": "", "evidence": "" }}
    ],
    "gaps": [
      {{ "point": "", "severity": "critical | moderate | minor" }}
    ],
    "recommendation": {{
      "verdict": "Strong Yes | Yes | Maybe | No",
      "justification": ""
    }},
    "interview_questions":[
      {{ "question": "", "targets": "" }}
    ],
    "red_flags":[]
  }}
}}

All percentages are integers 0–100. Every field must be populated — use null only if the information is genuinely absent. Base every judgment strictly on the provided documents.

"""

USER_PROMPT = """
<job_description>
{job_description}
</job_description>

<cv>
{cv}
</cv>
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

PROMPT_TEMPLATE = """You are a recruitment pipeline assistant. Follow the two stages below in order. Return ONLY valid JSON — no markdown fences, no commentary outside the JSON.

════════════════════════════════════════
STAGE 1 — JOB DESCRIPTION PRE-SCREENING
════════════════════════════════════════

Analyze the job description strictly. 

<job_description>
{job_description}
</job_description>

Evaluate the following. For rule 6, if the word appears at all, treat it as 100% confidence:
1. is_german_text        — Is more than 80% of the text written in German?
2. is_german_required    — Is German language listed as a must-have, required, or essential skill? (Ignore if listed as a plus or advantage.)
3. is_manager            — Is the position for a manager role?
4. is_staff              — Is "staff engineer" or "lead engineer" mentioned explicitly? Do NOT imply or infer — only mark true if stated verbatim.
5. is_contract           — Is the position temporary, contract-based, or for freelancers?
6. is_excluded_company   — Does the job description mention any company from this list: {excluded_companies}? Match case-insensitively if the name appears ANYWHERE in the text.
7. is_excluded_role      — Is the role a Data Scientist, intern, internship, Werkstudent, or trainee position? Match case-insensitively.

After evaluating, produce this object. Use the "reasoning" field to briefly explain your findings before outputting the boolean flags:

{{
  "screening": {{
    "reasoning": "Briefly state your findings for the 7 rules above.",
    "is_german_text": boolean,
    "is_german_required": boolean,
    "is_manager": boolean,
    "is_staff": boolean,
    "is_contract": boolean,
    "is_excluded_company": boolean,
    "is_excluded_role": boolean,
    "gate_passed": boolean,
    "gate_failed_reasons":[]
  }}
}}

Set "gate_passed" to true only if ALL flags are false.
Populate "gate_failed_reasons" with the names of any flags that are true (e.g. ["is_german_required", "is_excluded_company"]).

════════════════════════════════════════
STAGE 2 — CANDIDATE FIT ANALYSIS
════════════════════════════════════════

IMPORTANT: If gate_passed is false, stop here. Return ONLY the "screening" object above — do not analyze the CV.

If gate_passed is true, analyze the CV against the job description and append an "analysis" key to the same JSON object.

<cv>
{cv}
</cv>

The final JSON structure must be:

{{
  "screening": {{ ... }},
  "analysis": {{
    "candidate_name": "string | null",
    "job_title": "string",
    "overall_fit": {{
      "percentage": 0,
      "label": "Excellent | Strong | Moderate | Weak | Poor",
      "summary": "2–3 sentence explanation"
    }},
    "score_breakdown": {{
      "skills_match": {{
        "percentage": 0,
        "matched_skills": [""],
        "missing_skills": [""],
        "notes": ""
      }},
      "experience_relevance": {{
        "percentage": 0,
        "years_required": 0,
        "years_candidate_has": 0,
        "notes": ""
      }},
      "education_and_certifications": {{
        "percentage": 0,
        "required": "",
        "candidate_has": "",
        "notes": ""
      }},
      "soft_skills_and_culture": {{
        "percentage": 0,
        "notes": ""
      }},
      "seniority_alignment": {{
        "percentage": 0,
        "required_level": "",
        "candidate_level": "",
        "notes": ""
      }}
    }},
    "strengths": [
      {{ "point": "", "evidence": "" }}
    ],
    "gaps": [
      {{ "point": "", "severity": "critical | moderate | minor" }}
    ],
    "recommendation": {{
      "verdict": "Strong Yes | Yes | Maybe | No",
      "justification": ""
    }},
    "interview_questions":[
      {{ "question": "", "targets": "" }}
    ],
    "red_flags":[]
  }}
}}

All percentages are integers 0–100. Every field must be populated — use null only if the information is genuinely absent. Base every judgment strictly on the provided documents.
"""


def _create_prompt(system: None | str = None, user: str | None = None) -> dict:
    if system:
        return {"role": "system", "content": system}

    if user:
        return {"role": "user", "content": user}

    raise ValueError("system or user should be used")


def llm_send(*prompts: dict, debug_prompts: bool = False) -> str:
    """Send a prompt + content to Ollama."""
    if debug_prompts:
        content = "-----\n".join([p["content"] for p in prompts])
        Path("/tmp/llm_prompt_debug.txt").write_text(content)

    try:
        response = ollama.chat(
            model=_MODEL,
            messages=prompts,
            options={
                "temperature": 0,
                "num_ctx": 16384,
                "num_predict": 3072,
                "seed": 42,
            },
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return ""


def analyze_cv(cv: str, job_description: str) -> dict[str, Any]:
    """Analyze a CV against a job description using LLM.

    Args:
        cv: Full CV text
        job_description: Full job description text

    Returns:
        Parsed JSON result with screening and (if gate passed) analysis sections

    """
    # prompt = PROMPT_TEMPLATE.format(
    #     cv=cv.strip(),
    #     excluded_companies=", ".join(EXCLUDED_COMPANIES),
    #     job_description=job_description.strip(),
    # )

    # raw = llm_send(_create_prompt(user=prompt))

    system_prompt = SYSTEM_PROMPT.format(
        excluded_companies=", ".join(EXCLUDED_COMPANIES),
    )
    cv_prompt = CV_PROMPT.format(
        cv=cv.strip(),
    )
    jd_prompt = JD_PROMPT.format(
        job_description=job_description.strip(),
    )
    raw = llm_send(
        _create_prompt(system=system_prompt),
        _create_prompt(user=cv_prompt),
        _create_prompt(user=jd_prompt),
        debug_prompts=True,
    )

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    resp = json.loads(raw)

    # recheck
    fail_reasons = [k for k, v in resp["screening"].items() if k.startswith("is_") and v]
    resp["screening"]["gate_failed_reasons"] = fail_reasons
    resp["screening"]["gate_passed"] = len(fail_reasons) == 0

    return resp


def get_match_percentage(analysis_data: dict) -> int:
    """Return percentage from analyzed data."""
    return analysis_data.get("analysis", {}).get("overall_fit", {}).get("percentage", 0)


def get_checked_passed(analysis_data: dict) -> bool:
    """Return percentage from analyzed data."""
    return analysis_data.get("screening", {}).get("gate_passed", False)
