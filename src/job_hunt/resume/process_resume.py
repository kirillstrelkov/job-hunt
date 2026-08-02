#!/usr/bin/env python3
"""Check and fix Resume markdown formatting and chronological consistency."""

import argparse
import sys
from pathlib import Path

from loguru import logger

from job_hunt.resume.checker import Error, check_and_get_errors, get_section_class
from job_hunt.resume.fixer import _FIX_CONFIG, fix_last_pipe
from job_hunt.resume.models import Resume
from job_hunt.resume.parse import Section, split_markdown_into_sections


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Resume checking and fixing."""
    parser = argparse.ArgumentParser(description="Check and fix Resume markdown file.")
    parser.add_argument("file", type=str, help="Path to the markdown file")
    parser.add_argument("--check", action="store_true", help="Check the file for errors")
    parser.add_argument("--keep-thesis", action="store_true", help="Keep thesis name")
    parser.add_argument("--fix", action="store_true", help="Fix the errors in the file")
    return parser.parse_args()


def split_into_sections(filepath: str) -> list[Section]:
    """Parse the Resume file and split it into sections based on markdown headers."""
    path = Path(filepath)
    with path.open("r", encoding="utf-8") as f:
        content = f.read()
    return split_markdown_into_sections(content, filepath=path)


def do_fix(resume: Resume, *, keep_thesis: bool = True) -> Resume:
    """Apply sorting, formatting and structure fixes to a Resume object."""
    if not keep_thesis:
        logger.warning("Thesis will be removed")

    def run_fixes(section: Section) -> Section:
        import inspect

        sec_class = get_section_class(section)
        fix_classes = _FIX_CONFIG.get(sec_class, _FIX_CONFIG.get(Section, []))
        for fix_class in fix_classes:
            fixer = fix_class()
            sig = inspect.signature(fixer.fix)
            if "keep_thesis" in sig.parameters:
                section = fixer.fix(section, keep_thesis=keep_thesis)
            else:
                section = fixer.fix(section)
        return section

    if resume.header:
        resume.header.info_sec = run_fixes(resume.header.info_sec)
    if resume.summary:
        resume.summary = run_fixes(resume.summary)
    if resume.skills:
        resume.skills = run_fixes(resume.skills)
    if resume.body:
        resume.body.work_experience_sec = run_fixes(resume.body.work_experience_sec)
        resume.body.personal_projects_sec = run_fixes(resume.body.personal_projects_sec)
        resume.body.courses_and_certificates_sec = run_fixes(resume.body.courses_and_certificates_sec)
    if resume.footer:
        if resume.footer.education_sec:
            resume.footer.education_sec = run_fixes(resume.footer.education_sec)
        if resume.footer.language_sec:
            resume.footer.language_sec = run_fixes(resume.footer.language_sec)

    return resume


def check_file(filepath: str) -> None:
    """Run verification checks on a Resume file path."""
    content = Path(filepath).read_text(encoding="utf-8")
    errors = check_and_get_errors(content, is_resume=True)
    if errors:
        logger.error("Found {} errors", len(errors))
        for err in errors:
            logger.error(f"{err.msg}\n{err.filepath}:{err.line_num}: `{err.line}`")
        sys.exit(1)
    logger.info("No errors found")


def fix_file(filepath: str, *, keep_thesis: bool = True) -> None:
    """Apply auto-formatting and structure fixes to a Resume file path."""
    logger.debug("Fixing file {}", filepath)
    path = Path(filepath)
    content = path.read_text(encoding="utf-8")
    fixed_content = fix_markdown(content, keep_thesis=keep_thesis)
    path.write_text(fixed_content, encoding="utf-8")
    logger.info("Fixes applied and file written")


def check_markdown(md: str, *, filepath: str = "Resume.md") -> list[Error]:
    """Run verification checks on a Resume markdown string, returning a list of Error objects."""
    return check_and_get_errors(md, is_resume=True)


def fix_markdown(md: str, *, keep_thesis: bool = True) -> str:
    """Apply auto-formatting and structure fixes to a Resume markdown string, returning the fixed string."""
    # \hfill is not supported so first replace it
    md = md.replace("\\hfill", "|")

    resume_obj = Resume.from_string(md)
    resume_obj = do_fix(resume_obj, keep_thesis=keep_thesis)
    # fmt_md = format_md(resume_obj.to_string()) # has errors for '\'
    return fix_last_pipe(resume_obj.to_string())


def main() -> None:
    """Run the main CLI entry point for checking and fixing Resume files."""
    args = parse_args()

    logger.info("Starting Resume processing for file: {}", args.file)

    if args.check:
        logger.info("Running checks...")
        check_file(args.file)

    if args.fix:
        logger.info("Applying fixes...")
        fix_file(args.file, keep_thesis=args.keep_thesis)


if __name__ == "__main__":
    main()


# Future: check for wrong link syntax in projects section (e.g. mismatched brackets).
