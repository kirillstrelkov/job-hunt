"""Command-line interface to analyze a single job description from standard input."""

import argparse
import sys
from pathlib import Path
from pprint import pformat

# Add parent directory to path so relative imports work when executed directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger

from reviewer.llm import MODEL, analyze_cv, get_match_percentage

_CV_TEXT = (Path(__file__).resolve().parent.parent / "data/private/cv.txt").read_text(encoding="utf-8")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a single job description from standard input.")
    parser.add_argument("--model", type=str, default=MODEL, help="Optional Ollama model override")
    args = parser.parse_args()

    logger.info("Enter Job Description:\n```")
    jd = sys.stdin.read()
    logger.info("```\nJob Description received ({} characters).", len(jd))

    data = analyze_cv(_CV_TEXT, jd, model=args.model)
    match = get_match_percentage(data)

    logger.info("Generated LLM Text:\n{}", pformat(data))
    logger.info(f"Match Percentage: {match}%")
