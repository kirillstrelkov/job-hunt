import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

CONFIG_DIR = Path(__file__).resolve().parent


def get_default_config_path() -> Path:
    """Get the default config path, prioritizing JOB_HUNT_CONFIG env var if set."""
    env_path = os.getenv("JOB_HUNT_CONFIG")
    if env_path:
        return Path(env_path).resolve()
    return CONFIG_DIR / "config.yaml"


@dataclass
class Config:
    """Dataclass holding resolved Resume file paths."""

    header: Path
    body: Path
    footer: Path
    prompt: Path


@dataclass
class InputJob:
    """Represents a job configuration with ground truth and description paths."""

    name: str
    ground_truth_path: Path
    description_path: Path
    llm_prompt_path: Path


@dataclass
class ComposerConfig:
    """Configuration for Resume Composer inputs."""

    header: Path
    body: Path
    footer: Path


@dataclass
class TailorConfig:
    """Configuration for body tailoring prompt."""

    prompt: Path


@dataclass
class ModelConfig:
    """Configuration options for a specific LLM model."""

    name: str
    options: dict[str, Any] = None


@dataclass
class LLMOllamaConfig:
    """List of configured Ollama models."""

    models: list[ModelConfig]


@dataclass
class LLMGeminiConfig:
    """List of configured Gemini models."""

    models: list[ModelConfig]


@dataclass
class LLMConfig:
    """Root configuration options for LLMs."""

    eval_model: str
    fix_model: str
    embeddings_model: str
    model_default_options: dict[str, Any]
    top_models: list[str]
    ollama: LLMOllamaConfig
    gemini: LLMGeminiConfig


@dataclass
class PathsConfig:
    """Paths config section."""

    root_dir: Path
    tmp_output_dir: Path
    tmp_input_dir: Path
    trulens_db_url: str
    prepare_llm_prompt_script: Path
    env_file: Path


@dataclass
class DataConfig:
    """Data input config section (e.g. jobs list)."""

    jobs: list[InputJob]


@dataclass
class ScraperConfig:
    """Scraper configuration for excluded companies and keywords."""

    jobs_path: Path
    job_matches_path: Path
    excluded_companies: list[str]
    excluded_title_keywords: list[str]
    urls: list[str]


def _resolve_val(val: Any, context: dict[str, str]) -> tuple[Any, bool]:
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


def _make_paths_absolute(val: Any) -> Any:
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

    def __init__(self, config_path: Path | str | None = None) -> None:
        """Initialize ConfigManager with path to YAML config."""
        self.config_path = Path(config_path) if config_path is not None else get_default_config_path()
        self._config = None
        self.composer: ComposerConfig = None
        self.tailor: TailorConfig = None
        self.llm: LLMConfig = None
        self.paths: PathsConfig = None
        self.data: DataConfig = None
        self.scraper: ScraperConfig = None
        if self.config_path.exists():
            self.load()

    def get_path(self) -> Path:
        """Get the absolute path of the configuration file."""
        return self.config_path.resolve()

    def get_root_path(self) -> Path:
        """Get the resolved root directory path."""
        root_dir = self.paths.root_dir
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
        path_val = self.paths.tmp_output_dir
        if not path_val.is_absolute():
            path_val = self.get_root_path() / path_val
        return path_val.resolve()

    def get_jobs(self) -> list[InputJob]:
        """Get all configured jobs as a list of InputJob objects."""
        return self.data.jobs

    def get_config(self) -> dict:
        """Read configuration from YAML, merging default options into models."""
        if self._config is None:
            if not self.config_path.exists():
                msg = f"Configuration file not found at '{self.config_path}'"
                raise FileNotFoundError(msg)
            with self.config_path.open(encoding="utf-8") as f:
                raw_config = yaml.safe_load(f) or {}

            # Map the new structured config layout to the legacy top-level keys for backward-compatibility
            # Flatten paths configuration
            paths = raw_config.get("paths", {})
            if paths:
                for k, v in paths.items():
                    raw_config[k] = v

            # Flatten llm configuration
            llm = raw_config.get("llm", {})
            if llm:
                raw_config["eval_model"] = llm.get("eval_model")
                raw_config["fix_model"] = llm.get("fix_model")
                raw_config["embeddings_model"] = llm.get("embeddings_model")
                raw_config["model_default_options"] = llm.get("model_default_options")
                raw_config["top_models"] = llm.get("top_models")

                ollama_models = llm.get("ollama", {}).get("models", [])
                gemini_models = llm.get("gemini", {}).get("models", [])

                raw_config["models"] = ollama_models + gemini_models
                raw_config["gemini_models"] = [m["name"] for m in gemini_models]

            # Flatten data configuration
            data_sec = raw_config.get("data", {})
            if data_sec and "jobs" in data_sec:
                raw_config["jobs"] = data_sec["jobs"]

            raw_config = _make_paths_absolute(raw_config)
            raw_config = _resolve_dict_substitutions(raw_config)
            raw_config = _make_paths_absolute(raw_config)

            self._config = raw_config
            self.load()
        return self._config

    def load(self) -> None:
        """Load YAML configuration and parse into structured dataclass fields."""
        if self._config is None:
            self.get_config()

        config = self._config

        # Parse composer
        comp = config.get("composer", {})
        self.composer = ComposerConfig(
            header=Path(comp.get("header", "")),
            body=Path(comp.get("body", "")),
            footer=Path(comp.get("footer", "")),
        )

        # Parse tailor
        tail = config.get("tailor", {})
        self.tailor = TailorConfig(
            prompt=Path(tail.get("prompt", "")),
        )

        # Parse paths
        pts = config.get("paths", {})
        self.paths = PathsConfig(
            root_dir=Path(pts.get("root_dir", "")),
            tmp_output_dir=Path(pts.get("tmp_output_dir", "")),
            tmp_input_dir=Path(pts.get("tmp_input_dir", "")),
            trulens_db_url=str(pts.get("trulens_db_url", "")),
            prepare_llm_prompt_script=Path(pts.get("prepare_llm_prompt_script", "")),
            env_file=Path(pts.get("env_file", "")),
        )

        # Parse llm
        ll = config.get("llm", {})
        ollama_data = ll.get("ollama", {})
        ollama_models = [ModelConfig(name=m["name"], options=m.get("options")) for m in ollama_data.get("models", [])]
        gemini_data = ll.get("gemini", {})
        gemini_models = [ModelConfig(name=m["name"], options=m.get("options")) for m in gemini_data.get("models", [])]

        self.llm = LLMConfig(
            eval_model=str(ll.get("eval_model", "")),
            fix_model=str(ll.get("fix_model", "")),
            embeddings_model=str(ll.get("embeddings_model", "qwen3-embedding:0.6b")),
            model_default_options=dict(ll.get("model_default_options", {})),
            top_models=list(ll.get("top_models", [])),
            ollama=LLMOllamaConfig(models=ollama_models),
            gemini=LLMGeminiConfig(models=gemini_models),
        )

        # Parse data
        dt = config.get("data", {})
        self.data = DataConfig(
            jobs=[
                InputJob(
                    name=job["name"],
                    ground_truth_path=Path(job["ground_truth"]),
                    description_path=Path(job["description"]),
                    llm_prompt_path=Path(job["llm_prompt"]),
                )
                for job in dt.get("jobs", [])
            ]
        )

        # Parse scraper
        scr = config.get("scraper", {})
        self.scraper = ScraperConfig(
            jobs_path=Path(scr.get("jobs_path", "")),
            job_matches_path=Path(scr.get("job_matches_path", "")),
            excluded_companies=list(scr.get("excluded_companies", [])),
            excluded_title_keywords=list(scr.get("excluded_title_keywords", [])),
            urls=list(scr.get("urls", [])),
        )

    def get_config_value(self, query: str) -> Any:
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

    def get_env_file(self) -> Path:
        """Get the path to the environment variable file (.env) from the configuration."""
        return self.paths.env_file


def load(config_path: str | Path) -> dict:
    """Load config from YAML file and resolve paths to absolute paths."""
    cm = ConfigManager(Path(config_path))
    return cm.get_config()


def create_default_config(dest_path: Path) -> None:
    """Create a default configuration file if it does not exist."""
    if dest_path.exists():
        logger.warning(f"Config file already exists at {dest_path}")
        return

    # Ensure parent directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    default_data = {
        "composer": {
            "header": "../resume/example/header.md",
            "body": "../resume/example/body.md",
            "footer": "../resume/example/footer.md",
        },
        "tailor": {
            "prompt": "../resume/prompts/tailor_for_description.md",
        },
    }

    try:
        with dest_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(default_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Created configuration file at {dest_path}")
    except Exception as e:
        logger.error(f"Failed to create config file at {dest_path}: {e}")
        raise


def check_config(config_path: Path) -> bool:
    """Check that all paths referenced in the config file exist."""
    if not config_path.exists():
        logger.error(f"Config file not found at {config_path}")
        return False

    try:
        resolved = load(config_path)
    except (TypeError, ValueError, yaml.YAMLError, OSError) as e:
        logger.error(f"Error loading configuration: {e}")
        return False

    all_exist = True

    def check(label: str, value: Any) -> None:
        nonlocal all_exist
        if not value:
            return
        path_obj = Path(value)
        if path_obj.exists():
            logger.info(f"Path exists: {label} -> {path_obj}")
        else:
            logger.warning(f"Path missing: {label} -> {path_obj}")
            all_exist = False

    for key, val in resolved.get("composer", {}).items():
        check(f"composer.{key}", val)

    for key, val in resolved.get("tailor", {}).items():
        check(f"tailor.{key}", val)

    for key, val in resolved.get("paths", {}).items():
        if key == "trulens_db_url":  # not a plain filesystem path (sqlite:/// URL)
            continue
        check(f"paths.{key}", val)

    for job in resolved.get("data", {}).get("jobs", []):
        name = job.get("name", "?")
        for key in ("ground_truth", "description", "llm_prompt"):
            if key in job:
                check(f"data.jobs[{name}].{key}", job[key])

    for key in ("jobs_path", "job_matches_path"):
        if key in resolved.get("scraper", {}):
            check(f"scraper.{key}", resolved["scraper"][key])

    return all_exist


DEFAULT_CONFIG = ConfigManager(get_default_config_path())
TRULENS_DB_URL = DEFAULT_CONFIG.get_config_value(".trulens_db_url")
