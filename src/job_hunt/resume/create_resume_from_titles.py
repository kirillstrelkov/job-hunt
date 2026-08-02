"""Create tailored Resume documents and PDFs from section headers/titles."""

from pathlib import Path

from loguru import logger

from job_hunt.resume.md2pdf import convert_md_to_pdf
from job_hunt.resume.prepare_resume import prepare_resume
from job_hunt.resume.process_resume import fix_file

_TOOLS_DIR = Path(__file__).parent

_MARKER_START = "## Work Experience"
_MARKER_END = "### Tailoring Justification Report"


def extract_body(md_path: Path) -> str:
    """Extract work experience and projects sections from a Resume markdown file."""
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


def process_one(folder: Path, resume_md: Path) -> None:
    """Create a tailored body, prepare Resume, apply fixes, and compile to PDF for a single file."""
    name = resume_md.stem.removesuffix("_resume")
    job_folder = folder / name
    job_folder.mkdir(exist_ok=True)

    body_md = job_folder / "body.md"
    body_md.write_text(extract_body(resume_md))
    logger.info(f"Written body: {body_md}")

    logger.debug("Preparing resume in {} with {}", job_folder, body_md)
    prepare_resume(folder=str(job_folder), body=str(body_md))

    keep_thesis = any(kw in name.lower() for kw in ("test", "sdet"))
    gen_resume = job_folder / "gen/resume.md"
    fix_file(str(gen_resume), keep_thesis=keep_thesis)

    gen_pdf = job_folder / "gen/resumeStrelkov.pdf"
    convert_md_to_pdf(gen_resume, gen_pdf)
    logger.info(f"PDF: {gen_pdf}")


def main(folder: Path) -> None:
    """Build Resume PDFs from *_resume.md files in a folder."""
    resume_files = sorted(folder.glob("*_resume.md"))
    if not resume_files:
        logger.error(f"No *_resume.md files found in {folder}")
        return
    logger.info(f"Found {len(resume_files)} file(s)")
    for resume_md in resume_files:
        logger.info(f"Processing: {resume_md.name}")
        process_one(folder, resume_md)
