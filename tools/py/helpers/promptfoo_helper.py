"""Helper functions for Promptfoo integration and evaluation execution."""

import subprocess
import sys
from pathlib import Path

import yaml
from loguru import logger


def write_yaml_config(config: dict, output_file: Path) -> None:
    """Write Promptfoo configuration dict to a YAML file, using block style for multiline strings."""
    # Setup PyYAML to dump multiline strings using block scalar style (|)
    yaml.SafeDumper.add_representer(
        str,
        lambda dumper, data: (
            dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            if "\n" in data
            else dumper.represent_scalar("tag:yaml.org,2002:str", data)
        ),
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, default_flow_style=False)


def run_promptfoo_eval(config_file: Path, results_json_path: Path | None = None) -> None:
    """Execute Promptfoo eval command line tool via subprocess."""
    logger.info("Executing Promptfoo evaluation...")
    cmd = [
        "npx",
        "-y",
        "promptfoo@latest",
        "eval",
        "-c",
        str(config_file),
        "--no-cache",
        "-j",
        "1",
    ]
    if results_json_path:
        cmd.extend(["-o", str(results_json_path)])

    res = subprocess.run(cmd, check=False)  # noqa: S603

    if res.returncode not in [0, 100]:
        logger.error(f"Error running Promptfoo: exit code {res.returncode}")
        sys.exit(res.returncode)
