"""Gemini integration helpers using Pydantic AI for model executions."""

import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.gemini import GeminiModel

from helpers.config import DEFAULT_CONFIG, ConfigManager

MIN_EVAL_TIME = 0.001


def check_if_file_fits_into_ctx_num(path: str | Path, ctx_num: int) -> bool:
    tokens = len(Path(path).read_text(encoding="utf-8")) // 4
    if tokens > ctx_num:
        logger.error(f"The file {path} has {tokens} tokens, which is less than the context window of {ctx_num} tokens.")
        return False

    return True


@lru_cache
def __get_supported_models() -> list[str]:
    """Get list of supported Gemini models."""
    return [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.0-pro-exp-02-05",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash-8b",
    ]


def __check_models_supported(models: list[str]) -> None:
    supported = __get_supported_models()
    for model in models:
        # Lenient prefix check: allow if it matches a known model or starts with gemini
        if model not in supported and not model.startswith("gemini"):
            msg = f"Model '{model}' is not a recognized Gemini model. Supported models are: {', '.join(supported)}"
            raise ValueError(msg)


def get_top_model_names(config_manager: ConfigManager = DEFAULT_CONFIG) -> list[str]:
    """Get top model names."""
    try:
        models = config_manager.get_config_value(".top_models")
        # Filter for gemini models
        gemini_models = [m for m in models if m.startswith("gemini")]
        if gemini_models:
            __check_models_supported(gemini_models)
            return gemini_models
    except Exception:
        pass
    return ["gemini-2.0-flash", "gemini-1.5-flash"]


def get_model_names(config_manager: ConfigManager = DEFAULT_CONFIG) -> list[str]:
    """Get all configured model names."""
    try:
        models_list = config_manager.get_config_value(".models")
        models = [item["name"] for item in models_list]
        gemini_models = [m for m in models if m.startswith("gemini")]
        if gemini_models:
            __check_models_supported(gemini_models)
            return gemini_models
    except Exception:
        pass
    return ["gemini-2.0-flash", "gemini-1.5-flash"]


def get_models_with_options(
    config_manager: ConfigManager = DEFAULT_CONFIG,
) -> list[dict]:
    """Get all configured models along with their full options."""
    model_names = get_model_names(config_manager=config_manager)

    return [
        {
            "name": model,
            "options": get_model_options(model, config_manager=config_manager),
        }
        for model in model_names
    ]


def get_eval_model(config_manager: ConfigManager = DEFAULT_CONFIG) -> str:
    """Get the configured evaluation model name."""
    try:
        eval_model = config_manager.get_config_value(".eval_model")
        if eval_model.startswith("gemini"):
            return eval_model
    except Exception:
        pass
    return "gemini-2.0-flash"


def get_model_options(model: str, config_manager: ConfigManager = DEFAULT_CONFIG) -> dict:
    """Get configuration settings for a given model.
    If the model is not explicitly configured in config.yaml, returns default options.
    """
    try:
        default_options = config_manager.get_config_value(".model_default_options") or {}
    except Exception:
        default_options = {}

    try:
        models_config = config_manager.get_config_value(".models")
        for item in models_config:
            if item["name"] == model:
                options = default_options.copy()
                if model_options := item.get("options"):
                    options.update(model_options)
                return options
    except Exception:
        pass

    return default_options.copy()


def dict_to_model_settings(options: dict | None) -> ModelSettings:
    """Convert options dictionary to Pydantic AI ModelSettings."""
    if not options:
        return ModelSettings()

    settings = {}

    # Map temperature
    if "temperature" in options:
        settings["temperature"] = float(options["temperature"])

    # Map max_tokens / num_predict
    if "max_tokens" in options:
        settings["max_tokens"] = int(options["max_tokens"])
    elif "num_predict" in options:
        num_predict = int(options["num_predict"])
        if num_predict > 0:
            settings["max_tokens"] = num_predict

    # Map top_p
    if "top_p" in options:
        settings["top_p"] = float(options["top_p"])

    # Map top_k
    if "top_k" in options:
        settings["top_k"] = int(options["top_k"])

    # Map seed
    if "seed" in options:
        settings["seed"] = int(options["seed"])

    # Map presence_penalty
    if "presence_penalty" in options:
        settings["presence_penalty"] = float(options["presence_penalty"])

    # Map frequency_penalty
    if "frequency_penalty" in options:
        settings["frequency_penalty"] = float(options["frequency_penalty"])

    # Map timeout
    if "timeout" in options:
        settings["timeout"] = float(options["timeout"])

    return ModelSettings(**settings)


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


def run_model(model: str, prompt_content: str, options: dict | None = None) -> dict:
    """Run a prompt through the specified Gemini model with timing and usage stats."""
    if options is None:
        options = get_model_options(model)
    start_time = time.time()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    model_settings = dict_to_model_settings(options)
    gemini_model = GeminiModel(model, api_key=api_key)
    agent = Agent(gemini_model)

    result = agent.run_sync(prompt_content, model_settings=model_settings)
    elapsed = time.time() - start_time

    response = result.data
    usage = result.usage()
    prompt_tokens = usage.request_tokens or 0
    gen_tokens = usage.response_tokens or 0

    if not response.strip() or gen_tokens == 0:
        tokens_per_sec = 0.0
    else:
        tokens_per_sec = gen_tokens / elapsed if elapsed > MIN_EVAL_TIME else 0.0

    logger.debug(f"Time for generation: {elapsed:.2f} s")
    logger.debug(f"Prompt tokens: {prompt_tokens}, Gen tokens: {gen_tokens}")

    return {
        "model": model,
        "total_time": elapsed,
        "load_time": 0.0,
        "prompt_tokens": prompt_tokens,
        "gen_tokens": gen_tokens,
        "tokens_per_sec": tokens_per_sec,
        "char_count": len(response),
        "word_count": len(response.split()),
        "gpu_usage": 0.0,
        "gpu_info": None,
        "response": response,
        "options_str": format_options(options),
    }


def generate_response(model: str, prompt: str, options: dict | None = None) -> str:
    """Generate response from Gemini directly using Pydantic AI agent."""
    merged_options = get_model_options(model).copy()
    if options:
        merged_options.update(options)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    model_settings = dict_to_model_settings(merged_options)
    gemini_model = GeminiModel(model, api_key=api_key)
    agent = Agent(gemini_model)

    result = agent.run_sync(prompt, model_settings=model_settings)
    return result.data


def get_model_output(model: str, prompt_content: str, output_file: Path, options: dict | None = None) -> str:
    """Get the generated content from a cached file or generate it using Gemini if not present."""
    if output_file.exists():
        return output_file.read_text(encoding="utf-8")

    # Otherwise generate it once and store it
    output_file.parent.mkdir(parents=True, exist_ok=True)
    actual = generate_response(model, prompt_content, options=options)
    output_file.write_text(actual, encoding="utf-8")
    return actual


def call_api(prompt: str, options: dict, _context: Any = None) -> dict:  # noqa: ANN401
    """Promptfoo custom Python provider call API interface."""
    config = options.get("config", {})
    model = config.get("model", get_eval_model())

    # Extract all other parameters as options
    model_options = {key: val for key, val in config.items() if key != "model"}

    try:
        response = generate_response(model, prompt, options=model_options)
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
    else:
        return {"output": response}
