import sys
import os
import subprocess
from pathlib import Path
from loguru import logger

# Add root directory to path to import helpers
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR.parent))

from helpers.config import DEFAULT_CONFIG, LLM_PROMPT_OUTPUT_FILE
from helpers.tmp_helper import get_tmp_output_dir


def main():
    logger.info("Preparing LLM Prompt")
    if not os.getenv("MASTERCV_PATH"):
        logger.error("MASTERCV_PATH not set")
        sys.exit(1)

    job = DEFAULT_CONFIG.get_jobs()[0]
    prompt_name = Path(LLM_PROMPT_OUTPUT_FILE).name
    output_dir = get_tmp_output_dir() / job.name
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / prompt_name

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
    try:
        subprocess.run(
            [
                "uv",
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
