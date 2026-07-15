#!/usr/bin/env python3
"""Check and fix CV markdown formatting and chronological consistency."""

import argparse
import re
import sys
from pathlib import Path

from loguru import logger

from cv.tools.checker import Error
from cv.tools.checker import check as do_check
from md_tools.format import format as format_md
from md_tools.models import Section, SectionConstant
from md_tools.parse import split_markdown_into_sections

MONTHS_TO_SHORT = {
    "January": "Jan",
    "February": "Feb",
    "March": "Mar",
    "April": "Apr",
    "May": "May",
    "June": "Jun",
    "July": "Jul",
    "August": "Aug",
    "September": "Sep",
    "October": "Oct",
    "November": "Nov",
    "December": "Dec",
}

RE_HEADING = re.compile(r"^#+\s")
RE_DATE_EXTRACT = re.compile(r"([A-Z][a-z]+)?\s*(\d{4})")
RE_WORK_EXP = re.compile(r"^\*\*(.*?)\*\*\s*\|\s*_(.*?)_\s*(?:\||\\hfill)\s*(.*)$")
RE_PIPE_SPLIT = re.compile(r"\||\\hfill")
RE_ENDS_WITH_YEAR = re.compile(r"\d{4}$")
RE_COURSE_FORMAT = re.compile(r"^\- .+?\| \_.+?\_ \s*(?:\||\\hfill)\s*\w{3}\s\d{4}$")
RE_COURSE_DATE = re.compile(r"([A-Za-z]+\s+\d{4})$")
RE_LEADING_SPACES = re.compile(r"^\s*")
RE_COURSE_ADD_HFILL = re.compile(r"\s+([A-Za-z]+\s+\d{4})$")
RE_LAST_PIPE_YEAR = re.compile(r"\|\s*([A-Za-z]*\s*\d{4}.*)$")
RE_LAST_PIPE_REPLACE = re.compile(r"\|([^|]*)$")
RE_TRAILING_DOT = re.compile(r"\.(\s*)$")

MONTHS_TO_SHORT_RE = {re.compile(rf"\b{full_m}\b"): short_m for full_m, short_m in MONTHS_TO_SHORT.items()}


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


def _fix_skills_section(section: Section) -> None:
    if section.name.lower() != SectionConstant.SKILLS.lower():
        return

    new_lines = []
    for line_obj in section.raw_lines:
        line_str = line_obj.raw_line
        # fix markdown new flie with 2 spaces at the end
        if (line_str.startswith("**") or ":" in line_str) and not line_str.endswith("  "):
            line_obj.raw_line = line_str.rstrip() + "  "

        new_lines.append(line_obj)

    section.raw_lines = new_lines


def do_fix(sections: list[Section], *, keep_thesis: bool = True) -> list[Section]:  # noqa: C901
    """Apply sorting, formatting and structure fixes to CV sections."""
    if not keep_thesis:
        logger.warning("Thesis will be removed")

    for section in sections:
        heading_title = section.name.lower()
        if heading_title == SectionConstant.SKILLS.lower():
            _fix_skills_section(section)
            continue

        filtered_lines = []
        for line_obj in section.raw_lines:
            if not keep_thesis and line_obj.raw_line.strip().startswith("- Thesis"):
                continue

            line_str = line_obj.raw_line
            for full_m_re, short_m in MONTHS_TO_SHORT_RE.items():
                line_str = full_m_re.sub(short_m, line_str)

            if (
                SectionConstant.WORK_EXPERIENCE.lower() in heading_title
                or "projects" in heading_title
                or SectionConstant.PERSONAL_PROJECTS.lower() in heading_title
            ):
                line_str = RE_TRAILING_DOT.sub(r"\1", line_str)

            if SectionConstant.COURSES_AND_CERTIFICATES.lower() in heading_title:
                line_stripped = line_str.strip()
                if line_stripped and not line_stripped.startswith("-") and RE_ENDS_WITH_YEAR.search(line_stripped):
                    line_str = RE_LEADING_SPACES.sub("- ", line_str)

                line_str = line_str.rstrip()
                if (
                    RE_ENDS_WITH_YEAR.search(line_str)
                    and "|" not in line_str
                    and r"\hfill" not in line_str
                    and r"/hfill" not in line_str
                ):
                    line_str = RE_COURSE_ADD_HFILL.sub(r" \\hfill \1", line_str)

            if RE_LAST_PIPE_YEAR.search(line_str):
                line_str = RE_LAST_PIPE_REPLACE.sub(r"\\hfill\1", line_str)

            line_obj.raw_line = line_str
            filtered_lines.append(line_obj)

        section.raw_lines = filtered_lines

    return sections


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
    sections = split_markdown_into_sections(md)
    do_fix(sections, keep_thesis=keep_thesis)
    output_lines = []
    for section in sections:
        output_lines.extend(line_obj.raw_line for line_obj in section.raw_lines)
    fixed = "\n".join(output_lines) + ("\n" if output_lines else "")
    return format_md(fixed)


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
