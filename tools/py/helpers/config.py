"""Configuration helper utilities for resolving paths and substitutions."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parent


@dataclass
class InputJob:
    """Represents a job configuration with ground truth and description paths."""

    name: str
    ground_truth_path: Path
    description_path: Path
    llm_prompt_path: Path


def _resolve_val(val: Any, context: dict[str, str]) -> tuple[Any, bool]:  # noqa: ANN401
    """Recursively resolve values using context, returning (new_val, has_changed)."""
    if isinstance(val, str):
        try:
            resolved = val.format(**context)
            if resolved != val:
                return resolved, True
        except (KeyError, ValueError, IndexError):
            pass
        return val, False
    if isinstance(val, dict):
        has_changed = False
        new_dict = {}
        for k, v in val.items():
            new_v, changed = _resolve_val(v, context)
            new_dict[k] = new_v
            if changed:
                has_changed = True
        return new_dict, has_changed
    if isinstance(val, list):
        has_changed = False
        new_list = []
        for item in val:
            new_item, changed = _resolve_val(item, context)
            new_list.append(new_item)
            if changed:
                has_changed = True
        return new_list, has_changed
    return val, False


def _resolve_dict_substitutions(config: dict) -> dict:
    """Recursively resolve {key} placeholders in config values using config keys as context."""
    for _ in range(5):
        # Gather current string values as context
        context = {k: str(v) for k, v in config.items() if isinstance(v, (str, int, float, bool))}

        config, has_changed = _resolve_val(config, context)
        if not has_changed:
            break

    return config


def _make_paths_absolute(val: Any) -> Any:  # noqa: ANN401
    """Recursively convert strings starting with ./ or ../ to absolute paths resolved relative to CONFIG_DIR."""
    if isinstance(val, str):
        if val.startswith(("./", "../")) or val in {".", ".."}:
            return str((CONFIG_DIR / val).resolve())
        return val
    if isinstance(val, dict):
        return {k: _make_paths_absolute(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_make_paths_absolute(item) for item in val]
    return val


class ConfigManager:
    """Manages reading and querying YAML configurations."""

    def __init__(self, config_path: Path) -> None:
        """Initialize ConfigManager with path to YAML config."""
        self.config_path = Path(config_path)
        self._config = None

    def get_path(self) -> Path:
        """Get the absolute path of the configuration file."""
        return self.config_path.resolve()

    def get_root_path(self) -> Path:
        """Get the resolved root directory path."""
        root_dir = Path(self.get_config_value(".root_dir"))
        if not root_dir.is_absolute():
            root_dir = (self.config_path.parent / root_dir).resolve()
        return root_dir

    def get_config_value_as_path(self, query: str) -> Path:
        """Get a configuration value as an absolute resolved Path."""
        path_val = Path(self.get_config_value(query))
        if not path_val.is_absolute():
            path_val = self.get_root_path() / path_val
        return path_val.resolve()

    def get_tmp_root_output_dir(self) -> Path:
        """Get the resolved absolute temporary output directory path."""
        return self.get_config_value_as_path(".tmp_output_dir")

    def get_jobs(self) -> list[InputJob]:
        """Get all configured jobs as a list of InputJob objects."""
        jobs_list = self.get_config_value(".jobs")
        return [
            InputJob(
                name=job["name"],
                ground_truth_path=Path(job["ground_truth"]),
                description_path=Path(job["description"]),
                llm_prompt_path=Path(job["llm_prompt"]),
            )
            for job in jobs_list
        ]

    def get_config(self) -> dict:
        """Read configuration from YAML, merging default options into models."""
        if self._config is None:
            if not self.config_path.exists():
                msg = f"Configuration file not found at '{self.config_path}'"
                raise FileNotFoundError(msg)
            with self.config_path.open(encoding="utf-8") as f:
                raw_config = yaml.safe_load(f) or {}

            raw_config = _make_paths_absolute(raw_config)
            raw_config = _resolve_dict_substitutions(raw_config)
            raw_config = _make_paths_absolute(raw_config)

            # Merge model_default_options into models list options
            defaults = raw_config.get("model_default_options", {})
            models = raw_config.get("models", [])
            for model in models:
                opts = model.get("options", {})
                merged = defaults.copy()
                if opts:
                    merged.update(opts)
                model["options"] = merged

            self._config = raw_config
        return self._config

    def get_config_value(self, query: str) -> Any:  # noqa: ANN401
        """Get a value from config using a yq-like query path (e.g. '.models[0].name').

        Raises ValueError if the value is not found or query is invalid.
        """
        if not query.startswith("."):
            msg = f"Query '{query}' must start with '.'"
            raise ValueError(msg)

        config = self.get_config()
        path = query[1:]
        if not path:
            return config

        pattern = re.compile(r"([^.\[\]]+)|\[(\d+)\]")
        current = config

        for match in pattern.finditer(path):
            key, index = match.groups()
            if key is not None:
                if not isinstance(current, dict) or key not in current:
                    msg = f"Path '{query}' not found (missing key '{key}')"
                    raise ValueError(msg)
                current = current[key]
            elif index is not None:
                idx = int(index)
                if not isinstance(current, list) or idx < 0 or idx >= len(current):
                    msg = f"Path '{query}' not found (index '{idx}' out of bounds)"
                    raise ValueError(msg)
                current = current[idx]

        return current


DEFAULT_CONFIG = ConfigManager(CONFIG_DIR / "config.yaml")
TRULENS_DB_URL = DEFAULT_CONFIG.get_config_value(".trulens_db_url")
