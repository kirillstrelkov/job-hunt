#!/usr/bin/env python3
"""Validation and formatting checker for CV markdown files."""

from md_tools.models import is_root_section
import argparse
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from md_tools.models import (
    CourseOrCertificate,
    Education,
    Info,
    Language,
    Line,
    PersonalProjects,
    Section,
    SectionConstant,
    SkillGroup,
    Summary,
    WorkExperience,
)
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

RE_DATE_EXTRACT = re.compile(r"([A-Z][a-z]+)?\s*(\d{4})")
RE_WORK_EXP = re.compile(r"^\*\*(.*?)\*\*\s*\|\s*_(.*?)_\s*(?:\||\\hfill)\s*(.*)$")
RE_PIPE_SPLIT = re.compile(r"\||\\hfill")
RE_ENDS_WITH_YEAR = re.compile(r"\d{4}$")
RE_COURSE_FORMAT = re.compile(r"^\- .+?\| \_.+?\_ \s*(?:\||\\hfill)\s*\w{3}\s\d{4}$")
RE_COURSE_DATE = re.compile(r"([A-Za-z]+\s+\d{4})$")
RE_PHONE = re.compile(r"[\d\s]{5,}")

_CUR_YEAR = datetime.now(UTC).year


@dataclass
class Error:
    """Represents a validation error found in the CV."""

    msg: str
    filepath: str
    line_num: int
    line: str


def make_error(msg: str, section: Section, line: Line) -> Error:
    """Create an Error instance for a specific section and line."""
    return Error(
        msg=msg,
        filepath=str(section.filepath),
        line_num=line.number,
        line=line.raw_line,
    )


def get_sort_key(date_str: str) -> tuple[int, int]:
    """Calculate a numerical sort key (year, month) from a date string for sorting."""
    if date_str.endswith("..."):
        return (_CUR_YEAR, 1)

    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    month_map = {m: i + 1 for i, m in enumerate(month_names)}
    for full, short in MONTHS_TO_SHORT.items():
        month_map[full] = month_map[short]

    matches = RE_DATE_EXTRACT.findall(date_str)

    if not matches:
        return (0, 0)

    m_str, y_str = matches[-1]
    year = int(y_str)
    month = month_map.get(m_str, 1) if m_str else 1

    return (year, month)


class Check:
    """Base class for all checkers."""

    def check(self, section: Section) -> list[Error]:
        """Run check on a Section and return a list of Error objects."""
        raise NotImplementedError


class DotCheck(Check):
    """Checks that lines do not end with a dot, except in 'Summary' section."""

    def check(self, section: Section) -> list[Error]:
        if section.name.lower() == SectionConstant.SUMMARY.lower():
            return []

        errors = []
        for line in section.raw_lines:
            stripped = line.raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # Allow thesis lines or other custom formats that might end with a dot?
            # Standard requirements say "lines doesn't ends with '.'"
            if stripped.endswith("."):
                errors.append(make_error("Line ends with a dot", section, line))
        return errors


class TwoSpaceCheck(Check):
    """Checks that lines do not end with two spaces, except in Skills section (which must)."""

    def check(self, section: Section) -> list[Error]:
        errors = []
        if section.is_root():
            return errors

        is_skills = section.name.lower() == SectionConstant.SKILLS.lower()

        for line in section.raw_lines:
            stripped = line.raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            ends_with_two_spaces = line.raw_line.endswith("  ") and not line.raw_line.endswith("   ")

            if is_skills:
                # Skills section lines must end with exactly two spaces
                if not ends_with_two_spaces:
                    errors.append(
                        make_error(
                            "Line in Skills section must end with exactly two spaces",
                            section,
                            line,
                        )
                    )
            # Other sections must not end with two spaces
            elif line.raw_line.endswith("  "):
                errors.append(make_error("Line ends with two spaces", section, line))
        return errors


class ASpaceCheck(Check):
    """Checks that text does not contain ' a '."""

    def check(self, section: Section) -> list[Error]:
        errors = []
        if section.name == SectionConstant.COURSES_AND_CERTIFICATES:
            return errors

        for line in section.raw_lines:
            if " a " in line.raw_line:
                errors.append(make_error("Text contains ' a '", section, line))
        return errors


class DurationCheck(Check):
    """Checks that all years in a line's last segment are part of a properly formatted duration/date.

    Proper formats are:
    - MMM YYYY
    - MMM YYYY - MMM YYYY
    - MMM YYYY - Present
    """

    def check(self, section: Section) -> list[Error]:
        errors = []
        months_pat = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"

        # Patterns matching the entire last segment
        pat_range = re.compile(rf"^{months_pat}\s+\d{{4}}\s+-\s+{months_pat}\s+\d{{4}}$")
        pat_present = re.compile(rf"^{months_pat}\s+\d{{4}}\s+-\s+Present$")
        pat_single = re.compile(rf"^{months_pat}\s+\d{{4}}$")

        for line in section.raw_lines:
            parts = RE_PIPE_SPLIT.split(line.raw_line)
            if not parts:
                continue
            last_part = parts[-1].strip()

            if RE_PHONE.search(last_part):
                # skip for telephone
                continue

            if RE_ENDS_WITH_YEAR.search(last_part) or last_part.lower().endswith("present"):
                is_valid = (
                    pat_range.match(last_part) is not None
                    or pat_present.match(last_part) is not None
                    or pat_single.match(last_part) is not None
                )
                if not is_valid:
                    errors.append(
                        make_error(
                            "Line contains a year in an invalid format. Must be in MMM YYYY, MMM YYYY - MMM YYYY, or MMM YYYY - Present format",
                            section,
                            line,
                        )
                    )

        return errors


class BraketCheck(Check):
    """Checks brackets spacing conventions:

    - Only ' (' is correct (exactly one space before open bracket, meaning match of \\s+\\( length is 2)
    - '( ' is not correct (space after open bracket is invalid)
    """

    def check(self, section: Section) -> list[Error]:
        errors = []
        for line in section.raw_lines:
            # 1. Check spacing before '('
            matches = list(re.finditer(r"\s+\(", line.raw_line))
            for m in matches:
                if len(m.group(0)) != 2:  # 2 characters means exactly one space followed by '('
                    errors.append(
                        make_error(
                            f"Invalid spacing before open bracket: '{m.group(0)}'",
                            section,
                            line,
                        )
                    )

            # 2. Check spacing after '('
            if "( " in line.raw_line:
                errors.append(make_error("Space after open bracket '(' is not allowed", section, line))

        return errors


class ChronologicalCheck(Check):
    """Checks chronological ordering in specific CV sections."""

    def check(self, section: Section) -> list[Error]:
        errors = []
        heading_title = section.name.lower()

        if SectionConstant.WORK_EXPERIENCE.lower() in heading_title:
            line_and_dates = []
            for line_obj in section.raw_lines:
                line_str = line_obj.raw_line.strip()
                if line_str.startswith("**") and "_ " in line_str and RE_WORK_EXP.match(line_str):
                    date_str = RE_PIPE_SPLIT.split(line_str)[-1].strip()
                    skey = get_sort_key(date_str)
                    line_and_dates.append((line_obj, (skey, date_str, line_str)))
            errors.extend(self._check_chronological(line_and_dates, section))

        elif SectionConstant.COURSES_AND_CERTIFICATES.lower() in heading_title:
            line_and_dates = []
            for line_obj in section.raw_lines:
                line_str = line_obj.raw_line.strip()
                if not line_str:
                    continue
                if RE_ENDS_WITH_YEAR.search(line_str):
                    if RE_COURSE_FORMAT.match(line_str):
                        date_str = RE_PIPE_SPLIT.split(line_str)[-1].strip()
                    else:
                        parts = RE_PIPE_SPLIT.split(line_str)
                        if len(parts) >= 2:  # noqa: PLR2004
                            date_str = parts[-1].strip()
                        else:
                            match = RE_COURSE_DATE.search(line_str)
                            date_str = match.group(1) if match else line_str
                    skey = get_sort_key(date_str)
                    line_and_dates.append((line_obj, (skey, date_str, line_str)))
            errors.extend(self._check_chronological(line_and_dates, section))

        elif "projects" in heading_title or SectionConstant.PERSONAL_PROJECTS.lower() in heading_title:
            line_and_dates = []
            for line_obj in section.raw_lines:
                line_str = line_obj.raw_line.strip()
                if line_str.startswith("**["):
                    date_str = RE_PIPE_SPLIT.split(line_str)[-1].strip()
                    skey = get_sort_key(date_str)
                    line_and_dates.append((line_obj, (skey, date_str, line_str)))
            errors.extend(self._check_chronological(line_and_dates, section, double_error=True))

        return errors

    def _check_chronological(
        self, line_and_dates: list, section: Section, *, double_error: bool = False
    ) -> list[Error]:
        errors = []
        for i in range(len(line_and_dates) - 1):
            line1_obj, (key1, _, line_str1) = line_and_dates[i]
            line2_obj, (key2, _, line_str2) = line_and_dates[i + 1]
            if key1 < key2:
                errors.append(
                    make_error(
                        f"Chronological order broken in {section.name}: '{line_str1}' is before '{line_str2}'",
                        section,
                        line1_obj,
                    )
                )
                if double_error:
                    errors.append(
                        make_error(
                            f"Chronological order broken in {section.name}: '{line_str2}' is after '{line_str1}'",
                            section,
                            line2_obj,
                        )
                    )
        return errors


class FormatCheck(Check):
    """Checks structural formatting conventions in specific CV sections."""

    def check(self, section: Section) -> list[Error]:
        errors = []
        heading_title = section.name.lower()

        if SectionConstant.WORK_EXPERIENCE.lower() in heading_title:
            for line_obj in section.raw_lines:
                line_str = line_obj.raw_line.strip()
                if line_str.startswith("**") and "_ " in line_str and not RE_WORK_EXP.match(line_str):
                    errors.append(make_error(f"{section.name} format mismatch", section, line_obj))

        elif SectionConstant.COURSES_AND_CERTIFICATES.lower() in heading_title:
            for line_obj in section.raw_lines:
                line_str = line_obj.raw_line.strip()
                if not line_str:
                    continue
                if RE_ENDS_WITH_YEAR.search(line_str) and not RE_COURSE_FORMAT.match(line_str):
                    errors.append(make_error(f"{section.name} format mismatch", section, line_obj))
        return errors


class RequiredSectionsCheck:
    """Checks that all required sections exist in the CV."""

    def check_all(self, sections: list[Section]) -> list[Error]:
        filepath = str(sections[0].filepath) if sections else ""
        section_names = [s.name.lower() for s in sections if s.name]
        required_headers = [
            SectionConstant.WORK_EXPERIENCE.lower(),
            SectionConstant.PERSONAL_PROJECTS.lower(),
            SectionConstant.COURSES_AND_CERTIFICATES.lower(),
        ]

        return [
            Error(
                msg=f"Missing '{req}' section in headers",
                filepath=filepath,
                line_num=1,
                line="",
            )
            for req in required_headers
            if not any(req in name for name in section_names)
        ]


def get_section_class(section: Section) -> type[Section]:
    """Determine the Section subclass corresponding to a generic Section name/prefix."""
    if is_root_section(section):
        return Info

    name_lower = section.name.lower()
    mapping = {
        SectionConstant.SUMMARY.lower(): Summary,
        SectionConstant.SKILLS.lower(): SkillGroup,
        SectionConstant.WORK_EXPERIENCE.lower(): WorkExperience,
        SectionConstant.PERSONAL_PROJECTS.lower(): PersonalProjects,
        SectionConstant.COURSES_AND_CERTIFICATES.lower(): CourseOrCertificate,
        SectionConstant.EDUCATION.lower(): Education,
        SectionConstant.LANGUAGES.lower(): Language,
    }
    return mapping.get(name_lower, Section)


def get_all_check_klasses(skip: list[type[Check]] | None = None) -> list[type[Check]]:
    """Return all check classes, optionally excluding some."""
    all_klasses = [
        DotCheck,
        TwoSpaceCheck,
        ASpaceCheck,
        BraketCheck,
        DurationCheck,
        FormatCheck,
        ChronologicalCheck,
    ]
    if skip:
        return [k for k in all_klasses if k not in skip]
    return all_klasses


_CHECK_CONFIG = {
    Info: get_all_check_klasses(skip=[TwoSpaceCheck]),
    Summary: get_all_check_klasses(skip=[DotCheck]),
    SkillGroup: get_all_check_klasses(),
    Language: get_all_check_klasses(),
    Education: get_all_check_klasses(),
    WorkExperience: get_all_check_klasses(),
    PersonalProjects: get_all_check_klasses(),
    CourseOrCertificate: get_all_check_klasses(skip=[ASpaceCheck]),
    Section: get_all_check_klasses(),
}


def check(sections: list[Section], *, is_cv: bool = False) -> list[Error]:
    """Run all validation checkers on the provided sections based on _CHECK_CONFIG."""
    errors = []

    for section in sections:
        sec_class = get_section_class(section)
        check_classes = _CHECK_CONFIG.get(sec_class, _CHECK_CONFIG.get(Section, []))

        for check_class in check_classes:
            checker = check_class()
            errors.extend(checker.check(section))

    if is_cv:
        errors.extend(RequiredSectionsCheck().check_all(sections))
    return errors


def check_file(filepath: str, *, is_cv: bool = False) -> None:
    """Check a markdown file path for errors."""
    logger.debug("Checking file {}", filepath)
    path = Path(filepath)
    if not path.exists():
        logger.error("File not found: {}", filepath)
        sys.exit(1)

    content = path.read_text(encoding="utf-8")

    sections = split_markdown_into_sections(content, filepath=path)
    errors = check(sections, is_cv=is_cv)
    if errors:
        logger.error("Found {} errors", len(errors))
        for err in errors:
            logger.error(f"{err.msg}\n{err.filepath}:{err.line_num}: `{err.line}`")
        sys.exit(1)
    logger.info("No errors found")


def main() -> None:
    """Command line entrypoint for checking markdown files."""
    parser = argparse.ArgumentParser(description="Check CV markdown file.")
    parser.add_argument("file", type=str, help="Path to the markdown file")
    parser.add_argument("--cv", action="store_true", default=False, help="Run CV-specific required sections check")
    args = parser.parse_args()
    check_file(args.file, is_cv=args.cv)


if __name__ == "__main__":
    main()
