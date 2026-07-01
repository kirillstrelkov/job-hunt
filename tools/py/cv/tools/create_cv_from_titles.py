"""Create tailored CV documents and PDFs from section headers/titles."""

import argparse
import subprocess
import sys
from pathlib import Path

from loguru import logger

_TOOLS_DIR = Path(__file__).parent


from prepare_cv import prepare_cv  # noqa: E402
from process_cv import fix_file  # noqa: E402

_MARKER_START = "## Work Experience"
_MARKER_END = "### Tailoring Justification Report"


def extract_body(md_path: Path) -> str:
    """Extract work experience and projects sections from a CV markdown file."""
    lines = md_path.read_text().splitlines(keepends=True)

    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if start_idx is None and line.startswith(_MARKER_START):
            start_idx = i
        elif start_idx is not None and line.startswith(_MARKER_END):
            end_idx = i
            break

    if start_idx is None:
        return "".join(lines)

    return "".join(lines[start_idx:end_idx])


def process_one(folder: Path, cv_md: Path) -> None:
    """Create a tailored body, prepare CV, apply fixes, and compile to PDF for a single file."""
    name = cv_md.stem.removesuffix("_cv")
    job_folder = folder / name
    job_folder.mkdir(exist_ok=True)

    body_md = job_folder / "body.md"
    body_md.write_text(extract_body(cv_md))
    logger.info(f"Written body: {body_md}")

    logger.debug("Preparing cv in {} with {}", job_folder, body_md)
    prepare_cv(folder=str(job_folder), body=str(body_md))

    keep_thesis = any(kw in name.lower() for kw in ("test", "sdet"))
    gen_cv = job_folder / "gen/cv.md"
    fix_file(str(gen_cv), keep_thesis=keep_thesis)

    gen_pdf = job_folder / "gen/cvStrelkov.pdf"
    subprocess.run(  # noqa: S603
        [
            "pandoc",
            "-V",
            "papersize=a4",
            "-V",
            "geometry:margin=1.5cm",
            str(gen_cv),
            "-o",
            str(gen_pdf),
        ],
        check=True,
    )
    logger.info(f"PDF: {gen_pdf}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build CV PDFs from *_cv.md files.")
    parser.add_argument("--folder", required=True, help="Folder containing *_cv.md files")
    args = parser.parse_args()

    folder = Path(args.folder)
    cv_files = sorted(folder.glob("*_cv.md"))

    if not cv_files:
        logger.error(f"No *_cv.md files found in {folder}")
        sys.exit(1)

    logger.info(f"Found {len(cv_files)} file(s)")

    for cv_md in cv_files:
        logger.info(f"Processing: {cv_md.name}")
        process_one(folder, cv_md)
