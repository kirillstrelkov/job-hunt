#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path
from loguru import logger


def convert_md_to_pdf(input_path: Path, output_path: Path) -> None:
    logger.info(f"Converting {input_path} to {output_path}...")
    try:
        subprocess.run(
            [
                "pandoc",
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF using Pandoc.")
    parser.add_argument(
        "input",
        help="Path to the input Markdown file",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Path to the output PDF file (defaults to input file with .pdf extension)",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".pdf")

    convert_md_to_pdf(input_path, output_path)


if __name__ == "__main__":
    main()
