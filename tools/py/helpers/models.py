"""Pydantic models representing tailored CV structure for LLM requests."""

from pydantic import BaseModel, Field


class Skills(BaseModel):
    """List of skills grouped by categories."""

    languages: list[str] = Field(
        ...,
        description="Programming languages candidate is proficient in.",
    )
    databases_and_brokers: list[str] = Field(
        ...,
        description="Databases, message brokers, and queues.",
    )
    infrastructure_and_cloud: list[str] = Field(
        ...,
        description="Infrastructure, containerization, cloud, orchestration, and GitOps tools.",
    )
    ci_cd_and_testing: list[str] = Field(
        ...,
        description="CI/CD, build tools, and testing frameworks.",
    )
    observability_and_apis: list[str] = Field(
        ...,
        description="Observability, monitoring, and API protocols/standards.",
    )

    model_config = {
        "populate_by_name": True,
    }


class WorkExperience(BaseModel):
    """A role in the candidate's work history."""

    title: str = Field(..., description="Job title of the role.")
    company: str = Field(..., description="Company name.")
    location: str = Field(..., description="Job location (city, country).")
    dates: str = Field(..., description="Date range of the role (e.g. Oct 2023 - Aug 2025).")
    bullet_points: list[str] = Field(
        ...,
        description="List of accomplishments and duties in this role tailored to the JD.",
    )

    model_config = {
        "populate_by_name": True,
    }


class Project(BaseModel):
    """A project the candidate built or contributed to."""

    name: str = Field(..., description="Project name/title.")
    url: str | None = Field(None, description="GitHub or website URL of the project.")
    year: str = Field(..., description="Year or date of the project (e.g. 2026).")
    bullet_points: list[str] = Field(
        ...,
        description="List of details and accomplishments for this project.",
    )
    skills: list[str] = Field(
        ...,
        description="Specific skills or tech stack utilized in the project.",
    )

    model_config = {
        "populate_by_name": True,
    }


class CourseCertificate(BaseModel):
    """A completed course or certificate."""

    name: str = Field(..., description="Name of the course or certification.")
    provider: str = Field(..., description="Issuing organization or platform.")
    date: str = Field(..., description="Completion date or range.")

    model_config = {
        "populate_by_name": True,
    }


class JustificationReport(BaseModel):
    """Report detailing the choices made during tailoring."""

    reductions_and_omissions: list[str] = Field(
        ...,
        description="List of roles removed, condensed, or bullet points reduced.",
    )
    selections: list[str] = Field(
        ...,
        description="List of selected projects, certificates, and skills featured to match the JD.",
    )

    model_config = {
        "populate_by_name": True,
    }


class WorkExperienceOverflow(BaseModel):
    """An overflow bullet point for a specific role."""

    role_identifier: str = Field(
        ...,
        description="Identifier of the role (e.g., 'Software Engineer | CARIAD SE').",
    )
    bullet_point: str = Field(..., description="Additional tailored accomplishment.")

    model_config = {
        "populate_by_name": True,
    }


class CourseCertificateOverflow(BaseModel):
    """An overflow course or certificate with a potential relevance description."""

    name: str = Field(..., description="Name of the course or certification.")
    provider: str = Field(..., description="Issuing organization or platform.")
    date: str = Field(..., description="Completion date.")
    description: str | None = Field(
        None,
        description="Optional relevance description or notes.",
    )

    model_config = {
        "populate_by_name": True,
    }


class AdditionalOptions(BaseModel):
    """Additional tailored choices not fitting into the main CV layout."""

    work_experience_overflow: list[WorkExperienceOverflow] = Field(
        default_factory=list,
        description="List of overflow work experience bullet points.",
    )
    courses_and_certificates_overflow: list[CourseCertificateOverflow] = Field(
        default_factory=list,
        description="List of overflow courses & certificates.",
    )
    projects_overflow: list[Project] = Field(
        default_factory=list,
        description="List of overflow projects.",
    )

    model_config = {
        "populate_by_name": True,
    }


class TailoredCVBody(BaseModel):
    """The root model representing the complete tailored CV output of LLM request."""

    summary: str = Field(
        ...,
        description="Tailored summary/pitch paragraph highlighting matching qualifications.",
    )
    skills: Skills = Field(..., description="Grouped skills section.")
    work_experience: list[WorkExperience] = Field(
        ...,
        description="Tailored professional work experience list.",
    )
    projects: list[Project] = Field(
        ...,
        description="Selected and tailored project achievements.",
    )
    courses_and_certificates: list[CourseCertificate] = Field(
        ...,
        description="Relevant courses and certifications.",
    )
    justification_report: JustificationReport = Field(
        ...,
        description="Report explaining the tailored choices.",
    )
    additional_options: AdditionalOptions = Field(
        ...,
        description="Overflow choices and options for further tailoring.",
    )

    model_config = {
        "populate_by_name": True,
    }
