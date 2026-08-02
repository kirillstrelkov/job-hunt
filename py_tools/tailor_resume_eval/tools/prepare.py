"""Evaluation preparation script for LLM prompts."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from helpers.config import DEFAULT_CONFIG
from loguru import logger


def main() -> None:
    """Prepare LLM prompt for evaluation."""
    logger.info("Preparing LLM Prompt")
    if not os.getenv("MASTERCV_PATH"):
        logger.error("MASTERCV_PATH not set")
        sys.exit(1)

    job = DEFAULT_CONFIG.get_jobs()[0]
    output_file = Path(job.llm_prompt_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Resolve prepare script path
    script_path = DEFAULT_CONFIG.get_config_value_as_path(".prepare_llm_prompt_script")
    if not script_path.exists():
        logger.error(f"Prepare prompt script not found at: {script_path}")
        sys.exit(1)

    jd_input = Path(job.description_path)
    if not jd_input.exists():
        logger.error(f"Job description input not found at: {jd_input}")
        sys.exit(1)

    # Run prepare script using subprocess
    logger.info(f"Running prompt preparation script: {script_path.name}...")
    uv_cmd = shutil.which("uv") or "uv"
    try:
        subprocess.run(  # noqa: S603
            [
                uv_cmd,
                "run",
                str(script_path),
                "--output",
                str(output_file),
                "--tailor-for-description",
                "--job-description",
                str(jd_input),
            ],
            check=True,
        )
        logger.info(f"Successfully generated baseline prompt at: {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate prompt: {e}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
