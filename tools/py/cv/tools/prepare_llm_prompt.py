"""Prepare prompts for CV tailoring using templates and job descriptions."""

import argparse
import os
from pathlib import Path

from loguru import logger

_CUR_DIR = Path(__file__).parent
_MASTERCV = Path(os.getenv("MASTERCV_PATH"))
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
    mastercv = _require(_MASTERCV)
    template = _require(_PROMPT_TITLE)

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)

    content = template.read_text().format(
        job_title=job_title,
        master_cv=mastercv.read_text(),
    )
    out.write_text(content)
    logger.info(f"Written: {out}")


def tailor_for_description(output: str, jd_path: str) -> None:
    """Generate a prompt tailored for a detailed job description file."""
    mastercv = _require(_MASTERCV)
    template = _require(_PROMPT_DESC)
    jd = _require(Path(jd_path))

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)

    content = template.read_text().format(
        job_description=jd.read_text(),
        master_cv=mastercv.read_text(),
    )
    out.write_text(content)
    logger.info(f"Written: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate LLM prompt for CV tailoring.")
    parser.add_argument("--output", required=True, help="Output path for the generated .md file")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--tailor-for-title", metavar="JOB_TITLE", help="Job title text")
    mode.add_argument(
        "--tailor-for-description",
        action="store_true",
        help="Tailor for a job description file",
    )

    parser.add_argument(
        "--job-description",
        metavar="PATH",
        help="Path to job description file (use with --tailor-for-description)",
    )

    args = parser.parse_args()

    if args.tailor_for_description:
        if not args.job_description:
            parser.error("--job-description is required with --tailor-for-description")
        tailor_for_description(args.output, args.job_description)
    else:
        tailor_for_title(args.output, args.tailor_for_title)
