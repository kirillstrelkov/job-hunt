import re
from loguru import logger
from cv.tools.checker import get_sort_key
from md_tools.models import (
    CourseOrCertificate,
    Line,
    PersonalProjects,
    Section,
    Summary,
    SkillGroup,
    Language,
    Education,
    WorkExperience,
    Info,
)

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


class Fix:
    """Base class for all section fixers."""

    def fix(self, section: Section) -> Section:
        """Apply the fix logic on the section in-place."""
        raise NotImplementedError


class SkillsFix(Fix):
    """Formats Skills section lines to end with exactly two spaces."""

    def fix(self, section: Section) -> Section:
        new_lines = []
        for line_obj in section.raw_lines:
            line_str = line_obj.raw_line
            if (line_str.startswith("**") or ":" in line_str) and not line_str.endswith("  "):
                line_obj.raw_line = line_str.rstrip() + "  "
            new_lines.append(line_obj)
        section.raw_lines = new_lines
        return section


class ThesisFix(Fix):
    """Removes thesis lines when keep_thesis is false."""

    def fix(self, section: Section, *, keep_thesis: bool = True) -> Section:
        if keep_thesis:
            return section
        new_lines = [line_obj for line_obj in section.raw_lines if not line_obj.raw_line.strip().startswith("- Thesis")]
        section.raw_lines = new_lines
        return section


class MonthShortenerFix(Fix):
    """Replaces full month names with short names in section lines."""

    def fix(self, section: Section) -> Section:
        for line_obj in section.raw_lines:
            line_str = line_obj.raw_line
            for full_m_re, short_m in MONTHS_TO_SHORT_RE.items():
                line_str = full_m_re.sub(short_m, line_str)
            line_obj.raw_line = line_str
        return section


class TrailingDotFix(Fix):
    """Strips trailing dots from section lines (like WorkExperience or PersonalProjects)."""

    def fix(self, section: Section) -> Section:
        for line_obj in section.raw_lines:
            line_obj.raw_line = RE_TRAILING_DOT.sub(r"\1", line_obj.raw_line)
        return section


class CourseCertificateFormatterFix(Fix):
    """Normalizes courses/certificates line formatting and ensures dates are preceded by \hfill."""

    def fix(self, section: Section) -> Section:
        for line_obj in section.raw_lines:
            line_str = line_obj.raw_line
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
            line_obj.raw_line = line_str
        return section


class LastPipeFix(Fix):
    """Replaces trailing '| Year' date delimiters with \hfill."""

    def fix(self, section: Section) -> Section:
        for line_obj in section.raw_lines:
            if RE_LAST_PIPE_YEAR.search(line_obj.raw_line):
                line_obj.raw_line = RE_LAST_PIPE_REPLACE.sub(r"\\hfill\1", line_obj.raw_line)
        return section


class ChronologicalSortingFix(Fix):
    """Chronologically sorts entries in PersonalProjects and CourseOrCertificate sections."""

    def fix(self, section: Section) -> Section:
        if not isinstance(section, (PersonalProjects, CourseOrCertificate)):
            return section

        sec_text = "\n".join(l.raw_line for l in section.raw_lines)
        try:
            new_section = type(section).from_string(sec_text, section.filepath, section.raw_lines)
            new_section.entries.sort(key=lambda x: get_sort_key(x.duration.to_string()), reverse=True)
            new_sec_text = new_section.to_string()
            new_section.raw_lines = [
                Line(raw_line=raw_l, number=i + 1) for i, raw_l in enumerate(new_sec_text.splitlines())
            ]
            return new_section
        except Exception:  # noqa: BLE001
            return section


_FIX_CONFIG = {
    Info: [MonthShortenerFix, LastPipeFix],
    Summary: [MonthShortenerFix, LastPipeFix],
    SkillGroup: [SkillsFix],
    Language: [MonthShortenerFix, LastPipeFix],
    Education: [MonthShortenerFix, LastPipeFix],
    WorkExperience: [ThesisFix, MonthShortenerFix, TrailingDotFix, LastPipeFix],
    PersonalProjects: [ThesisFix, MonthShortenerFix, TrailingDotFix, LastPipeFix, ChronologicalSortingFix],
    CourseOrCertificate: [
        ThesisFix,
        MonthShortenerFix,
        CourseCertificateFormatterFix,
        LastPipeFix,
        ChronologicalSortingFix,
    ],
    Section: [MonthShortenerFix, LastPipeFix],
}
