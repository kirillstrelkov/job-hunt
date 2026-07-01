#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path

from loguru import logger

from helpers.llm import get_agent
from helpers.ollama_helper import get_eval_model


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Tailor CV body using a local LLM via Ollama.")
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force generation even if the output file already exists",
    )
    return parser.parse_args()


def run_ollama(prompt_content: str, model: str) -> dict:
    """Run Ollama model on the prompt content using Pydantic AI Agent."""
    logger.info(f"Running LLM model '{model}' via Ollama Pydantic AI agent...")
    start_time = time.time()
    agent = get_agent(
        model_name=model,
        output_type=str,
    )
    result = agent.run_sync(prompt_content)
    elapsed = time.time() - start_time

    response_text = result.output

    usage = result.usage
    prompt_tokens = usage.input_tokens or 0
    gen_tokens = usage.output_tokens or 0
    tokens_per_sec = gen_tokens / elapsed if elapsed > 0.001 else 0.0

    return {
        "model": model,
        "total_time": elapsed,
        "load_time": 0.0,
        "prompt_tokens": prompt_tokens,
        "gen_tokens": gen_tokens,
        "tokens_per_sec": tokens_per_sec,
        "char_count": len(response_text),
        "word_count": len(response_text.split()),
        "gpu_usage": 0.0,
        "gpu_info": None,
        "response": response_text,
    }


def process_output_of_ollama(result: dict, output_file: Path) -> None:
    """Process result from Ollama, trim the response to the CV content, and write it to the output file."""
    if (gen_tokens := result.get("gen_tokens")) < 100:
        logger.warning(
            f"WARNING!!!! Generated {gen_tokens} tokens is too small. This may be because context is too small."
        )

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

    if output_file.exists() and not args.force:
        logger.warning(f"Output file already exists at: {output_file}. Skipping generation. Use --force to overwrite.")
        sys.exit(0)

    logger.info(f"Reading prompt from: {prompt_file}")
    prompt_content = prompt_file.read_text(encoding="utf-8")

    model = args.model or get_eval_model()

    try:
        result = run_ollama(prompt_content, model)
        process_output_of_ollama(result, output_file)
    except Exception as e:
        logger.error(f"Failed to generate tailored CV: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
