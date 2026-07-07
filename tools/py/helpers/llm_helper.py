"""Gemini integration helpers using Pydantic AI for model executions."""

import os
import time
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.google import GoogleModel

from config.config import DEFAULT_CONFIG, ConfigManager

MIN_EVAL_TIME = 0.001


def get_eval_model(config_manager: ConfigManager = DEFAULT_CONFIG) -> str:
    """Get the evaluation model."""
    return config_manager.get_config_value(".eval_model")


def get_model_names(config_manager: ConfigManager = DEFAULT_CONFIG) -> list[str]:
    """Get all configured model names."""
    return config_manager.get_config_value(".gemini_models")


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


def get_model_options(model: str, config_manager: ConfigManager = DEFAULT_CONFIG) -> dict:
    """Get configuration settings for a given model.

    If the model is not explicitly configured in config.yaml, returns default options.
    """
    try:
        default_options = config_manager.get_config_value(".model_default_options") or {}
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Failed to get default model options: {e}")
        default_options = {}

    try:
        models_config = config_manager.get_config_value(".models")
        for item in models_config:
            if item["name"] == model:
                options = default_options.copy()
                if model_options := item.get("options"):
                    options.update(model_options)
                return options
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Failed to get options for model {model}: {e}")

    return default_options.copy()


def dict_to_model_settings(options: dict | None) -> ModelSettings:
    """Convert options dictionary to Pydantic AI ModelSettings."""
    if not options:
        return ModelSettings()

    settings = {}

    # Define mapping of option keys to types for straightforward properties
    float_keys = ["temperature", "top_p", "presence_penalty", "frequency_penalty", "timeout"]
    int_keys = ["top_k", "seed"]

    for k in float_keys:
        if k in options:
            settings[k] = float(options[k])

    for k in int_keys:
        if k in options:
            settings[k] = int(options[k])

    # Map max_tokens / num_predict
    if "max_tokens" in options:
        settings["max_tokens"] = int(options["max_tokens"])
    elif "num_predict" in options:
        num_predict = int(options["num_predict"])
        if num_predict > 0:
            settings["max_tokens"] = num_predict

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

    if not os.environ.get("GEMINI_API_KEY"):
        msg = "GEMINI_API_KEY environment variable is not set"
        raise RuntimeError(msg)

    model_settings = dict_to_model_settings(options)
    gemini_model = GoogleModel(model)
    agent = Agent(gemini_model, model_settings=model_settings)

    result = agent.run_sync(prompt_content)
    elapsed = time.time() - start_time

    response = result.output
    usage = result.usage
    prompt_tokens = usage.input_tokens or 0
    gen_tokens = usage.output_tokens or 0

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

    if not os.environ.get("GEMINI_API_KEY"):
        msg = "GEMINI_API_KEY environment variable is not set"
        raise RuntimeError(msg)

    model_settings = dict_to_model_settings(merged_options)
    gemini_model = GoogleModel(model)
    agent = Agent(gemini_model, model_settings=model_settings)

    result = agent.run_sync(prompt)
    return result.output


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
    gemini_models = get_model_names()
    default_model = gemini_models[0] if gemini_models else "gemini-2.5-flash"
    model = config.get("model", default_model)

    # Extract all other parameters as options
    model_options = {key: val for key, val in config.items() if key != "model"}

    try:
        response = generate_response(model, prompt, options=model_options)
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
    else:
        return {"output": response}
