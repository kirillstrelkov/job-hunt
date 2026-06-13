import re
from pathlib import Path

import yaml

# ROOT_DIR points to tailor_cv_eval to maintain compatibility for all output and input paths
ROOT_DIR = Path(__file__).resolve().parents[1] / "tailor_cv_eval"
CONFIG_DIR = Path(__file__).resolve().parent


class ConfigManager:
    """Manages reading and querying YAML configurations."""

    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)
        self._config = None

    def get_config(self) -> dict:
        if self._config is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found at '{self.config_path}'")
            with open(self.config_path, encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        return self._config

    def get_config_value(self, query: str):
        """Get a value from config using a yq-like query path (e.g. '.models[0].name').

        Raises ValueError if the value is not found or query is invalid.
        """
        if not query.startswith("."):
            raise ValueError(f"Query '{query}' must start with '.'")

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
                    raise ValueError(f"Path '{query}' not found (missing key '{key}')")
                current = current[key]
            elif index is not None:
                idx = int(index)
                if not isinstance(current, list) or idx < 0 or idx >= len(current):
                    raise ValueError(f"Path '{query}' not found (index '{idx}' out of bounds)")
                current = current[idx]

        return current


_DEFAULT_CONFIG = ConfigManager(CONFIG_DIR / "config.yaml")


TMP_OUTPUT_DIR = Path(_DEFAULT_CONFIG.get_config_value(".tmp_output_dir"))
if not TMP_OUTPUT_DIR.is_absolute():
    TMP_OUTPUT_DIR = ROOT_DIR / TMP_OUTPUT_DIR

LLM_PROMPT_OUTPUT_FILE = _DEFAULT_CONFIG.get_config_value(".llm_prompt_output_file")
TRULENS_DB_URL = _DEFAULT_CONFIG.get_config_value(".trulens_db_url")
