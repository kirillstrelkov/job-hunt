"""CLI tool to review and update LLM match evaluations from a CSV, TSV, or ODF spreadsheet."""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path so relative imports work when executed directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from loguru import logger
from reviewer.match import get_job_matches
from job_finder.scraper.base import Job
from job_finder.utils.caching_utils import ENV_VAR_DISABLE_CACHED


def load_file(path: Path) -> tuple[pd.DataFrame, str]:
    """Load a CSV, TSV, or ODF file into a pandas DataFrame and detect file type/delimiter.

    Args:
        path: Path to the file to load.

    Returns:
        A tuple of (DataFrame, format_specifier).

    """
    ext = path.suffix.lower()
    if ext in (".csv", ".tsv"):
        with path.open(encoding="utf-8") as f:
            first_line = f.readline()
        sep = "\t" if "\t" in first_line else ","
        df = pd.read_csv(path, sep=sep)
        return df, sep
    if ext in (".ods", ".xlsx", ".xls", ".odf"):
        try:
            df = pd.read_excel(path, engine="odf")
        except Exception:  # noqa: BLE001
            df = pd.read_excel(path)
        return df, "excel"
    # Fallback to standard CSV
    return pd.read_csv(path), ","


def save_file(df: pd.DataFrame, path: Path, file_type: str) -> None:
    """Save a pandas DataFrame back to disk using the original format.

    Args:
        df: The DataFrame to save.
        path: Path to the destination file.
        file_type: The format specifier returned by `load_file`.

    """
    if file_type == "excel":
        try:
            df.to_excel(path, index=False, engine="odf")
        except Exception:  # noqa: BLE001
            df.to_excel(path, index=False)
    else:
        df.to_csv(path, sep=file_type, index=False)


def main() -> None:
    """Execute the review CLI."""
    parser = argparse.ArgumentParser(description="Review and update CV matching results from a CSV, TSV, or ODF file.")
    parser.add_argument(
        "--path", type=str, required=True, help="Path to the CSV, TSV, or ODF file containing jobs to review"
    )
    parser.add_argument("--no-cache", action="store_true", help="Do not cache LLM results")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set log level",
    )

    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level=args.log_level)

    if args.no_cache:
        os.environ[ENV_VAR_DISABLE_CACHED] = "1"

    path = Path(args.path)
    if not path.exists():
        logger.error(f"File not found: {path}")
        sys.exit(1)

    logger.info(f"Loading data from {path}...")
    df, file_type = load_file(path)

    # Ensure required columns exist in the file
    required_cols = ["url", "title", "company", "description"]
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column '{col}' in input file.")
            sys.exit(1)

    jobs = []
    for _idx, row in df.iterrows():
        job = Job(
            title=str(row.get("title", "")),
            company=str(row.get("company", "")),
            url=str(row.get("url", "")),
            description=str(row.get("description", "")),
            error="",
        )
        jobs.append(job)

    logger.info(f"Running LLM analysis on {len(jobs)} job descriptions...")
    matches = get_job_matches(jobs)

    # Update columns
    for idx, match in enumerate(matches):
        df.loc[idx, "match_percentage"] = match.match_percentage
        df.loc[idx, "llm_text"] = match.llm_text
        df.loc[idx, "check_passed"] = match.check_passed

    logger.info(f"Saving updated data back to {path}...")
    save_file(df, path, file_type)
    logger.info("Done!")


if __name__ == "__main__":
    main()
