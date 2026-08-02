#!/usr/bin/env python3
"""Execute a prompt against a single Ollama model for performance testing."""

import sys
from pathlib import Path

from loguru import logger

from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.core.ollama_helper import get_eval_model, get_model_options, run_model
from job_hunt.core.tmp_helper import get_llm_prompt_for_job


def main(
    prompt: str | None = None,
    model: str | None = None,
    show_response: bool = False,
) -> None:
    """Run a single prompt on a selected Ollama model and log performance metrics."""
    default_llm_prompt_path = get_llm_prompt_for_job(DEFAULT_CONFIG.get_jobs()[0])
    prompt_path = Path(prompt) if prompt else default_llm_prompt_path
    resolved_model = model or get_eval_model()

    if not prompt_path.exists():
        logger.error(f"Prompt file '{prompt_path}' not found.")
        sys.exit(1)

    try:
        prompt_content = prompt_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Error reading prompt file: {e}")
        sys.exit(1)

    try:
        options = get_model_options(resolved_model)
    except ValueError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

    logger.info(f"Executing prompt on model '{resolved_model}' with options {options}...")
    try:
        stat = run_model(resolved_model, prompt_content, options=options)
        for key, val in stat.items():
            if key != "response":
                logger.info(f"{key}: {val}")
        if show_response:
            resp = stat["response"].strip()
            if resp:
                logger.info(resp)
            else:
                logger.warning("Response is empty.")
    except Exception as e:
        logger.error(f"Error executing prompt: {e}")
        sys.exit(1)
