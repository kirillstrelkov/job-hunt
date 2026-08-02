from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BaseJob(BaseModel):
    """Represents a base job description model with only basic info."""

    model_config = ConfigDict(frozen=True)

    title: str
    company: str
    url: str
    error: str = ""

    @model_validator(mode="before")
    @classmethod
    def clean_empty_strings(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        for key, value in list(cleaned.items()):
            if value == "":
                field_info = cls.model_fields.get(key)
                if field_info and field_info.annotation is not str:
                    cleaned.pop(key)
        return cleaned

    def __eq__(self, other: object) -> bool:
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.title == other.title and self.company == other.company

    def __hash__(self) -> int:
        return hash((self.title, self.company))


class Job(BaseJob):
    """Represents a complete job description model."""

    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def __eq__(self, other: object) -> bool:
        if self.__class__ is not other.__class__:
            return NotImplemented
        return super().__eq__(other) and self.description == other.description

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.description))


def make_job(
    *,
    base_job: BaseJob | None = None,
    title: str | None = None,
    company: str | None = None,
    url: str | None = None,
    description: str = "",
    error: str | None = None,
    created_at: datetime | None = None,
) -> Job:
    """Create a Job instance."""
    base_job = base_job or BaseJob(title="", company="", url="")
    kwargs = {
        "title": title or base_job.title,
        "company": company or base_job.company,
        "url": url or base_job.url,
        "description": description,
        "error": error or base_job.error,
    }
    if created_at is not None:
        kwargs["created_at"] = created_at
    return Job(**kwargs)


class JobMatch(Job):
    """Pydantic model holding the results of a Resume-to-job match assessment."""

    match_percentage: int = -1
    llm_text: str = ""
    check_passed: bool = False
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def __eq__(self, other: object) -> bool:
        if self.__class__ is not other.__class__:
            return NotImplemented
        return (
            super().__eq__(other)
            and self.match_percentage == other.match_percentage
            and self.llm_text == other.llm_text
            and self.check_passed == other.check_passed
        )

    def __hash__(self) -> int:
        return hash(
            (
                super().__hash__(),
                self.match_percentage,
                self.llm_text,
                self.check_passed,
            )
        )
