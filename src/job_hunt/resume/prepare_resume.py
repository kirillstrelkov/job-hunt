"""Assembles Resume parts (header, body, footer) and prepares LLM tailoring prompts."""

from pathlib import Path

from loguru import logger

from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.resume.combine_resume_parts import combine_resume_part_files


def generate_llm_prompt(
    *,
    template: Path,
    resume_body: Path,
    job_description: Path | str | None = None,
    job_title: str | None = None,
) -> str:
    """Fill an LLM tailoring prompt template with a resume body and a job description or job title."""
    jd_text = (
        job_description.read_text(encoding="utf-8") if isinstance(job_description, Path) else (job_description or "")
    )
    return template.read_text(encoding="utf-8").format(
        master_resume=resume_body.read_text(encoding="utf-8"),
        job_description=jd_text,
        job_title=job_title or "",
    )


def prepare_resume(  # noqa: C901
    *,
    folder: str | None = None,
    body: str | None = None,
    llm_prompt: bool = False,
    job_description: str | None = None,
) -> None:
    """Prepare the Resume files, either composing final markdown or creating an LLM tailoring prompt."""
    folder_path = Path(folder) if folder else None
    body_path = Path(body) if body else None

    if folder_path is None and body_path is None:
        msg = "Must specify at least a folder or a body path"
        raise ValueError(msg)

    if body_path is not None:
        if folder_path and not folder_path.is_dir():
            msg = f"folder must be a directory: {folder_path}"
            raise ValueError(msg)
        body_file = body_path
        target_folder = folder_path or body_path.parent
        generate_resume_mode = True
    else:
        # body_path is None, so folder_path must be not None
        body_file = folder_path / "body.md"
        target_folder = folder_path
        generate_resume_mode = not llm_prompt

    assert target_folder is not None

    if not target_folder.exists():
        msg = f"{target_folder} not found"
        raise FileNotFoundError(msg)

    # inputs
    header = DEFAULT_CONFIG.composer.header
    footer = DEFAULT_CONFIG.composer.footer
    master_resume = DEFAULT_CONFIG.composer.body
    tailor_for_desc = DEFAULT_CONFIG.tailor.prompt

    jd = Path(job_description) if job_description else target_folder / "jd.txt"

    paths_to_check = [
        header,
        footer,
        tailor_for_desc,
        master_resume,
    ]

    if generate_resume_mode:
        paths_to_check.append(body_file)

    if llm_prompt:
        paths_to_check.append(jd)

    for p in paths_to_check:
        if not p.exists():
            msg = f"{p} not found"
            raise FileNotFoundError(msg)

    # outputs
    out_folder = target_folder / "gen"
    if not out_folder.exists():
        out_folder.mkdir(exist_ok=False)

    tailored_llm_text = out_folder / "llm_prompt.txt"

    # generate
    if llm_prompt:
        logger.info(f"Generating {tailored_llm_text}")

        content = generate_llm_prompt(template=tailor_for_desc, resume_body=master_resume, job_description=jd)
        tailored_llm_text.write_text(content)

    if generate_resume_mode:
        resume_out = out_folder / f"{body_file.stem.replace('body', 'resume')}.md"
        logger.info(f"Generating {resume_out}")

        resume_out.write_text(combine_resume_part_files(header, body_file, footer))
