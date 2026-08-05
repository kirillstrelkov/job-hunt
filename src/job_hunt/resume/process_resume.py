#!/usr/bin/env python3
"""Check and fix Resume markdown formatting and chronological consistency."""

import re
import sys
from pathlib import Path

from loguru import logger

from job_hunt.resume.checker import Error, check_and_get_errors, get_section_class
from job_hunt.resume.fixer import _FIX_CONFIG, fix_last_pipe
from job_hunt.resume.models import Resume
from job_hunt.resume.parse import Section, split_markdown_into_sections

RE_BREAK_LINE = re.compile(r"^\s*\\break\s*$")


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

    # \break lines aren't recognized by the section models and get dropped when the
    # Resume round-trips through parse -> fix -> to_string, so remove them up front,
    # remembering their surrounding context, and reinsert them afterwards.
    lines = md.split("\n")
    break_anchors = [
        (lines[i - 1] if i > 0 else "", lines[i + 1] if i + 1 < len(lines) else "")
        for i, line in enumerate(lines)
        if RE_BREAK_LINE.match(line)
    ]
    md_no_breaks = "\n".join(line for line in lines if not RE_BREAK_LINE.match(line))

    resume_obj = Resume.from_string(md_no_breaks)
    resume_obj = do_fix(resume_obj, keep_thesis=keep_thesis)
    # fmt_md = format_md(resume_obj.to_string()) # has errors for '\'
    fixed_md = fix_last_pipe(resume_obj.to_string())
    # Drop filler articles ('a'/'an') to keep bullet points terse
    fixed_md = fixed_md.replace(" a ", " ").replace(" an ", " ")

    return _restore_break_lines(fixed_md, break_anchors)


def _normalize_for_match(line: str) -> str:
    """Normalize a line the same way fix_markdown mutates surrounding text, so anchor lines still match."""
    line = line.strip().replace(" a ", " ").replace(" an ", " ").rstrip(".")
    return re.sub(r"\s+", " ", line)


def _restore_break_lines(md: str, break_anchors: list[tuple[str, str]]) -> str:
    r"""Reinsert \break lines between the same before/after lines they originally sat between."""
    fixed_lines = md.split("\n")
    for prev_line, next_line in break_anchors:
        prev_norm = _normalize_for_match(prev_line)
        next_norm = _normalize_for_match(next_line)
        for i, line in enumerate(fixed_lines):
            if (
                _normalize_for_match(line) == prev_norm
                and i + 1 < len(fixed_lines)
                and _normalize_for_match(fixed_lines[i + 1]) == next_norm
            ):
                fixed_lines.insert(i + 1, "\\break")
                break
    return "\n".join(fixed_lines)


# Future: check for wrong link syntax in projects section (e.g. mismatched brackets).
