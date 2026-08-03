"""Read job postings from a CSV and compose Resumes locally for each posting."""

import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger
from tqdm import tqdm

from job_hunt.config import config as cfg
from job_hunt.resume import prepare_resume
from job_hunt.resume.compose_resume import compose_resume

WORD_PATTERN = re.compile(r"\w{2,}")


def generate_id(title: str, company: str) -> str:
    """Generate a clean slug/id based on the first 4 words of 2 or more characters in title and first 2 in company."""
    title_words = WORD_PATTERN.findall(title.lower())[:5]
    company_words = WORD_PATTERN.findall(company.lower())[:2]
    return "_".join(company_words + title_words)


def main(
    path: str | Path,
    folder: str | Path,
    model: str | None = None,
    force: bool = False,
    feedback: bool = False,
    config: str | Path | None = None,
) -> None:  # noqa: PLR0915
    """Read CSV, extract job postings, and run compose pipeline for each job."""
    # Load custom config if specified
    if config:
        config_path = Path(config).resolve()
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        custom_cfg = cfg.ConfigManager(config_path)
        cfg.DEFAULT_CONFIG = custom_cfg
        prepare_resume.DEFAULT_CONFIG = custom_cfg
        logger.info(f"Loaded custom configuration from {config_path}")

    # Load CSV
    csv_path = Path(path).resolve()
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    try:
        if csv_path.suffix == ".ods":
            df = pd.read_excel(csv_path, engine="calamine")
        else:
            df = pd.read_csv(csv_path, sep=None, engine="python")
    except Exception as e:
        logger.error(f"Failed to read CSV file {csv_path}: {e}")
        sys.exit(1)

    # Normalize column names to lowercase and stripped
    df.columns = [col.strip().lower() for col in df.columns]

    required_cols = {"title", "company", "description"}
    if not required_cols.issubset(df.columns):
        logger.error(f"CSV file must contain 'title', 'company', and 'description' columns. Found: {list(df.columns)}")
        sys.exit(1)

    mtime = csv_path.stat().st_mtime
    timestamp = datetime.fromtimestamp(mtime).strftime(r"%Y-%m-%d_%H-%M-%S")
    output_dir = (Path(folder) / f"from_csv_{csv_path.stem}" / timestamp).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Processing {} job postings from {}", len(df), csv_path)

    for idx, row in tqdm(df.iterrows(), total=len(df)):
        title = str(row["title"]).strip() if pd.notna(row["title"]) else ""
        company = str(row["company"]).strip() if pd.notna(row["company"]) else ""
        description = str(row["description"]) if pd.notna(row["description"]) else ""

        if not title or not company:
            logger.warning(f"Row {idx} skipped: missing title or company.")
            continue

        job_id = generate_id(title, company)
        if not job_id:
            logger.warning(f"Row {idx} skipped: failed to generate a valid job id.")
            continue

        job_folder = output_dir / job_id
        job_folder.mkdir(parents=True, exist_ok=True)

        logger.info(f"[{idx + 1}/{len(df)}] Processing job '{title}' at '{company}' (ID: {job_id})")

        jd_file = job_folder / "jd.txt"
        jd_file.write_text(description, encoding="utf-8")

        try:
            compose_resume(
                folder=job_folder,
                model=model,
                force=force,
                feedback=feedback,
            )
        except Exception as e:
            logger.error(f"Failed to compose Resume for job ID {job_id}: {e}")
