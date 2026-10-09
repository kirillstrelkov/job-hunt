"""OKF (Markdown + Frontmatter) reader and writer for Job models."""

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from job_hunt.job_finder.utils.models import BaseJob, Job, JobMatch

MODEL_MAP: dict[str, type[BaseJob]] = {
    "BaseJob": BaseJob,
    "Job": Job,
    "JobMatch": JobMatch,
}

MULTILINE_FIELD_TO_HEADING = {
    "description": "Description",
    "error": "Error",
    "llm_text": "LLM Text",
}

HEADING_TO_MULTILINE_FIELD = {
    "Description": "description",
    "Error": "error",
    "LLM Text": "llm_text",
    "Llm Text": "llm_text",
}


def _get_fence(text: str) -> str:
    """Return a backtick fence of at least 3 backticks longer than any consecutive backticks in text."""
    matches = re.findall(r"`+", text)
    max_backticks = max((len(m) for m in matches), default=0)
    return "`" * max(3, max_backticks + 1)


def write_job(job: BaseJob | Job | JobMatch, path: Path | str) -> None:
    """Serialize a BaseJob, Job, or JobMatch instance to an OKF markdown file.

    Frontmatter contains scalar metadata and model_type.
    Markdown body contains # <Title> followed by non-empty multiline fields under
    ## <Heading> wrapped in adaptive code fences.
    """
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    frontmatter_data: dict[str, Any] = {
        "model_type": job.__class__.__name__,
        "title": job.title,
        "company": job.company,
        "url": job.url,
    }

    if isinstance(job, Job):
        created_at = job.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        frontmatter_data["created_at"] = created_at.isoformat()

    if isinstance(job, JobMatch):
        frontmatter_data["match_percentage"] = job.match_percentage
        frontmatter_data["check_passed"] = job.check_passed
        processed_at = job.processed_at
        if processed_at.tzinfo is None:
            processed_at = processed_at.replace(tzinfo=UTC)
        frontmatter_data["processed_at"] = processed_at.isoformat()

    yaml_str = yaml.safe_dump(frontmatter_data, sort_keys=False, default_flow_style=False).strip()

    body_parts = [
        f"---\n{yaml_str}\n---",
        "",
        f"# {job.title}",
    ]

    for field_name, heading in MULTILINE_FIELD_TO_HEADING.items():
        if hasattr(job, field_name):
            val = getattr(job, field_name)
            if val:  # Omit empty multiline sections
                fence = _get_fence(str(val))
                body_parts.extend(
                    [
                        "",
                        f"## {heading}",
                        "",
                        f"{fence}text\n{val}\n{fence}",
                    ]
                )

    content = "\n".join(body_parts) + "\n"
    target_path.write_text(content, encoding="utf-8")


def read_job(path: Path | str) -> BaseJob | Job | JobMatch:
    """Read an OKF markdown file and parse it into a BaseJob, Job, or JobMatch instance.

    Determines class strictly based on frontmatter model_type and validates required title.
    """
    target_path = Path(path)
    content = target_path.read_text(encoding="utf-8")

    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", content, re.DOTALL)
    if not fm_match:
        raise ValueError(f"File {target_path} does not contain valid YAML frontmatter delimiters (---)")

    fm_raw, body_raw = fm_match.groups()
    frontmatter = yaml.safe_load(fm_raw)
    if not isinstance(frontmatter, dict):
        raise ValueError(f"Invalid frontmatter YAML in {target_path}: expected dictionary")

    model_type = frontmatter.get("model_type")
    if not model_type or model_type not in MODEL_MAP:
        raise ValueError(
            f"Missing or invalid 'model_type' in frontmatter of {target_path}. "
            f"Expected one of: {list(MODEL_MAP.keys())}, got: {model_type!r}"
        )

    if "title" not in frontmatter or not str(frontmatter["title"]).strip():
        raise ValueError(f"Missing required field 'title' in frontmatter of {target_path}")

    klass = MODEL_MAP[model_type]
    data: dict[str, Any] = dict(frontmatter)

    # Parse multiline sections from body
    pattern = re.compile(
        r"^##\s+([^\n]+)\s*\n+(?P<fence>`{3,}|~{3,})[^\n]*\n(?P<code>.*?)\n(?P=fence)",
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(body_raw):
        heading = match.group(1).strip()
        code_content = match.group("code")
        field_name = HEADING_TO_MULTILINE_FIELD.get(heading)
        if not field_name:
            norm = heading.lower().replace(" ", "_")
            if norm in MULTILINE_FIELD_TO_HEADING:
                field_name = norm
        if field_name:
            data[field_name] = code_content

    # Parse datetime fields
    for dt_field in ("created_at", "processed_at"):
        if dt_field in data and isinstance(data[dt_field], str):
            try:
                dt = datetime.fromisoformat(data[dt_field])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                data[dt_field] = dt
            except ValueError:
                pass
        elif dt_field in data and isinstance(data[dt_field], datetime) and data[dt_field].tzinfo is None:
            data[dt_field] = data[dt_field].replace(tzinfo=UTC)

    data.pop("model_type", None)

    return klass(**data)


__all__ = [
    "HEADING_TO_MULTILINE_FIELD",
    "MODEL_MAP",
    "MULTILINE_FIELD_TO_HEADING",
    "read_job",
    "write_job",
]
