#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from loguru import logger
from pydantic import BaseModel, Field

# Ensure local tools and parent paths are in sys.path
tools_dir = Path(__file__).resolve().parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

tools_py_dir = tools_dir.parent.parent
if str(tools_py_dir) not in sys.path:
    sys.path.insert(0, str(tools_py_dir))

from .prepare_cv import prepare_cv
from .tailor_cv_body import run_ollama, process_output_of_ollama, get_eval_model
from .process_cv import fix_file, check_file
from .md2pdf import convert_md_to_pdf

from helpers.llm import get_agent


class ThesisDecision(BaseModel):
    keep_thesis: bool = Field(
        description="Whether to keep the thesis name in the CV. This should be True if the job description is for a software test engineer / QA automation / SDET role, and False if it is for a developer / software engineer role."
    )
    reason: str = Field(description="Short reason/justification for the decision.")


def decide_keep_thesis(jd_text: str) -> bool:
    """Run LLM with structured output to decide whether to keep the thesis in CV."""
    model_name = get_eval_model()

    logger.info(f"Running LLM ({model_name}) to decide whether to keep the thesis based on job description...")
    agent = get_agent(
        model_name=model_name,
        output_type=ThesisDecision,
        instructions=(
            "You are an expert recruiter and CV compiler. Analyze the job description and decide "
            "if it is for a software test engineer / QA / SDET (set keep_thesis to True) and not a software developer / "
            "engineer (set keep_thesis to False). The decision should be True only if the role is primarily focused on "
            "testing/QA/SDET, otherwise False."
        ),
    )
    result = agent.run_sync(f"Job Description:\n{jd_text}")
    decision: ThesisDecision = result.output
    logger.info(f"Thesis decision: keep_thesis={decision.keep_thesis} (Reason: {decision.reason})")
    return decision.keep_thesis


def tailor(folder: str | Path, model: str | None = None, force: bool = False) -> None:
    """Tailor CV locally for a given folder using the specified Ollama model."""
    folder = Path(folder).resolve()
    if not folder.exists():
        logger.error(f"Folder or file {folder} not found")
        sys.exit(1)

    target_folder = folder.parent if folder.is_file() else folder

    if not target_folder.is_dir():
        logger.error(f"Resolved folder is not a directory: {target_folder}")
        sys.exit(1)

    logger.info(f"Step 1: Preparing LLM prompt for {target_folder}")
    prepare_cv(folder=str(target_folder), llm_prompt=True)

    prompt_file = target_folder / "gen" / "llm_prompt.txt"
    model_name = model or get_eval_model()

    if model:
        model_suffix = model.replace(":", "-")
        body_output = target_folder / f"body-{model_suffix}.md"
        assembled_cv = target_folder / "gen" / f"cv-{model_suffix}.md"
        pdf_output = target_folder / "gen" / f"cv-{model_suffix}.pdf"
    else:
        body_output = target_folder / "body.md"
        assembled_cv = target_folder / "gen" / "cv.md"
        pdf_output = target_folder / "gen" / "cv.pdf"

    if force or not body_output.exists():
        logger.info(f"Step 2: Tailoring CV body with {model_name} model")
        prompt_content = prompt_file.read_text(encoding="utf-8")
        result = run_ollama(prompt_content, model_name)
        process_output_of_ollama(result, body_output)
    else:
        logger.warning(
            f"Step 2: Skipping LLM tailoring because {body_output.name} already exists. Use --force to re-generate."
        )

    logger.info("Step 3: Assembling CV from tailored body")
    prepare_cv(body=str(body_output))

    logger.info(f"Step 4: Fixing CV: {assembled_cv}")
    keep_thesis = True
    jd_file = target_folder / "jd.txt"
    if jd_file.exists():
        try:
            keep_thesis = decide_keep_thesis(jd_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to dynamically decide keep_thesis via LLM: {e}. Defaulting to True.")

    fix_file(str(assembled_cv), keep_thesis=keep_thesis)

    logger.info(f"Step 5: Checking CV: {assembled_cv}")
    try:
        check_file(str(assembled_cv))
    except (SystemExit, Exception):
        logger.warning("Step 5 check failed, but proceeding to Step 6 anyway.")

    logger.info(f"Step 6: Converting CV to PDF: {pdf_output}")
    convert_md_to_pdf(assembled_cv, pdf_output)

    logger.info("Successfully finished tailoring CV locally!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tailor CV locally using Ollama models.")
    parser.add_argument(
        "job_description",
        help="Path to the CV folder or the jd.txt file directly",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Ollama model to use for tailoring. If None, the configured eval model is used without filename prefixes.",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        default=False,
        help="Force execution of Step 2 (LLM tailoring) even if the tailored body file already exists",
    )
    args = parser.parse_args()

    tailor(folder=args.job_description, model=args.model, force=args.force)


if __name__ == "__main__":
    main()
