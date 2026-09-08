"""Domain models for Job Description screening and Resume match analysis."""

from typing import Any

from pydantic import BaseModel, Field


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
    gate_passed: bool = Field(default=False, description="Set to true only if ALL flags are false.")
    gate_failed_reasons: list[str] = Field(
        default_factory=list, description="List of names of any flags that are true."
    )

    model_config = {
        "populate_by_name": True,
    }

    def model_post_init(self, context: Any) -> None:
        """Evaluate gate_passed status and synchronize failed flag reasons."""
        flags = {
            "is_contract": self.is_contract,
            "is_excluded_role": self.is_excluded_role,
            "is_german_required": self.is_german_required,
            "is_german_text": self.is_german_text,
            "is_manager": self.is_manager,
            "is_staff": self.is_staff,
        }
        self.gate_passed = not any(flags.values())
        failed = [name for name, val in flags.items() if val]
        if failed:
            for flag in failed:
                if flag not in self.gate_failed_reasons:
                    self.gate_failed_reasons.append(flag)
        else:
            self.gate_failed_reasons = []


class Analysis(BaseModel):
    """Pydantic model holding the Resume-to-JD fit analysis details."""

    match_percentage: int = Field(description="Candidate match percentage (0-100).")
    fit_label: str = Field(description="Excellent | Strong | Moderate | Weak | Poor.")
    summary: str = Field(description="2-3 sentence explanation of candidate fit.")
    matched_skills: list[str] = Field(description="Skills requested in JD that are matched in the Resume.")
    missing_skills: list[str] = Field(description="Skills requested in JD but missing in the Resume.")
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
