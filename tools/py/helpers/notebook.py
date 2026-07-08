"""Helper functions for Jupyter Notebook operations."""

import subprocess
import sys
from pathlib import Path

from loguru import logger


def run_jupyter_notebook(notebook_path: Path) -> None:
    """Execute all cells in the Jupyter notebook in-place."""
    logger.info(f"Executing Jupyter notebook: {notebook_path.name}...")
    if not notebook_path.exists():
        logger.error(f"Jupyter notebook not found at: {notebook_path}")
        sys.exit(1)

    res = subprocess.run(  # noqa: S603
        [
            "uv",
            "run",
            "--with",
            "nbconvert",
            "--with",
            "ipykernel",
            "--with",
            "pandas",
            "--with",
            "matplotlib",
            "--with",
            "seaborn",
            "python",
            "-m",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--inplace",
            str(notebook_path),
        ],
        check=False,
    )

    if res.returncode != 0:
        logger.error(f"Error executing Jupyter notebook: exit code {res.returncode}")
        sys.exit(res.returncode)

    logger.info("Jupyter notebook executed successfully.")
