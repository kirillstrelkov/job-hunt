#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

from loguru import logger


from helpers.config import DEFAULT_CONFIG  # noqa: E402
from helpers.ollama_helper import get_eval_model, get_model_options, run_model  # noqa: E402
from helpers.tmp_helper import get_llm_prompt_for_job  # noqa: E402


def main():
    default_llm_prompt_path = get_llm_prompt_for_job(DEFAULT_CONFIG.get_jobs()[0])

    parser = argparse.ArgumentParser(description="Run a single prompt against a specific Ollama model.")
    parser.add_argument(
        "--prompt",
        type=str,
        default=str(default_llm_prompt_path),
        help="Path to the prompt markdown file (default: resolved path from config).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=get_eval_model(),
        help="Ollama model name to execute the prompt (default: resolved evaluation model from config).",
    )
    parser.add_argument(
        "--show-response",
        action="store_true",
        help="Show the model's full response in the logs.",
    )

    args = parser.parse_args()

    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        logger.error(f"Prompt file '{args.prompt}' not found.")
        sys.exit(1)

    try:
        prompt_content = prompt_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Error reading prompt file: {e}")
        sys.exit(1)

    try:
        options = get_model_options(args.model)
    except ValueError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

    logger.info(f"Executing prompt on model '{args.model}' with options {options}...")
    try:
        stat = run_model(args.model, prompt_content, options=options)
        for key, val in stat.items():
            if key != "response":
                logger.info(f"{key}: {val}")
        if args.show_response:
            resp = stat["response"].strip()
            if resp:
                logger.info(resp)
            else:
                logger.warning("Response is empty.")
    except Exception as e:
        logger.error(f"Error executing prompt: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
