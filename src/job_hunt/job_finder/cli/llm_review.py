"""CLI tool to review and update LLM match evaluations from a CSV, TSV, or ODF spreadsheet."""

import os
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

from job_hunt.job_finder.reviewer.match import get_job_matches
from job_hunt.job_finder.scraper.base import Job
from job_hunt.job_finder.utils.caching_utils import ENV_VAR_DISABLE_CACHED


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
        except Exception:
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
        except Exception:
            df.to_excel(path, index=False)
    else:
        df.to_csv(path, sep=file_type, index=False)


def main(path: str | Path, no_cache: bool = False, log_level: str = "INFO") -> None:
    """Execute the review CLI."""
    logger.remove()
    logger.add(sys.stderr, level=log_level)

    if no_cache:
        os.environ[ENV_VAR_DISABLE_CACHED] = "1"

    path_obj = Path(path)
    if not path_obj.exists():
        logger.error(f"File not found: {path_obj}")
        sys.exit(1)

    logger.info(f"Loading data from {path_obj}...")
    df, file_type = load_file(path_obj)

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

    logger.info(f"Saving updated data back to {path_obj}...")
    save_file(df, path_obj, file_type)
    logger.info("Done!")
