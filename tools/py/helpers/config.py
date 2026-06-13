"""Configuration management helper."""

import re
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parent


def _resolve_dict_substitutions(config: dict) -> dict:
    """Recursively resolve {key} placeholders in config values using config keys as context."""
    for _ in range(5):
        # Gather current string values as context
        context = {}
        for k, v in config.items():
            if isinstance(v, (str, int, float, bool)):
                context[k] = str(v)

        has_changed = False

        def resolve_val(val: Any) -> Any:  # noqa: ANN401
            nonlocal has_changed
            if isinstance(val, str):
                try:
                    resolved = val.format(**context)
                    if resolved != val:
                        has_changed = True
                        return resolved
                except (KeyError, ValueError, IndexError):
                    pass
            elif isinstance(val, dict):
                return {k: resolve_val(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [resolve_val(item) for item in val]
            return val

        config = {k: resolve_val(v) for k, v in config.items()}
        if not has_changed:
            break

    return config


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

    def get_tmp_root_output_dir(self) -> Path:
        """Get the resolved absolute temporary output directory path."""
        tmp_output_dir = Path(self.get_config_value(".tmp_output_dir"))
        if not tmp_output_dir.is_absolute():
            tmp_output_dir = self.get_root_path() / tmp_output_dir
        return tmp_output_dir.resolve()

    def get_config(self) -> dict:
        """Read configuration from YAML, merging default options into models."""
        if self._config is None:
            if not self.config_path.exists():
                msg = f"Configuration file not found at '{self.config_path}'"
                raise FileNotFoundError(msg)
            with self.config_path.open(encoding="utf-8") as f:
                raw_config = yaml.safe_load(f) or {}

            raw_config = _resolve_dict_substitutions(raw_config)

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

LLM_PROMPT_OUTPUT_FILE = DEFAULT_CONFIG.get_config_value(".llm_prompt_output_file")
TRULENS_DB_URL = DEFAULT_CONFIG.get_config_value(".trulens_db_url")
