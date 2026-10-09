"""Scaffold workspace directory, extracted JDs, and LLM tailoring prompts from job match listings."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger
from tabulate import tabulate
from tqdm import tqdm

from job_hunt.config import config as cfg
from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.job_finder.utils.models import JobMatch
from job_hunt.job_finder.utils.okf import write_job
from job_hunt.resume import prepare_resume
from job_hunt.resume.compose_jobs_from_csv import generate_id
from job_hunt.resume.prepare_resume import generate_llm_prompt


def filter_job_listings(
    df: pd.DataFrame,
    min_score: float = 80,
) -> pd.DataFrame:
    """Filter job listings by match percentage and screening check status.

    Args:
        df: Raw DataFrame loaded from CSV or ODS.
        min_score: Minimum match percentage threshold (inclusive).

    Returns:
        Filtered DataFrame containing matching jobs.

    """
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]

    required_cols = {"title", "company", "description"}
    if not required_cols.issubset(df.columns):
        # Check if the header row was preceded by empty rows or banners
        for idx, row in df.head(10).iterrows():
            row_vals = {str(v).strip().lower() for v in row.values if pd.notna(v)}
            if required_cols.issubset(row_vals):
                df.columns = [str(v).strip().lower() for v in row.values]
                df = df.iloc[idx + 1 :].reset_index(drop=True)
                break

    if not required_cols.issubset(df.columns):
        msg = f"Data file must contain 'title', 'company', and 'description' columns. Found: {list(df.columns)}"
        raise ValueError(msg)

    # Check for check_passed column
    if "check_passed" in df.columns:

        def _is_passed(val: Any) -> bool:
            if pd.isna(val):
                return False
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return bool(val)
            return str(val).strip().lower() in ("true", "1", "t", "yes", "passed")

        df = df[df["check_passed"].apply(_is_passed)]

    # Check for match_percentage column
    if "match_percentage" in df.columns:
        df["match_percentage"] = pd.to_numeric(df["match_percentage"], errors="coerce").fillna(0)
        df = df[df["match_percentage"] >= min_score]

    # Filter out empty title or company
    return df[df["title"].astype(str).str.strip().ne("") & df["company"].astype(str).str.strip().ne("")]


def print_scaffold_summary(records: list[dict[str, Any]]) -> None:
    """Print a formatted summary table of scaffolded job folders."""
    if not records:
        logger.info("No records to display.")
        return

    headers = ["#", "Job ID", "Company", "Title", "Fit Score", "Prompt File", "Status"]
    table_data = [
        [
            r["index"],
            r["job_id"],
            r["company"],
            r["title"][:40] + "..." if len(r["title"]) > 40 else r["title"],
            r["score"],
            r["prompt"],
            r["status"],
        ]
        for r in records
    ]

    try:
        print("\n" + tabulate(table_data, headers=headers, tablefmt="rounded_outline") + "\n")
    except UnicodeEncodeError:
        print("\n" + tabulate(table_data, headers=headers, tablefmt="grid") + "\n")


def scaffold_jobs_from_csv(
    path: str | Path,
    folder: str | Path = "tmp/manual_jds",
    min_score: float = 80,
    force: bool = False,
    config: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Read CSV/ODS, filter jobs, scaffold workspace folders, and generate prompts.

    Args:
        path: Path to CSV or ODS file.
        folder: Output base folder.
        min_score: Minimum match score threshold.
        force: Whether to overwrite existing files.
        config: Optional custom configuration file.

    Returns:
        List of dictionaries representing scaffolded jobs metadata.

    """
    if config:
        config_path = Path(config).resolve()
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            raise FileNotFoundError(f"Config file not found: {config_path}")
        custom_cfg = cfg.ConfigManager(config_path)
        cfg.DEFAULT_CONFIG = custom_cfg
        prepare_resume.DEFAULT_CONFIG = custom_cfg
        logger.info(f"Loaded custom configuration from {config_path}")

    csv_path = Path(path).resolve()
    if not csv_path.exists():
        logger.error(f"Data file not found: {csv_path}")
        raise FileNotFoundError(f"Data file not found: {csv_path}")

    try:
        if csv_path.suffix.lower() == ".ods":
            df = pd.read_excel(csv_path, engine="calamine")
        else:
            df = pd.read_csv(csv_path, sep=None, engine="python")
    except Exception as e:
        logger.error(f"Failed to read file {csv_path}: {e}")
        raise RuntimeError(f"Failed to read file {csv_path}: {e}") from e

    filtered_df = filter_job_listings(df, min_score=min_score)
    logger.info(f"Found {len(filtered_df)} matching job postings (>= {min_score}%) from {csv_path}")

    if filtered_df.empty:
        logger.warning("No job listings matched the filter criteria.")
        return []

    timestamp = datetime.now(tz=UTC).strftime(r"%Y-%m-%d_%H-%M-%S")
    output_dir = (Path(folder) / timestamp).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    template_path = DEFAULT_CONFIG.tailor.prompt
    master_resume = DEFAULT_CONFIG.composer.body

    records = []

    for idx, (_, row) in enumerate(tqdm(filtered_df.iterrows(), total=len(filtered_df)), start=1):
        title = str(row["title"]).strip()
        company = str(row["company"]).strip()
        description = str(row["description"]) if pd.notna(row["description"]) else ""
        score = row.get("match_percentage", min_score)

        job_id = generate_id(title, company)
        if not job_id:
            logger.warning(f"Skipping row with invalid job id: title='{title}', company='{company}'")
            continue

        job_folder = output_dir / job_id
        job_folder.mkdir(parents=True, exist_ok=True)

        job_file = job_folder / "job.md"
        if force or not job_file.exists():
            match_score = int(score) if pd.notna(score) and isinstance(score, (int, float)) else -1
            job = JobMatch(
                title=title,
                company=company,
                url=str(row.get("url", "")),
                description=description,
                match_percentage=match_score,
                check_passed=bool(row.get("check_passed", True)),
                llm_text=str(row.get("llm_text", "")),
                error=str(row.get("error", "")),
            )
            write_job(job, job_file)

        prompt_file = job_folder / "prompt.md"
        if force or not prompt_file.exists():
            prompt_content = generate_llm_prompt(
                template=template_path,
                resume_body=master_resume,
                job_description=job_file,
                job_title=title,
            )
            prompt_file.write_text(prompt_content, encoding="utf-8")

        records.append(
            {
                "index": idx,
                "job_id": job_id,
                "company": company,
                "title": title,
                "score": f"{score:.0f}%" if isinstance(score, (int, float)) else str(score),
                "folder": str(job_folder),
                "prompt": str(prompt_file),
                "status": "Scaffolded",
            }
        )

    print_scaffold_summary(records)
    return records
