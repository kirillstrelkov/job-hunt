"""Convert Markdown to PDF using Pandoc."""

import subprocess
import sys
from pathlib import Path

from loguru import logger

from job_hunt.core.binary_helper import get_pandoc


def convert_md_to_pdf(input_path: Path, output_path: Path) -> None:
    """Convert input markdown path to output PDF path using Pandoc."""
    logger.info(f"Converting {input_path} to {output_path}...")
    try:
        subprocess.run(  # noqa: S603
            [
                get_pandoc(),
                "-V",
                "papersize=a4",
                "-V",
                "geometry:left=1.5cm",
                "-V",
                "geometry:right=1.5cm",
                "-V",
                "geometry:top=1.2cm",
                "-V",
                "geometry:bottom=1.2cm",
                str(input_path),
                "-o",
                str(output_path),
            ],
            check=True,
        )
        logger.info(f"Successfully generated PDF: {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Pandoc failed: {e}")
        sys.exit(e.returncode)
