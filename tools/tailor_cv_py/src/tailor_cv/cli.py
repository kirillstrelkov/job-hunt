import sys
from pathlib import Path

import typer
from loguru import logger

from tailor_cv.llm import DEFAULT_MODEL, call_ollama
from tailor_cv.llm_gemini import DEFAULT_GEMINI_MODEL, call_gemini
from tailor_cv.pdf import convert_to_pdf
from tailor_cv.prompt import (
    COVER_LETTER_SYSTEM_PROMPT,
    DEFAULT_FOOTER,
    DEFAULT_HEADER,
    SYSTEM_PROMPT,
    build_cover_letter_message,
    build_user_message,
)
from tailor_cv.reader import read_file
from tailor_cv.text import to_plain_text

app = typer.Typer(add_completion=False)


@app.command()
def main(
    input_cv: Path = typer.Option(..., "-i", "--input", help="Path to master CV plain text file"),
    job_desc: Path = typer.Option(
        ..., "-j", "--job", help="Path to job description plain text file"
    ),
    output: Path = typer.Option(..., "-o", "--output", help="Path to output file (.md or .pdf)"),
    log_level: str = typer.Option("INFO", "-l", "--log-level", help="Log level"),
    model: str = typer.Option(None, "-m", "--model", help="Model name — prefix with 'gemini' to use Gemini API (requires GEMINI_API_KEY), otherwise uses local Ollama"),
    cover_letter: bool = typer.Option(False, "--cov", help="Also generate a cover letter"),
    header: Path = typer.Option(
        None, "--header", help="Path to header .md file (default placeholder used if omitted)"
    ),
    footer: Path = typer.Option(
        None, "--footer", help="Path to footer .md file (default placeholder used if omitted)"
    ),
) -> None:
    logger.remove()
    logger.add(sys.stderr, level=log_level.upper())

    if output.suffix not in {".md", ".pdf"}:
        raise typer.BadParameter(
            f"Output file must be .md or .pdf, got '{output.suffix}'", param_hint="'-o'"
        )

    logger.info(f"Reading master CV from {input_cv}")
    master_cv = read_file(str(input_cv))

    logger.info(f"Reading job description from {job_desc}")
    job_description = to_plain_text(read_file(str(job_desc)))

    def _call(system: str, user_message: str) -> str:
        resolved = model or DEFAULT_MODEL
        if resolved.startswith("gemini"):
            return call_gemini(system=system, user_message=user_message, model=resolved)
        return call_ollama(system=system, user_message=user_message, model=resolved)

    user_message = build_user_message(master_cv=master_cv, job_description=job_description)
    logger.debug("Messages built, sending to LLM")

    tailored_cv = _call(system=SYSTEM_PROMPT, user_message=user_message)

    header_text = read_file(str(header) if header else str(DEFAULT_HEADER))
    footer_text = read_file(str(footer) if footer else str(DEFAULT_FOOTER))
    full_cv = f"{header_text.rstrip()}\n\n{tailored_cv.strip()}\n\n{footer_text.strip()}\n"

    md_path = output.with_suffix(".md")
    md_path.write_text(full_cv, encoding="utf-8")
    logger.success(f"Tailored CV Markdown written to {md_path}")

    if output.suffix == ".pdf":
        convert_to_pdf(str(md_path), str(output))
        logger.success(f"Tailored CV PDF written to {output}")

    if cover_letter:
        logger.info("Generating cover letter")
        cover_message = build_cover_letter_message(
            master_cv=master_cv, job_description=job_description
        )
        cover_text = _call(system=COVER_LETTER_SYSTEM_PROMPT, user_message=cover_message)

        cover_md = output.with_name(output.stem + "_cover.md")
        cover_md.write_text(cover_text, encoding="utf-8")
        logger.success(f"Cover letter Markdown written to {cover_md}")

        if output.suffix == ".pdf":
            cover_pdf = output.with_name(output.stem + "_cover.pdf")
            convert_to_pdf(str(cover_md), str(cover_pdf))
            logger.success(f"Cover letter PDF written to {cover_pdf}")
