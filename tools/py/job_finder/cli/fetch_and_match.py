"""Main command-line interface for running the CV-job matching pipeline."""

import argparse
import sys
import tempfile
from dataclasses import asdict, is_dataclass
from pathlib import Path

import pandas as pd
import yaml
from loguru import logger
from job_finder.reviewer.match import JobMatch, get_job_matches
from job_finder.scraper.base import Job
from job_finder.scraper.fetch import get_jobs

_OUTPUT_PATH = Path(tempfile.gettempdir()) / "job_matches.csv"


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


def _main(urls: list[str], output: Path = _OUTPUT_PATH, *, use_cache: bool = True) -> None:
    """Execute the matching pipeline from a list of URLs to CSV output.

    Args:
        urls: List of job/search URLs.
        output: Path to save the CSV matches.
        use_cache: If True, use cached matches/jobs.

    """
    jobs_file = output.with_name("jobs.csv")

    if jobs_file.exists():
        logger.info(f"Loading jobs from {jobs_file}")
        df = pd.read_csv(jobs_file).fillna("")
        jobs = [Job(**row) for row in df.to_dict(orient="records")]
    else:
        logger.info("Fetching jobs...")
        jobs = get_jobs(*urls, use_cache=use_cache)
        create_save_df(jobs, sort_by="url", output=jobs_file, ascending=True)

    if output.exists():
        logger.info(f"Output file {output} already exists, skipping match analysis.")
    else:
        logger.info("Analyzing matches...")
        # filter failed ones and sort by url - to have proper hash
        jobs = sorted([j for j in jobs if j.description.strip()], key=lambda j: j.url)
        matches = get_job_matches(jobs)
        create_save_df(matches, sort_by="match_percentage", output=output, ascending=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some job URLs from a YAML file.")
    parser.add_argument("yaml_path", type=str, help="Path to the YAML file containing job URLs")
    parser.add_argument("--no-cache", action="store_true", help="Do not cache results")
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set log level"
    )

    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level=args.log_level)

    urls = yaml.safe_load(Path(args.yaml_path).read_text(encoding="utf-8"))

    _main(urls, use_cache=not args.no_cache)
