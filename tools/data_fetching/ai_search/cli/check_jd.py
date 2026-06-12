"""Command-line interface to analyze a single job description from standard input."""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path so relative imports work when executed directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger

from cli.fetch_and_match import _CV_TEXT
from llm import MODEL, analyze_cv, get_match_percentage

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a single job description from standard input.")
    parser.add_argument("--model", type=str, default=MODEL, help="Optional Ollama model override")
    args = parser.parse_args()

    logger.info("Enter Job Description:\n```")
    jd = sys.stdin.read()
    logger.info("```\nJob Description received ({} characters).", len(jd))

    data = analyze_cv(_CV_TEXT, jd, model=args.model)
    match = get_match_percentage(data)

    logger.info("Generated LLM Text:\n{}", json.dumps(data, indent=2, ensure_ascii=False))
    logger.info(f"Match Percentage: {match}%")
