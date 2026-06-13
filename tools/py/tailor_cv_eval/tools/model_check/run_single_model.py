#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

from loguru import logger

# Add root directory to path to import tools
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR.parent))

from config import ConfigManager  # noqa: E402
from helpers.ollama_helper import get_model_options, run_model  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Run a single prompt against a specific Ollama model.")
    parser.add_argument(
        "--prompt",
        required=True,
        type=str,
        help="Path to the prompt markdown file.",
    )
    parser.add_argument(
        "--model",
        required=True,
        type=str,
        help="Ollama model name to execute the prompt.",
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
