#!/usr/bin/env python
import argparse
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import ollama
from loguru import logger

# Add root directory to path to import tools
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from config import ConfigManager  # noqa: E402
from tools.ollama_helper import get_model_options  # noqa: E402


@contextmanager
def track_ollama_gpu(model_name: str, interval_seconds: float = 0.5):
    """
    Context manager to track Ollama GPU metrics during generation.
    Yields a shared dict that tracks model size and history of VRAM usage.
    """
    history = {"model_size": 0, "gpu_used": []}
    stop_event = threading.Event()

    def monitor_loop():
        while not stop_event.is_set():
            try:
                status = ollama.ps()
                # Find matching model
                target = next((m for m in status.models if m.model == model_name), None)
                if target and target.size > 0:
                    history["model_size"] = target.size
                    history["gpu_used"].append(target.size_vram)
            except Exception:
                pass  # Ignore network drops or busy socket errors
            stop_event.wait(timeout=interval_seconds)

    # Start the monitoring background thread
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()

    try:
        # Give control back to the 'with' block, sharing the history dict
        yield history
    finally:
        # Guarantee cleanup: stop and join thread when leaving 'with' block
        stop_event.set()
        thread.join()


def run_model(model: str, prompt_content: str, options: dict = None, config_manager: ConfigManager = None) -> dict:
    if options is None:
        options = get_model_options(model, config_manager=config_manager)
    start_time = time.time()

    with track_ollama_gpu(model, interval_seconds=0.5) as gpu_data:
        res = ollama.generate(
            model=model,
            prompt=prompt_content,
            options=options,
            keep_alive=0,
        )
    elapsed = time.time() - start_time

    avg_gpu = None
    gpu_info = None
    if gpu_data and gpu_data.get("gpu_used"):
        model_size = gpu_data["model_size"]
        gpu_used = gpu_data["gpu_used"]
        max_vram = max(gpu_used)

        gpu_pcts = [(vram / model_size) * 100.0 for vram in gpu_used] if model_size > 0 else []
        avg_gpu = sum(gpu_pcts) / len(gpu_pcts) if gpu_pcts else 0.0

        logger.debug(f"Snapshots taken: {len(gpu_used)}")
        logger.debug(f"Average GPU usage: {avg_gpu:.1f}%")
        gpu_info = f"{max_vram / (1024**3):.2f} GB / {model_size / (1024**3):.2f} GB"
        logger.debug(f"Max VRAM / Model size: {gpu_info}")
    else:
        logger.warning("No snapshots captured. The prompt completed too fast or the model layout wasn't visible.")

    response = res.get("response", "")
    total_duration = (res.get("total_duration") or 0) / 1e9
    load_duration = (res.get("load_duration") or 0) / 1e9
    prompt_eval_count = res.get("prompt_eval_count") or 0
    eval_count = res.get("eval_count") or 0
    eval_duration = (res.get("eval_duration") or 0) / 1e9

    total_time = total_duration if total_duration > 0 else elapsed
    eval_time = eval_duration if eval_duration > 0 else elapsed

    if not response.strip() or eval_count == 0:
        tokens_per_sec = 0.0
    else:
        tokens_per_sec = eval_count / eval_time if eval_time > 0.001 else 0.0

    return {
        "model": model,
        "total_time": total_time,
        "load_time": load_duration,
        "prompt_tokens": prompt_eval_count,
        "gen_tokens": eval_count,
        "tokens_per_sec": tokens_per_sec,
        "char_count": len(response),
        "word_count": len(response.split()),
        "gpu_usage": avg_gpu / 100.0 if avg_gpu is not None else 1.0,
        "gpu_info": gpu_info,
        "response": response,
    }


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
        stat = run_model(args.model, prompt_content)
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
