#!/usr/bin/env python3
"""Module to manage and validate the CV configuration files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from loguru import logger


def load(config_path: str | Path) -> dict[str, str]:
    """Load config from YAML file and resolve paths to absolute paths.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        A dictionary mapping keys to their absolute file paths.

    """
    config_path = Path(config_path).resolve()
    logger.info(f"Loading configuration from {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        logger.error(f"Failed to read config file {config_path}: {e}")
        raise

    if not isinstance(data, dict):
        msg = f"Configuration at {config_path} is not a valid YAML dictionary"
        logger.error(msg)
        raise TypeError(msg)

    resolved: dict[str, str] = {}
    config_dir = config_path.parent

    for key, val in data.items():
        if val is None:
            resolved[key] = ""
            continue
        val_str = str(val)
        val_path = Path(val_str)
        resolved_path = (config_dir / val_path).resolve() if not val_path.is_absolute() else val_path.resolve()
        resolved[key] = str(resolved_path)

    return resolved


def create_default_config(dest_path: Path) -> None:
    """Create a default configuration file if it does not exist.

    Args:
        dest_path: Destination path for the config file.

    """
    if dest_path.exists():
        logger.warning(f"Config file already exists at {dest_path}")
        return

    # Ensure parent directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    default_data = {
        "header": "../example/header.md",
        "body": "../example/body.md",
        "footer": "../example/footer.md",
        "prompt": "../prompts/tailor.md",
    }

    try:
        with dest_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(default_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Created configuration file at {dest_path}")
    except Exception as e:
        logger.error(f"Failed to create config file at {dest_path}: {e}")
        raise


def check_config(config_path: Path) -> bool:
    """Check that all files referenced in the config file exist.

    Args:
        config_path: Path to the config file.

    Returns:
        True if all files exist, False otherwise.

    """
    if not config_path.exists():
        logger.error(f"Config file not found at {config_path}")
        return False

    try:
        resolved_paths = load(config_path)
    except (TypeError, ValueError, yaml.YAMLError, OSError) as e:
        logger.error(f"Error loading configuration: {e}")
        return False

    all_exist = True
    for key, filepath in resolved_paths.items():
        path_obj = Path(filepath)
        if path_obj.exists() and path_obj.is_file():
            logger.info(f"File exists: {key} -> {filepath}")
        else:
            logger.warning(f"File missing: {key} -> {filepath}")
            all_exist = False

    return all_exist


def main() -> None:
    """Run the CLI application."""
    parser = argparse.ArgumentParser(description="Manage CV configuration files.")
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create cv/tmp/config.yml if it doesn't exist.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that all files in the configuration file exist.",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Path to the config file to check. Defaults to cv/tmp/config.yml.",
    )

    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    cv_dir = script_dir.parent
    default_config_path = cv_dir / "tmp" / "config.yml"

    # Handle create
    if args.create:
        create_default_config(default_config_path)
        return

    # Handle check
    if args.check:
        config_path = Path(args.path) if args.path else default_config_path
        success = check_config(config_path)
        if not success:
            sys.exit(1)
        return

    # If no options provided, print help
    parser.print_help()


if __name__ == "__main__":
    main()
