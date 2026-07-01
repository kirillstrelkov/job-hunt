"""CLI script to run batch CV tailoring from jobs in a CSV file."""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
from loguru import logger
from tqdm import tqdm

from cv.tools import cfg, prepare_cv
from cv.tools.tailor_cv_locally import tailor

WORD_PATTERN = re.compile(r"\w{2,}")


def generate_id(title: str, company: str) -> str:
    """Generate a clean slug/id based on the first 4 words of 2 or more characters in title and first 2 in company."""
    title_words = WORD_PATTERN.findall(title.lower())[:5]
    company_words = WORD_PATTERN.findall(company.lower())[:2]
    return "_".join(title_words + company_words)


def main() -> None:  # noqa: PLR0915
    """Run batch CV tailoring by reading job postings from a CSV file."""
    parser = argparse.ArgumentParser(
        description="Read job postings from a CSV and tailor CVs locally for each posting."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to the CSV file containing job postings.",
    )
    parser.add_argument(
        "--config",
        help="Optional path to a custom configuration YAML file.",
    )
    parser.add_argument(
        "--folder",
        required=True,
        help="Output folder where folders and files for each job should be created.",
    )
    parser.add_argument(
        "--model",
        help="Optional Ollama model to use for tailoring. If not set, defaults to configured eval model.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force execution of Step 2 (LLM tailoring) even if tailored body already exists.",
    )
    args = parser.parse_args()

    # Load custom config if specified
    if args.config:
        config_path = Path(args.config).resolve()
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        custom_cfg = cfg.load_config(config_path)
        cfg.DEFAULT_CONFIG = custom_cfg
        prepare_cv.DEFAULT_CONFIG = custom_cfg
        logger.info(f"Loaded custom configuration from {config_path}")

    # Load CSV
    csv_path = Path(args.path).resolve()
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(csv_path, sep=None, engine="python")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to read CSV file {csv_path}: {e}")
        sys.exit(1)

    # Normalize column names to lowercase and stripped
    df.columns = [col.strip().lower() for col in df.columns]

    required_cols = {"title", "company", "description"}
    if not required_cols.issubset(df.columns):
        logger.error(f"CSV file must contain 'title', 'company', and 'description' columns. Found: {list(df.columns)}")
        sys.exit(1)

    output_dir = Path(args.folder).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Processing {len(df)} job postings from CSV...")

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
            tailor(folder=job_folder, model=args.model, force=args.force)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to tailor CV for job ID {job_id}: {e}")


if __name__ == "__main__":
    main()
