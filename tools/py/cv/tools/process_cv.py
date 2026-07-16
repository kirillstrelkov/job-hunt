#!/usr/bin/env python3
"""Check and fix CV markdown formatting and chronological consistency."""

import argparse
import sys
from pathlib import Path

from loguru import logger

from cv.tools.checker import Error, get_section_class
from cv.tools.checker import check as do_check
from cv.tools.fixer import _FIX_CONFIG
from md_tools.format import format as format_md
from md_tools.models import CV
from md_tools.parse import Section, split_markdown_into_sections


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for CV checking and fixing."""
    parser = argparse.ArgumentParser(description="Check and fix CV markdown file.")
    parser.add_argument("file", type=str, help="Path to the markdown file")
    parser.add_argument("--check", action="store_true", help="Check the file for errors")
    parser.add_argument("--keep-thesis", action="store_true", help="Keep thesis name")
    parser.add_argument("--fix", action="store_true", help="Fix the errors in the file")
    return parser.parse_args()


def split_into_sections(filepath: str) -> list[Section]:
    """Parse the CV file and split it into sections based on markdown headers."""
    path = Path(filepath)
    with path.open("r", encoding="utf-8") as f:
        content = f.read()
    return split_markdown_into_sections(content, filepath=path)


def do_fix(cv: CV, *, keep_thesis: bool = True) -> CV:
    """Apply sorting, formatting and structure fixes to a CV object."""
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

    if cv.header:
        cv.header.info_sec = run_fixes(cv.header.info_sec)
    if cv.summary:
        cv.summary = run_fixes(cv.summary)
    if cv.skills:
        cv.skills = run_fixes(cv.skills)
    if cv.body:
        cv.body.work_experience_sec = run_fixes(cv.body.work_experience_sec)
        cv.body.personal_projects_sec = run_fixes(cv.body.personal_projects_sec)
        cv.body.courses_and_certificates_sec = run_fixes(cv.body.courses_and_certificates_sec)
    if cv.footer:
        if cv.footer.education_sec:
            cv.footer.education_sec = run_fixes(cv.footer.education_sec)
        if cv.footer.language_sec:
            cv.footer.language_sec = run_fixes(cv.footer.language_sec)

    return cv


def check_file(filepath: str) -> None:
    """Run verification checks on a CV file path."""
    logger.debug("Checking file {}", filepath)

    sections = split_into_sections(filepath)
    errors = do_check(sections, is_cv=True)
    if errors:
        logger.error("Found {} errors", len(errors))
        for err in errors:
            logger.error(f"{err.msg}\n{err.filepath}:{err.line_num}: `{err.line}`")
        sys.exit(1)
    logger.info("No errors found")


def fix_file(filepath: str, *, keep_thesis: bool = True) -> None:
    """Apply auto-formatting and structure fixes to a CV file path."""
    logger.debug("Fixing file {}", filepath)
    path = Path(filepath)
    content = path.read_text(encoding="utf-8")
    fixed_content = fix_markdown(content, keep_thesis=keep_thesis)
    path.write_text(fixed_content, encoding="utf-8")
    logger.info("Fixes applied and file written")


def check_markdown(md: str, *, filepath: str = "CV.md") -> list[Error]:
    """Run verification checks on a CV markdown string, returning a list of Error objects."""
    sections = split_markdown_into_sections(md, filepath=Path(filepath) if filepath else None)
    return do_check(sections, is_cv=True)


def fix_markdown(md: str, *, keep_thesis: bool = True) -> str:
    """Apply auto-formatting and structure fixes to a CV markdown string, returning the fixed string."""
    cv_obj = CV.from_string(md)
    cv_obj = do_fix(cv_obj, keep_thesis=keep_thesis)
    return format_md(cv_obj.to_string())


def main() -> None:
    """Run the main CLI entry point for checking and fixing CV files."""
    args = parse_args()

    logger.info("Starting CV processing for file: {}", args.file)

    if args.check:
        logger.info("Running checks...")
        check_file(args.file)

    if args.fix:
        logger.info("Applying fixes...")
        fix_file(args.file, keep_thesis=args.keep_thesis)


if __name__ == "__main__":
    main()


# Future: check for wrong link syntax in projects section (e.g. mismatched brackets).
