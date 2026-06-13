"""Input/Output helpers for managing temporary directories."""

import os
from pathlib import Path

from helpers.config import _DEFAULT_CONFIG

HELPERS_DIR = Path(__file__).resolve().parent
CONFIG_PATH = HELPERS_DIR / "config.yaml"


def _get_absolute_tmp_output_dir() -> Path:
    """Load tmp_output_dir from config.yaml and resolve it relative to config.yaml's directory."""
    tmp_output_dir = _DEFAULT_CONFIG.get_config_value(".tmp_output_dir")
    return (HELPERS_DIR / tmp_output_dir).resolve()


def get_tmp_folder(file_path: str | Path) -> Path:
    """Get the tmp folder path for a given file_path.

    Constructed using tmp_output_dir from tools/py/helpers/config.yaml.
    The path is mapped relative to the common parent path with config.yaml.
    """
    abs_file_path = Path(file_path).resolve()
    abs_config_path = CONFIG_PATH.resolve()

    # Find common ancestor path of the parent directories
    common = Path(os.path.commonpath([abs_config_path.parent, abs_file_path.parent]))

    # Calculate the remaining relative path of the file without extension
    rel_path = abs_file_path.with_suffix("").relative_to(common)

    # Combine the resolved absolute tmp_output_dir with the relative path
    tmp_base = _get_absolute_tmp_output_dir()
    return tmp_base / rel_path


def get_tmp_input_folder(file_path: str | Path) -> Path:
    """Get the input tmp folder path using get_tmp_folder."""
    return get_tmp_folder(file_path) / "input"


def get_tmp_output_folder(file_path: str | Path) -> Path:
    """Get the output tmp folder path using get_tmp_folder."""
    return get_tmp_folder(file_path) / "output"
