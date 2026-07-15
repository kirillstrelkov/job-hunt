"""Main command-line interface for running the CV-job matching pipeline."""

import argparse
import sys
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


def _get_from_csv(path: Path, klass: type[Job] | type[JobMatch]) -> list[Job]:
    """Load jobs from a CSV file."""
    if not path.exists():
        return []
    logger.info(f"Loading {klass}s from {path}")
    df = pd.read_csv(path).fillna("")
    return [klass(**row) for row in df.to_dict(orient="records")]


def create_jobs_csv(urls: list[str], jobs_file: Path, *, use_cache: bool = True) -> list[Job]:
    """Fetch jobs from URLs, save them to a CSV file, and return the list of Jobs."""
    existing_jobs = _get_from_csv(jobs_file, Job)

    logger.info("Fetching jobs...")
    new_jobs = get_jobs(*urls, use_cache=use_cache)

    all_jobs = existing_jobs + new_jobs
    jobs_no_dup = list(set(all_jobs))
    diff = len(all_jobs) - len(jobs_no_dup)

    if diff > 0:
        logger.warning(f"Found {diff} duplicate job urls")

    create_save_df(jobs_no_dup, sort_by="created_at", output=jobs_file)
    return jobs_no_dup


def create_job_matches_csv(jobs: list[Job], matches_file: Path) -> list[JobMatch]:
    """Evaluate jobs against the CV, save matches to a CSV file, and return the list of JobMatches."""
    existing_matches = _get_from_csv(matches_file, JobMatch)

    logger.info("Analyzing matches...")
    # filter failed ones and sort by url - to have proper hash
    filtered_jobs = sorted([j for j in jobs if j.description.strip()], key=lambda j: j.url)

    existing_jobs = [
        Job(
            title=m.title,
            company=m.company,
            url=m.url,
            description=m.description,
            error=m.error,
            created_at=m.created_at,
        )
        for m in existing_matches
    ]
    existing_jobs_set = set(existing_jobs)
    already_processed = [j for j in filtered_jobs if j in existing_jobs_set]
    new_jobs = [j for j in filtered_jobs if j not in existing_jobs_set]

    logger.info(f"Already processed matches: {len(already_processed)}, new matches to process: {len(new_jobs)}")

    new_matches = get_job_matches(new_jobs)

    all_matches = existing_matches + new_matches

    create_save_df(all_matches, sort_by="match_percentage", output=matches_file, ascending=False)
    return all_matches


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
    parser.add_argument(
        "yaml_path",
        type=str,
        nargs="?",
        default=None,
        help="Path to the YAML file containing job URLs. If not provided, configuration is loaded from config.yaml",
    )
    parser.add_argument("--output", "-o", type=str, default=None, help="Output directory path for CSV files")
    parser.add_argument("--no-cache", action="store_true", help="Do not cache results")
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set log level"
    )

    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level=args.log_level)

    if args.yaml_path:
        data = yaml.safe_load(Path(args.yaml_path).read_text(encoding="utf-8"))
        if isinstance(data, list):
            urls = data
        elif isinstance(data, dict):
            if "scraper" in data and isinstance(data["scraper"], dict) and "urls" in data["scraper"]:
                urls = data["scraper"]["urls"]
            elif "urls" in data:
                urls = data["urls"]
            else:
                raise ValueError("Could not find list of URLs in the provided YAML file.")
        else:
            raise ValueError("YAML file must contain a list of URLs or a config dictionary.")
    else:
        from config.config import DEFAULT_CONFIG

        urls = DEFAULT_CONFIG.scraper.urls

    if not urls:
        logger.error("No URLs found to process. Please specify them in config.yaml or provide a YAML file.")
        sys.exit(1)

    # Resolve output directory: command-line argument or get_tmp_folder fallback
    output_dir = Path(args.output) if args.output else get_tmp_folder(__file__)

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using output directory: {output_dir}")

    _main(urls, output_dir, use_cache=not args.no_cache)
