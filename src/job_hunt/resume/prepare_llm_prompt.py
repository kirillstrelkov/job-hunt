"""Prepare prompts for Resume tailoring using templates and job descriptions."""

from pathlib import Path

from loguru import logger

from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.resume.prepare_resume import generate_llm_prompt

_CUR_DIR = Path(__file__).parent.resolve()
_PROMPT_TITLE = _CUR_DIR / "prompts/tailor_for_title.md"
_PROMPT_DESC = _CUR_DIR / "prompts/tailor_for_description.md"


def get_master_resume_body_path(custom_path: Path | str | None = None) -> Path:
    """Resolve master resume body path from parameter or config.yaml."""
    if custom_path:
        return Path(custom_path)
    return DEFAULT_CONFIG.composer.body


def _require(path: Path) -> Path:
    """Ensure that a required file exists and resolve its absolute path."""
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def tailor_for_title(
    output: str | Path,
    job_title: str,
    *,
    resume_body: Path | str | None = None,
    template_path: Path | str | None = None,
) -> None:
    """Generate a prompt tailored for a specific job title using the template."""
    master_resume_body = _require(get_master_resume_body_path(resume_body))
    template = _require(Path(template_path) if template_path else _PROMPT_TITLE)

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)

    content = generate_llm_prompt(
        template=template,
        resume_body=master_resume_body,
        job_title=job_title,
    )
    out.write_text(content, encoding="utf-8")
    logger.info(f"Written: {out}")


def tailor_for_description(
    output: str | Path,
    jd_path: str | Path,
    *,
    resume_body: Path | str | None = None,
    template_path: Path | str | None = None,
) -> None:
    """Generate a prompt tailored for a detailed job description file."""
    master_resume_body = _require(get_master_resume_body_path(resume_body))
    template = _require(Path(template_path) if template_path else _PROMPT_DESC)
    jd = _require(Path(jd_path))

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)

    content = generate_llm_prompt(
        template=template,
        resume_body=master_resume_body,
        job_description=jd,
    )
    out.write_text(content, encoding="utf-8")
    logger.info(f"Written: {out}")
