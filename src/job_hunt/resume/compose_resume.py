"""Local Resume composer that coordinates prompt generation, LLM tailoring, and PDF conversion."""

import sys
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field

from job_hunt.core.llm import run_model
from job_hunt.resume.check_pdf import check_pdf
from job_hunt.resume.feedback_loop import fix_with_feedback
from job_hunt.resume.md2pdf import convert_md_to_pdf
from job_hunt.resume.prepare_resume import prepare_resume
from job_hunt.resume.process_resume import check_markdown, fix_file
from job_hunt.resume.tailor_resume_body import get_eval_model, process_output_of_ollama, run_ollama


class ThesisDecision(BaseModel):
    """Pydantic model representing LLM decision about keeping or removing the thesis from the Resume."""

    keep_thesis: bool = Field(
        description=(
            "Whether to keep the thesis name in the Resume. This should be True if the job description "
            "is for a software test engineer / QA automation / SDET role, and False if it is for "
            "a developer / software engineer role."
        )
    )
    reason: str = Field(description="Short reason/justification for the decision.")


def decide_keep_thesis(jd_text: str) -> bool:
    """Run LLM with structured output to decide whether to keep the thesis in Resume."""
    model_name = get_eval_model()

    logger.info(f"Running LLM ({model_name}) to decide whether to keep the thesis based on job description...")
    result = run_model(
        model_name=model_name,
        output_type=ThesisDecision,
        user_prompt=f"Job Description:\n{jd_text}",
        system_prompt=(
            "Recruiter and Resume compiler. Analyze the job description and decide "
            "if it is for a software test engineer / QA / SDET (set keep_thesis to True) "
            "and not a software developer / engineer (set keep_thesis to False)."
        ),
    )
    decision: ThesisDecision = result.output
    logger.info(f"Thesis decision: keep_thesis={decision.keep_thesis} (Reason: {decision.reason})")
    return decision.keep_thesis


def compose_resume(
    folder: str | Path,
    model: str | None = None,
    force: bool = False,
    feedback: bool = False,
) -> None:
    """Compose Resume locally for a given folder using the specified Ollama model."""
    folder = Path(folder).resolve()
    if not folder.exists():
        logger.error(f"Folder or file {folder} not found")
        sys.exit(1)

    target_folder = folder.parent if folder.is_file() else folder

    if not target_folder.is_dir():
        logger.error(f"Resolved folder is not a directory: {target_folder}")
        sys.exit(1)

    logger.info(f"Step 1: Preparing LLM prompt for {target_folder}")
    prepare_resume(folder=str(target_folder), llm_prompt=True)

    prompt_file = target_folder / "gen" / "llm_prompt.txt"
    model_name = model or get_eval_model()

    if model:
        model_suffix = model.replace(":", "-")
        body_output = target_folder / f"body-{model_suffix}.md"
        assembled_resume = target_folder / "gen" / f"resume-{model_suffix}.md"
        pdf_output = target_folder / "gen" / f"resume-{model_suffix}.pdf"
    else:
        body_output = target_folder / "body.md"
        assembled_resume = target_folder / "gen" / "resume.md"
        pdf_output = target_folder / "gen" / "resume.pdf"

    if force or not body_output.exists():
        logger.info(f"Step 2: Tailoring Resume body with {model_name} model")
        prompt_content = prompt_file.read_text(encoding="utf-8")
        result = run_ollama(prompt_content, model_name)
        process_output_of_ollama(result, body_output)
    else:
        logger.warning(
            f"Step 2: Skipping LLM tailoring because {body_output.name} already exists. Use --force to re-generate."
        )

    logger.info("Step 3: Composing Resume from tailored body")
    prepare_resume(body=str(body_output))

    logger.info(f"Step 4: Fixing Resume: {assembled_resume}")
    keep_thesis = True
    jd_file = target_folder / "jd.txt"
    if jd_file.exists():
        try:
            keep_thesis = decide_keep_thesis(jd_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to dynamically decide keep_thesis via LLM: {e}. Defaulting to True.")

    fix_file(str(assembled_resume), keep_thesis=keep_thesis)

    logger.info(f"Step 5: Checking Resume: {assembled_resume}")

    for _ in range(2):  # first run is for fixer, second to check for feedback if needed
        content = assembled_resume.read_text(encoding="utf-8")
        errors = check_markdown(content)
        if not errors:
            logger.info("No errors found during Step 5 check.")
            break

        logger.warning(f"Found {len(errors)} errors during Step 5 check.")
        for err in errors:
            logger.error(f"{err.msg}\n{err.filepath}:{err.line_num}: `{err.line}`")

        if feedback:
            logger.info("Feedback option enabled: running fix_with_feedback...")
            fixed_content = fix_with_feedback(content)
            assembled_resume.write_text(fixed_content, encoding="utf-8")
        else:
            # feedback not enabled, just stop after the first run
            break

    logger.info(f"Step 6: Converting Resume to PDF: {pdf_output}")
    convert_md_to_pdf(assembled_resume, pdf_output)

    logger.info(f"Step 7: Checking PDF layout: {pdf_output}")
    pdf_errors = check_pdf(pdf_output)
    for err in pdf_errors:
        logger.error(err)

    logger.info("Successfully finished composing Resume locally!")
