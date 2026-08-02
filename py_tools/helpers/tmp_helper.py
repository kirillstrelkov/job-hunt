"""Input/Output helpers for managing temporary directories."""

import os
from pathlib import Path

from config.config import DEFAULT_CONFIG, InputJob


def get_root_dir() -> Path:
    """Get the root directory of the project."""
    return DEFAULT_CONFIG.get_root_path()


def get_tmp_output_dir() -> Path:
    """Load tmp_output_dir from config.yaml and resolve it relative to the root directory."""
    return DEFAULT_CONFIG.get_tmp_root_output_dir()


def get_tmp_folder(file_path: str | Path) -> Path:
    """Get the tmp folder path for a given file_path.

    Constructed using tmp_output_dir from tools/py/helpers/config.yaml.
    The path is mapped relative to the common parent path with get_tmp_output_dir().
    """
    abs_file_path = Path(file_path).resolve()
    tmp_base = get_tmp_output_dir()

    # Find common ancestor path of tmp_base and the file's parent directory
    common = Path(os.path.commonpath([tmp_base, abs_file_path.parent]))

    # Calculate the remaining relative path of the file without extension
    rel_path = abs_file_path.with_suffix("").relative_to(common)

    result_path = tmp_base / rel_path
    result_path.mkdir(parents=True, exist_ok=True)
    return result_path


def get_tmp_input_folder(file_path: str | Path) -> Path:
    """Get the input tmp folder path using get_tmp_folder."""
    return get_tmp_folder(file_path) / "input"


def get_tmp_output_folder(file_path: str | Path) -> Path:
    """Get the output tmp folder path using get_tmp_folder."""
    return get_tmp_folder(file_path) / "output"


def get_llm_prompt_for_job(job: InputJob) -> Path:
    """Get the llm prompt for a given job."""
    return job.llm_prompt_path
