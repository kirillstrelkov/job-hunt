"""Prepare prompts for Resume tailoring using templates and job descriptions."""

import os
from pathlib import Path

from loguru import logger

_CUR_DIR = Path(__file__).parent
_MASTER_RESUME = Path(os.getenv("MASTERCV_PATH"))
_PROMPT_TITLE = _CUR_DIR / ".." / "prompts/tailor_for_title.md"
_PROMPT_DESC = _CUR_DIR / ".." / "prompts/tailor_for_description.md"


def _require(path: Path) -> Path:
    """Ensure that a required file exists and resolve its absolute path."""
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def tailor_for_title(output: str, job_title: str) -> None:
    """Generate a prompt tailored for a specific job title using the template."""
    master_resume = _require(_MASTER_RESUME)
    template = _require(_PROMPT_TITLE)

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)

    content = template.read_text().format(
        job_title=job_title,
        master_resume=master_resume.read_text(),
    )
    out.write_text(content)
    logger.info(f"Written: {out}")


def tailor_for_description(output: str, jd_path: str) -> None:
    """Generate a prompt tailored for a detailed job description file."""
    master_resume = _require(_MASTER_RESUME)
    template = _require(_PROMPT_DESC)
    jd = _require(Path(jd_path))

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)

    content = template.read_text().format(
        job_description=jd.read_text(),
        master_resume=master_resume.read_text(),
    )
    out.write_text(content)
    logger.info(f"Written: {out}")
