"""Main command-line interface for running the CV-job matching pipeline."""

import argparse
import sys
import tempfile
from dataclasses import asdict, is_dataclass
from pathlib import Path

import pandas as pd
import yaml
from loguru import logger

from helpers.tmp_helper import get_tmp_folder
from job_finder.reviewer.match import JobMatch, get_job_matches
from job_finder.scraper.base import Job
from job_finder.scraper.fetch import get_jobs


def create_save_df(objects: list[Job | JobMatch], sort_by: str, output: Path, *, ascending: bool = True) -> None:
    """Create a DataFrame from a list of objects, sort, and save it to a CSV file.

    Args:
        objects: List of objects (Job or JobMatch).
        sort_by: Column name to sort the DataFrame by.
        output: CSV destination file path.
        ascending: True to sort ascending, False for descending.

    """
    if not objects:
        msg = "No matches found"
        raise ValueError(msg)

    data = [asdict(item) if is_dataclass(item) else item for item in objects]
    df = pd.DataFrame(data).sort_values(by=sort_by, ascending=ascending)
    df.to_csv(output, index=False)
    logger.info(f"Saved to {output}")


def create_jobs_csv(urls: list[str], jobs_file: Path, *, use_cache: bool = True) -> list[Job]:
    """Fetch jobs from URLs, save them to a CSV file, and return the list of Jobs."""
    if jobs_file.exists():
        logger.info(f"Loading jobs from {jobs_file}")
        df = pd.read_csv(jobs_file).fillna("")
        return [Job(**row) for row in df.to_dict(orient="records")]

    logger.info("Fetching jobs...")
    jobs = get_jobs(*urls, use_cache=use_cache)
    create_save_df(jobs, sort_by="url", output=jobs_file, ascending=True)
    return jobs


def create_job_matches_csv(jobs: list[Job], matches_file: Path) -> list[JobMatch]:
    """Evaluate jobs against the CV, save matches to a CSV file, and return the list of JobMatches."""
    if matches_file.exists():
        logger.info(f"Output file {matches_file} already exists, skipping match analysis.")
        df = pd.read_csv(matches_file).fillna("")
        return [JobMatch(**row) for row in df.to_dict(orient="records")]

    logger.info("Analyzing matches...")
    # filter failed ones and sort by url - to have proper hash
    filtered_jobs = sorted([j for j in jobs if j.description.strip()], key=lambda j: j.url)
    matches = get_job_matches(filtered_jobs)
    create_save_df(matches, sort_by="match_percentage", output=matches_file, ascending=False)
    return matches


def _main(urls: list[str], output_dir: Path, *, use_cache: bool = True) -> None:
    """Execute the matching pipeline from a list of URLs to CSV output.

    Args:
        urls: List of job/search URLs.
        output_dir: Path to the directory where CSV files will be saved.
        use_cache: If True, use cached matches/jobs.

    """
    jobs_file = output_dir / "jobs.csv"
    matches_file = output_dir / "job_matches.csv"

    jobs = create_jobs_csv(urls, jobs_file, use_cache=use_cache)
    create_job_matches_csv(jobs, matches_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some job URLs from a YAML file.")
    parser.add_argument("yaml_path", type=str, help="Path to the YAML file containing job URLs")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output directory path for CSV files")
    parser.add_argument("--no-cache", action="store_true", help="Do not cache results")
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set log level"
    )

    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level=args.log_level)

    urls = yaml.safe_load(Path(args.yaml_path).read_text(encoding="utf-8"))

    # Resolve output directory: command-line argument or get_tmp_folder fallback
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = get_tmp_folder(__file__)

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using output directory: {output_dir}")

    _main(urls, output_dir, use_cache=not args.no_cache)

