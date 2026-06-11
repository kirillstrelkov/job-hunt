#!/usr/bin/env python
import sys
from pathlib import Path

import yaml

# Add root directory to path to ensure proper imports
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

# Standard configuration template
CONFIG_TEMPLATE = {
    "models": [],
    "eval_model": "llama3.1:8b",
    "tmp_output_dir": "tmp/outputs",
    "llm_prompt_output_file": "llm_prompt.md",
    "trulens_db_url": "sqlite:///tmp/outputs/truelens/default.sqlite",
}


def _generate_config(
    models: list[str],
    models_data: dict | None,
    default_options: dict | None,
) -> dict:
    """Generate a configuration dictionary using standard templates.

    Args:
        models: List of model names.
        models_data: Dictionary mapping model names to their specific options or data, or None.
        default_options: Dictionary of default execution options, or None.

    Returns:
        A dictionary representation of the configuration.
    """
    config = CONFIG_TEMPLATE.copy()
    config["models"] = []

    for model_name in models:
        # Start with default options
        merged_options = default_options.copy() if default_options else {}

        # Merge specific overrides from models_data if present
        if models_data and model_name in models_data:
            model_spec = models_data[model_name]
            if isinstance(model_spec, dict):
                # Handle nested options key if present, otherwise treat as options directly
                overrides = model_spec.get("options", model_spec)
                if isinstance(overrides, dict):
                    merged_options.update(overrides)

        config["models"].append(
            {
                "name": model_name,
                "options": merged_options,
            }
        )

    return config


def create_config(
    models: list[str],
    models_data: dict | None,
    default_options: dict | None,
    output: str | Path,
) -> None:
    """Generate configuration and save it to the specified output file path.

    Args:
        models: List of model names.
        models_data: Dictionary mapping model names to overrides, or None.
        default_options: Dictionary of default options, or None.
        output: Path to the output configuration file.
    """
    config_dict = _generate_config(models, models_data, default_options)
    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = ROOT_DIR / output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_dict, f, sort_keys=False)
