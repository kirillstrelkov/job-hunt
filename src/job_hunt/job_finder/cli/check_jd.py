"""Command-line interface to analyze a single job description from standard input."""

import sys
from pathlib import Path
from pprint import pformat

from loguru import logger

from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.job_finder.reviewer.llm import MODEL, analyze_resume, get_match_percentage

_RESUME_TEXT = DEFAULT_CONFIG.composer.body.read_text()


def main(jd_path: Path | str, model: str = MODEL) -> None:
    """Analyze a single job description from a file or standard input."""
    if str(jd_path) == "-":
        logger.info("Enter Job Description (Ctrl-D to end):\n```")
        jd = sys.stdin.read()
    else:
        path = Path(jd_path)
        if not path.exists():
            logger.error(f"File not found: {path}")
            sys.exit(1)
        jd = path.read_text(encoding="utf-8")

    logger.info("```\nJob Description received ({} characters).", len(jd))
    data = analyze_resume(_RESUME_TEXT, jd, model=model)
    match = get_match_percentage(data)

    logger.info("Generated LLM Text:\n{}", pformat(data))
    logger.info(f"Match Percentage: {match}%")
