"""Command-line interface to analyze a single job description from standard input."""

import sys

from loguru import logger

from cli import _CV_TEXT
from llm import analyze_cv, get_match_percentage

if __name__ == "__main__":
    logger.info("Enter Job Description:\n```")
    jd = sys.stdin.read()
    logger.info("```\nJob Description received ({} characters).", len(jd))

    data = analyze_cv(_CV_TEXT, jd)
    match = get_match_percentage(data)

    logger.info("Generated LLM Text:\n{}", data)
    logger.info(f"Match Percentage: {match}%")
