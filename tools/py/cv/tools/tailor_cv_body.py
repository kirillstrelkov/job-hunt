#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Ensure tools/py is in sys.path to import helpers
tools_py_dir = Path(__file__).resolve().parent.parent.parent / "tools/py"
if str(tools_py_dir) not in sys.path:
    sys.path.insert(0, str(tools_py_dir))

from loguru import logger
from helpers.ollama_helper import run_model, get_eval_model, get_model_options


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Tailor CV using a local LLM via Ollama.")
    parser.add_argument(
        "--prompt-file",
        required=True,
        type=Path,
        help="Path to the prompt markdown/txt file",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to the output tailored markdown file",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Ollama model to use. Defaults to the configured eval model.",
    )
    return parser.parse_args()


def run_ollama(prompt_content: str, model: str) -> dict:
    """Run Ollama model on the prompt content."""
    model_options = get_model_options(model)
    logger.info(f"Running LLM model '{model}' via Ollama...")
    return run_model(
        model=model,
        prompt_content=prompt_content,
        options=model_options,
    )


def process_output_of_ollama(result: dict, output_file: Path) -> None:
    """Process result from Ollama, trim the response to the CV content, and write it to the output file."""
    response_text = result.get("response", "")

    lines = response_text.splitlines()
    start_idx = 0
    for i, line in enumerate(lines):
        if "Summary" in line:
            start_idx = i
            break

    end_idx = len(lines)
    for i in range(start_idx, len(lines)):
        if "TAILORING JUSTIFICATION REPORT" in lines[i]:
            end_idx = i
            break

    trimmed_text = "\n".join(lines[start_idx:end_idx]).strip()
    output_file = Path(output_file).resolve()

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing tailored CV to: {output_file}")
    output_file.write_text(trimmed_text, encoding="utf-8")

    logger.info(f"Success! Tokens per second: {result.get('tokens_per_sec', 0.0):.2f}")


def main() -> None:
    args = parse_args()

    prompt_file = Path(args.prompt_file).resolve()
    output_file = Path(args.output).resolve()

    if not prompt_file.exists():
        logger.error(f"Prompt file not found at: {prompt_file}")
        sys.exit(1)

    logger.info(f"Reading prompt from: {prompt_file}")
    prompt_content = prompt_file.read_text(encoding="utf-8")

    model = args.model if args.model else get_eval_model()

    try:
        result = run_ollama(prompt_content, model)
        process_output_of_ollama(result, output_file)
    except Exception as e:
        logger.error(f"Failed to generate tailored CV: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
