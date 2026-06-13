import sys
import threading
import time
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import ollama
from loguru import logger

# Add tailor_cv_eval directory to path to import shared config
sys.path.append(str(Path(__file__).resolve().parents[1] / "tailor_cv_eval"))
from config import _DEFAULT_CONFIG, ConfigManager


@lru_cache
def __get_ollama_models() -> list[str]:
    return [m.model for m in ollama.list().models]


def __check_models_in_ollama(models: list[str]) -> None:
    ollama_models = __get_ollama_models()
    for model in models:
        if model not in ollama_models:
            raise ValueError(
                f"Model '{model}' is configured but not found in Ollama. "
                f"Please run 'ollama pull {model}' to download it."
            )


def get_models(config_manager: ConfigManager = None) -> list[str]:
    cfg = config_manager or _DEFAULT_CONFIG
    models_list = cfg.get_config_value(".models")
    models = [item["name"] for item in models_list]
    __check_models_in_ollama(models)
    return models


def get_eval_model(config_manager: ConfigManager = None) -> str:
    cfg = config_manager or _DEFAULT_CONFIG
    eval_model = cfg.get_config_value(".eval_model")
    __check_models_in_ollama([eval_model])
    return eval_model


def get_model_options(model: str, config_manager: ConfigManager = None) -> dict:
    """Get configuration settings for a given model.

    Raises ValueError if the model is not configured.
    """
    cfg = config_manager or _DEFAULT_CONFIG
    models_list = cfg.get_config_value(".models")
    eval_model = get_eval_model(config_manager=cfg)
    if model == eval_model:
        for item in models_list:
            if item["name"] == model:
                return item["options"]
        raise ValueError(f"Model '{model}' not found in config")

    for item in models_list:
        if item["name"] == model:
            return item["options"]

    raise ValueError(f"Model '{model}' is not configured.")


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


def format_options(options: dict) -> str:
    """Format model options dictionary into a readable string."""
    if not options:
        return ""
    parts = []
    if "num_ctx" in options:
        parts.append(f"ctx: {options['num_ctx']}")
    if "num_predict" in options:
        parts.append(f"pred: {options['num_predict']}")
    if "temperature" in options:
        parts.append(f"temp: {options['temperature']}")
    for k, v in options.items():
        if k not in ["num_ctx", "num_predict", "temperature"]:
            parts.append(f"{k}: {v}")
    return ", ".join(parts)


def run_model(model: str, prompt_content: str, options: dict = None) -> dict:
    if options is None:
        options = get_model_options(model)
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
        "options_str": format_options(options),
    }


def generate_response(model: str, prompt: str, options: dict = None) -> str:
    """Generate response from Ollama directly without caching."""
    merged_options = get_model_options(model).copy()
    if options:
        merged_options.update(options)
    res = ollama.generate(model=model, prompt=prompt, keep_alive=0, options=merged_options)
    return res.get("response", "")


def get_model_output(model: str, prompt_content: str, output_file: Path, options: dict = None) -> str:
    """Get the generated CV from a cached file or generate it using Ollama if not present."""
    if output_file.exists():
        return output_file.read_text(encoding="utf-8")

    # Otherwise generate it once and store it
    output_file.parent.mkdir(parents=True, exist_ok=True)
    actual = generate_response(model, prompt_content, options=options)
    output_file.write_text(actual, encoding="utf-8")
    return actual


def call_api(prompt, options, context=None):
    """Promptfoo custom Python provider call API interface."""
    config = options.get("config", {})
    model = config.get("model", get_eval_model())

    # Extract all other parameters as ollama options
    ollama_options = {}
    for key, val in config.items():
        if key != "model":
            ollama_options[key] = val

    try:
        response = generate_response(model, prompt, options=ollama_options)
        return {"output": response}
    except Exception as e:
        return {"error": str(e)}
