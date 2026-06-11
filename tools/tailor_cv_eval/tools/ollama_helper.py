import sys
from functools import lru_cache
from pathlib import Path

import ollama

# Add root directory to path to import shared config
sys.path.append(str(Path(__file__).resolve().parents[1]))
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
