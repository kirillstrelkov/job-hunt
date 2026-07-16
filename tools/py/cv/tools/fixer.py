import re

from cv.tools.checker import get_sort_key
from md.models import (
    CourseOrCertificate,
    Education,
    Info,
    Language,
    PersonalProjects,
    SkillGroup,
    Summary,
    WorkExperience,
)
from md.parse import IndexedLine, Section

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

RE_ENDS_WITH_YEAR = re.compile(r"\d{4}$")
RE_LEADING_SPACES = re.compile(r"^\s*")
RE_COURSE_ADD_HFILL = re.compile(r"\s+([A-Za-z]+\s+\d{4})$")
RE_LAST_PIPE_YEAR = re.compile(r"\|\s*([A-Za-z]*\s*\d{4}.*)$")
RE_LAST_PIPE_REPLACE = re.compile(r"\|([^|]*)$")
RE_TRAILING_DOT = re.compile(r"\.(\s*)$")

MONTHS_TO_SHORT_RE = {re.compile(rf"\b{full_m}\b"): short_m for full_m, short_m in MONTHS_TO_SHORT.items()}


def recreate_section(section: Section) -> Section:
    """Helper function to recreate/re-parse a Section object from its current indexed_lines."""
    sec_text = str(section)
    if not sec_text:
        return section

    return type(section).from_string(sec_text, section.filepath)


class Fix:
    """Base class for all section fixers."""

    def fix(self, section: Section) -> Section:
        """Apply the fix logic on the section in-place."""
        raise NotImplementedError


class SkillsFix(Fix):
    """Formats Skills section lines to end with backslash."""

    def fix(self, section: Section) -> Section:
        new_lines = []
        for line_obj in section.indexed_lines:
            line_str = line_obj.line
            if (line_str.startswith("**") or ":" in line_str) and not line_str.endswith("\\"):
                line_obj.line = line_str.rstrip() + "\\"
            new_lines.append(line_obj)
        section.indexed_lines = new_lines
        return recreate_section(section)


class ThesisFix(Fix):
    """Removes thesis lines when keep_thesis is false."""

    def fix(self, section: Section, *, keep_thesis: bool = True) -> Section:
        if keep_thesis:
            return section
        new_lines = [line_obj for line_obj in section.indexed_lines if not line_obj.line.strip().startswith("- Thesis")]
        section.indexed_lines = new_lines
        return recreate_section(section)


class MonthShortenerFix(Fix):
    """Replaces full month names with short names in section lines."""

    def fix(self, section: Section) -> Section:
        if not section.indexed_lines:
            return section

        for line_obj in section.indexed_lines:
            line_str = line_obj.line
            for full_m_re, short_m in MONTHS_TO_SHORT_RE.items():
                line_str = full_m_re.sub(short_m, line_str)
            line_obj.line = line_str
        return recreate_section(section)


# TODO: should be done only to final text file
class TrailingDotFix(Fix):
    """Strips trailing dots from section lines (like WorkExperience or PersonalProjects)."""

    def fix(self, section: Section) -> Section:
        for line_obj in section.indexed_lines:
            line_obj.line = RE_TRAILING_DOT.sub(r"\1", line_obj.line)
        return recreate_section(section)


def fix_last_pipe(md: str) -> str:
    r"""Replace trailing '| Year' date delimiters with \hfill."""
    lines = md.split("\n")
    fixed_lines = []
    for line in lines:
        if RE_LAST_PIPE_YEAR.search(line):
            line = RE_LAST_PIPE_REPLACE.sub(r"\\hfill\1", line)
        fixed_lines.append(line)
    return "\n".join(fixed_lines)


class LastPipeFix(Fix):
    r"""Replaces trailing '| Year' date delimiters with \hfill."""

    def fix(self, section: Section) -> Section:
        for line_obj in section.indexed_lines:
            line_obj.line = fix_last_pipe(line_obj.line)
        return recreate_section(section)


class ChronologicalSortingFix(Fix):
    """Chronologically sorts entries in PersonalProjects and CourseOrCertificate sections."""

    def fix(self, section: Section) -> Section:
        if not isinstance(section, (PersonalProjects, CourseOrCertificate)):
            return section

        sec_text = "\n".join(l.line for l in section.indexed_lines) if section.indexed_lines else section.to_string()
        try:
            new_section = type(section).from_string(sec_text, section.filepath)
            new_section.entries.sort(key=lambda x: get_sort_key(x.duration.to_string()), reverse=True)
            new_sec_text = new_section.to_string()
            new_section.indexed_lines = [
                IndexedLine(line=raw_l, index=i + 1) for i, raw_l in enumerate(new_sec_text.splitlines())
            ]
            return new_section
        except Exception:  # noqa: BLE001
            return section


_FIX_CONFIG = {
    Info: [MonthShortenerFix],
    Summary: [MonthShortenerFix],
    SkillGroup: [SkillsFix],
    WorkExperience: [MonthShortenerFix, ChronologicalSortingFix, TrailingDotFix],
    PersonalProjects: [MonthShortenerFix, ChronologicalSortingFix, TrailingDotFix],
    CourseOrCertificate: [MonthShortenerFix, ChronologicalSortingFix],
    Education: [ThesisFix, MonthShortenerFix],
    Language: [MonthShortenerFix],
}
