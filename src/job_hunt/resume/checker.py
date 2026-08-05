#!/usr/bin/env python3
"""Validation and formatting checker for Resume markdown files.

The canonical CLI/entrypoint for checking a Resume file lives in `resume.tools.process_resume`;
this module is the reusable checking implementation it (and other tools) build on.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from job_hunt.resume.models import (
    CourseOrCertificate,
    Education,
    Info,
    Language,
    PersonalProjects,
    SectionConstant,
    SkillGroup,
    Summary,
    WorkExperience,
    is_root_section,
)
from job_hunt.resume.parse import Heading, IndexedLine, Section, split_markdown_into_sections

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


class Error(BaseModel):
    """Represents a validation error found in the Resume."""

    msg: str
    filepath: str
    line_num: int
    line: str


def make_error(msg: str, section: Section, line: IndexedLine) -> Error:
    """Create an Error instance for a specific section and line."""
    return Error(
        msg=msg,
        filepath=str(section.filepath),
        line_num=line.index,
        line=line.line,
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

    _DEFAULT_ERROR_MSG = ""

    def __init__(self) -> None:
        self.errors = []

    def check(self, section: Section) -> list[Error]:
        """Run check on a Section and return a list of Error objects."""
        raise NotImplementedError

    def add_error(self, section: Section, line: IndexedLine, msg: str | None = None) -> None:
        if not msg:
            msg = self._DEFAULT_ERROR_MSG

        self.errors.append(make_error(msg, section, line))


class DotCheck(Check):
    """Checks that lines do not end with a dot, except in 'Summary' section."""

    _DEFAULT_ERROR_MSG = "Line ends with a dot"

    def check(self, section: Section) -> list[Error]:
        self.errors = []
        if section.heading.text.lower() == SectionConstant.SUMMARY.lower():
            return self.errors

        for line in section.indexed_lines:
            stripped = line.line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # Allow thesis lines or other custom formats that might end with a dot?
            # Standard requirements say "lines doesn't ends with '.'"
            if stripped.endswith("."):
                self.add_error(section, line)
        return self.errors


class TwoSpaceCheck(Check):
    """Checks that lines do not end with two spaces, except in Skills section (which must)."""

    _DEFAULT_ERROR_MSG = "Line in Skills section must end two spaces"
    _ERR_MSG_WRONG_ENDING = "Line must not end with two spaces"

    def check(self, section: Section) -> list[Error]:
        self.errors = []
        if is_root_section(section):
            return self.errors

        is_skills = section.heading.text.lower() == SectionConstant.SKILLS.lower()

        for line in section.indexed_lines:
            stripped = line.line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if is_skills:
                # Skills section lines must end with exactly two spaces or backslash
                if not line.line.endswith("  "):
                    self.add_error(section, line)
            # Other sections must not end with two spaces or backslash
            elif line.line.endswith("  "):
                self.add_error(section, line, self._ERR_MSG_WRONG_ENDING)
        return self.errors


class ASpaceCheck(Check):
    """Checks that text does not contain ' a '."""

    _DEFAULT_ERROR_MSG = "Text contains ' a '"

    def check(self, section: Section) -> list[Error]:
        self.errors = []
        if section.heading.text == SectionConstant.COURSES_AND_CERTIFICATES:
            return self.errors

        for line in section.indexed_lines:
            if " a " in line.line:
                self.add_error(section, line)
        return self.errors


class DurationCheck(Check):
    """Checks that all years in a line's last segment are part of a properly formatted duration/date.

    Proper formats are:
    - MMM YYYY
    - MMM YYYY - MMM YYYY
    - MMM YYYY - Present
    """

    _DEFAULT_ERROR_MSG = "Line contains a year in an invalid format. Must be in MMM YYYY, MMM YYYY - MMM YYYY, or MMM YYYY - Present format"

    def check(self, section: Section) -> list[Error]:
        self.errors = []
        months_pat = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"

        # Patterns matching the entire last segment
        pat_range = re.compile(rf"^{months_pat}\s+\d{{4}}\s+-\s+{months_pat}\s+\d{{4}}$")
        pat_present = re.compile(rf"^{months_pat}\s+\d{{4}}\s+-\s+Present$")
        pat_single = re.compile(rf"^{months_pat}\s+\d{{4}}$")

        for line in section.indexed_lines:
            parts = RE_PIPE_SPLIT.split(line.line)
            if not parts:
                continue
            last_part = parts[-1].strip()

            if (
                is_root_section(section) or section.heading.text.lower() == SectionConstant.INFO.lower()
            ) and RE_PHONE.search(last_part):
                # skip for telephone
                continue

            if RE_ENDS_WITH_YEAR.search(last_part) or last_part.lower().endswith("present"):
                is_valid = (
                    pat_range.match(last_part) is not None
                    or pat_present.match(last_part) is not None
                    or pat_single.match(last_part) is not None
                )
                if not is_valid:
                    self.add_error(section, line)

        return self.errors


class BraketCheck(Check):
    r"""Checks brackets spacing conventions:

    - Only ' (' is correct (exactly one space before open bracket, meaning match of \\s+\\( length is 2)
    - '( ' is not correct (space after open bracket is invalid)
    """

    _DEFAULT_ERROR_MSG = "Invalid spacing around brackets"

    def check(self, section: Section) -> list[Error]:
        self.errors = []
        for line in section.indexed_lines:
            # 1. Check spacing before '('
            matches = list(re.finditer(r"\s+\(", line.line))
            for m in matches:
                if len(m.group(0)) != 2:  # 2 characters means exactly one space followed by '('
                    self.add_error(
                        section,
                        line,
                        f"Invalid spacing before open bracket: '{m.group(0)}'",
                    )

            # 2. Check spacing after '('
            if "( " in line.line:
                self.add_error(section, line, "Space after open bracket '(' is not allowed")

        return self.errors


class ChronologicalCheck(Check):
    """Checks chronological ordering in specific Resume sections."""

    _DEFAULT_ERROR_MSG = "Chronological order broken"

    def check(self, section: Section) -> list[Error]:
        self.errors = []
        heading_title = section.heading.text.lower()

        if SectionConstant.WORK_EXPERIENCE.lower() in heading_title:
            line_and_dates = []
            for line_obj in section.indexed_lines:
                line_str = line_obj.line.strip()
                if line_str.startswith("**") and "_ " in line_str and RE_WORK_EXP.match(line_str):
                    date_str = RE_PIPE_SPLIT.split(line_str)[-1].strip()
                    skey = get_sort_key(date_str)
                    line_and_dates.append((line_obj, (skey, date_str, line_str)))
            self._check_chronological(line_and_dates, section)

        elif SectionConstant.COURSES_AND_CERTIFICATES.lower() in heading_title:
            line_and_dates = []
            for line_obj in section.indexed_lines:
                line_str = line_obj.line.strip()
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
            self._check_chronological(line_and_dates, section)

        elif "projects" in heading_title or SectionConstant.PERSONAL_PROJECTS.lower() in heading_title:
            line_and_dates = []
            for line_obj in section.indexed_lines:
                line_str = line_obj.line.strip()
                if line_str.startswith("**["):
                    date_str = RE_PIPE_SPLIT.split(line_str)[-1].strip()
                    skey = get_sort_key(date_str)
                    line_and_dates.append((line_obj, (skey, date_str, line_str)))
            self._check_chronological(line_and_dates, section, double_error=True)

        return self.errors

    def _check_chronological(self, line_and_dates: list, section: Section, *, double_error: bool = False) -> None:
        for i in range(len(line_and_dates) - 1):
            line1_obj, (key1, _, line_str1) = line_and_dates[i]
            line2_obj, (key2, _, line_str2) = line_and_dates[i + 1]
            if key1 < key2:
                self.add_error(
                    section,
                    line1_obj,
                    f"Chronological order broken in {section.heading.text}: '{line_str1}' is before '{line_str2}'",
                )
                if double_error:
                    self.add_error(
                        section,
                        line2_obj,
                        f"Chronological order broken in {section.heading.text}: '{line_str2}' is after '{line_str1}'",
                    )


class FormatCheck(Check):
    """Checks structural formatting conventions in specific Resume sections."""

    _DEFAULT_ERROR_MSG = "Format mismatch"

    def check(self, section: Section) -> list[Error]:
        self.errors = []
        heading_title = section.heading.text.lower()

        if SectionConstant.WORK_EXPERIENCE.lower() in heading_title:
            for line_obj in section.indexed_lines:
                line_str = line_obj.line.strip()
                if line_str.startswith("**") and "_ " in line_str and not RE_WORK_EXP.match(line_str):
                    self.add_error(
                        section,
                        line_obj,
                        f"{section.heading.text} format mismatch",
                    )

        elif SectionConstant.COURSES_AND_CERTIFICATES.lower() in heading_title:
            for line_obj in section.indexed_lines:
                line_str = line_obj.line.strip()
                if not line_str:
                    continue
                if RE_ENDS_WITH_YEAR.search(line_str) and not RE_COURSE_FORMAT.match(line_str):
                    self.add_error(
                        section,
                        line_obj,
                        f"{section.heading.text} format mismatch",
                    )
        return self.errors


def _section_text_with_heading(section: Section) -> str:
    r"""Serialize a section back to markdown, guaranteeing the '#'-heading line `sec_class.from_string` expects.

    Sections built by `split_markdown_into_sections` already carry the heading line as their first
    `indexed_lines` entry, but hand-built `Section` objects (e.g. in tests) often don't - so prepend it
    when missing to avoid `from_string` mistaking the first content line for the heading.

    Also normalizes `\\hfill` back to `|`, since a resume already run through `fix_markdown` persists
    dates as `\\hfill` (see `fix_markdown`'s first line), but the entry models only parse `|`.
    """
    lines = [line.line for line in section.indexed_lines] if section.indexed_lines else []
    if lines and lines[0].strip().startswith("#"):
        text = "\n".join(lines)
    else:
        heading_line = f"{section.heading.heading_prefix} {section.heading.text}".strip()
        text = "\n".join([heading_line, *lines])
    return text.replace("\\hfill", "|")


def _find_line_containing(section: Section, needle: str) -> IndexedLine:
    """Best-effort lookup of the raw line an entry originated from, for error reporting."""
    for line in section.indexed_lines:
        if needle and needle in line.line:
            return line
    if section.indexed_lines:
        return section.indexed_lines[0]
    return IndexedLine(line="", index=1)


class DuplicateEntryCheck(Check):
    """Checks that Work experience / Personal projects / Courses entries aren't duplicated within a section."""

    _DEFAULT_ERROR_MSG = "Duplicate entry found"

    def check(self, section: Section) -> list[Error]:
        self.errors = []
        heading_title = section.heading.text.lower()

        if SectionConstant.WORK_EXPERIENCE.lower() in heading_title:
            self._check_entries(
                section,
                WorkExperience,
                key_fn=lambda e: (e.title.lower(), e.company.lower(), e.duration.to_string().lower()),
                label_fn=lambda e: e.title,
            )
        elif "projects" in heading_title or SectionConstant.PERSONAL_PROJECTS.lower() in heading_title:
            self._check_entries(
                section,
                PersonalProjects,
                key_fn=lambda e: (e.name.lower(), e.url.lower()),
                label_fn=lambda e: e.name,
            )
        elif SectionConstant.COURSES_AND_CERTIFICATES.lower() in heading_title:
            self._check_entries(
                section,
                CourseOrCertificate,
                key_fn=lambda e: (e.name.lower(), e.institution.lower()),
                label_fn=lambda e: e.name,
            )

        return self.errors

    def _check_entries(self, section: Section, sec_class: type[Section], *, key_fn, label_fn) -> None:
        try:
            typed_section = sec_class.from_string(_section_text_with_heading(section), section.filepath)
        except Exception:  # noqa: BLE001
            return

        seen = set()
        for entry in typed_section.entries:
            key = key_fn(entry)
            if key in seen:
                line = _find_line_containing(section, label_fn(entry))
                self.add_error(section, line, f"Duplicate entry in {section.heading.text}: '{label_fn(entry)}'")
            else:
                seen.add(key)


class DuplicateLineCheck(Check):
    """Checks that no non-trivial line is repeated verbatim within a section."""

    _DEFAULT_ERROR_MSG = "Duplicate line found"
    _SKIP_LINES = {"\\hfill", "\\break"}

    def check(self, section: Section) -> list[Error]:
        self.errors = []
        seen: set[str] = set()
        for line in section.indexed_lines:
            stripped = line.line.strip()
            if not stripped or stripped.startswith("#") or stripped in self._SKIP_LINES:
                continue
            if stripped in seen:
                self.add_error(section, line, f"Duplicate line: '{stripped}'")
            else:
                seen.add(stripped)
        return self.errors


class ProjectFormatCheck(Check):
    """Checks that Personal projects entries have all required fields filled in."""

    _DEFAULT_ERROR_MSG = "Personal project entry is incomplete"

    def check(self, section: Section) -> list[Error]:
        self.errors = []
        heading_title = section.heading.text.lower()
        if "projects" not in heading_title and SectionConstant.PERSONAL_PROJECTS.lower() not in heading_title:
            return self.errors

        try:
            typed_section = PersonalProjects.from_string(_section_text_with_heading(section), section.filepath)
        except Exception:  # noqa: BLE001
            return self.errors

        for entry in typed_section.entries:
            line = _find_line_containing(section, entry.name)
            if not entry.name:
                self.add_error(section, line, "Project entry is missing a name")
            if not entry.duration.end_date:
                self.add_error(section, line, f"Project '{entry.name}' is missing a date")
            if not entry.bullet_points:
                self.add_error(section, line, f"Project '{entry.name}' has no bullet points")
            if not entry.skills:
                self.add_error(section, line, f"Project '{entry.name}' has no Skills line")
        return self.errors


class RequiredSectionsCheck:
    """Checks that all required sections exist in the Resume."""

    def check_all(self, sections: list[Section]) -> list[Error]:
        if not sections:
            sec = Section(
                heading=Heading(text="", heading_prefix=""),
                filepath=Path(),
                indexed_lines=[],
            )
        else:
            sec = sections[0]

        section_names = [s.heading.text.lower() for s in sections if s.heading.text]
        required_headers = [
            SectionConstant.WORK_EXPERIENCE.lower(),
            SectionConstant.PERSONAL_PROJECTS.lower(),
            SectionConstant.COURSES_AND_CERTIFICATES.lower(),
        ]

        dummy_line = IndexedLine(line="", index=1)

        return [
            make_error(f"Missing '{req}' section in headers", sec, dummy_line)
            for req in required_headers
            if not any(
                req in name or (req == SectionConstant.PERSONAL_PROJECTS.lower() and "projects" in name)
                for name in section_names
            )
        ]


class SectionNotEmptyCheck:
    """Checks that required sections which are present in the headers actually contain at least one entry."""

    _SECTION_CLASSES = {
        SectionConstant.PERSONAL_PROJECTS.lower(): PersonalProjects,
        SectionConstant.COURSES_AND_CERTIFICATES.lower(): CourseOrCertificate,
    }

    def check_all(self, sections: list[Section]) -> list[Error]:
        errors = []
        for section in sections:
            heading_title = section.heading.text.lower()
            for name, sec_class in self._SECTION_CLASSES.items():
                is_match = name in heading_title or (sec_class is PersonalProjects and "projects" in heading_title)
                if not is_match:
                    continue
                try:
                    typed_section = sec_class.from_string(_section_text_with_heading(section), section.filepath)
                except Exception:  # noqa: BLE001, S112
                    continue
                if not typed_section.entries:
                    line = section.indexed_lines[0] if section.indexed_lines else IndexedLine(line="", index=1)
                    errors.append(make_error(f"'{section.heading.text}' section has no entries", section, line))
        return errors


def get_section_class(section: Section) -> type[Section]:
    """Determine the Section subclass corresponding to a generic Section name/prefix."""
    if is_root_section(section):
        return Info

    name_lower = section.heading.text.lower()
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
        DuplicateEntryCheck,
        DuplicateLineCheck,
        ProjectFormatCheck,
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


def check(sections: list[Section], *, is_resume: bool = False) -> list[Error]:
    """Run all validation checkers on the provided sections based on _CHECK_CONFIG."""
    errors = []

    for section in sections:
        sec_class = get_section_class(section)
        check_classes = _CHECK_CONFIG.get(sec_class, _CHECK_CONFIG.get(Section, []))

        for check_class in check_classes:
            checker = check_class()
            errors.extend(checker.check(section))

    if is_resume:
        errors.extend(RequiredSectionsCheck().check_all(sections))
        errors.extend(SectionNotEmptyCheck().check_all(sections))
    return errors


def check_and_get_errors(markdown: str, *, is_resume: bool = False) -> list[Error]:
    """Check markdown string and return a list of Error objects."""
    sections = split_markdown_into_sections(markdown)
    return check(sections, is_resume=is_resume)
