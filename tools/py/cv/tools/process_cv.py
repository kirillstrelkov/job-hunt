"""Check and fix CV markdown formatting and chronological consistency."""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

# TODO: create tests to check:
# ". " at the end of lines should be remove everywhere except Summary
# "  " two spaces should be removed with do_fix and add "  " in seconds where it is needed - Certificates

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
_CUR_YEAR = datetime.now(UTC).year


@dataclass
class Line:
    """Represents a single line from the CV with its content and line number."""

    raw_line: str
    number: int


@dataclass
class Section:
    """Represents a CV section under a specific header."""

    name: str | None
    filepath: str
    lines: list[Line]


@dataclass
class Error:
    """Represents a validation error found in the CV."""

    msg: str
    filepath: str
    line_num: int
    line: str


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for CV checking and fixing."""
    parser = argparse.ArgumentParser(description="Check and fix CV markdown file.")
    parser.add_argument("file", type=str, help="Path to the markdown file")
    parser.add_argument("--check", action="store_true", help="Check the file for errors")
    parser.add_argument("--keep-thesis", action="store_true", help="Keep thesis name")
    parser.add_argument("--fix", action="store_true", help="Fix the errors in the file")
    return parser.parse_args()


def split_markdown_into_sections(md: str, filepath: str = "CV.md") -> list[Section]:
    """Parse the CV markdown string and split it into sections based on markdown headers."""
    lines_raw = md.splitlines()
    sections = []
    cur_section = None

    for i, raw_line in enumerate(lines_raw):
        if RE_HEADING.match(raw_line):
            if cur_section is not None:
                sections.append(cur_section)
                cur_section = None

            name = raw_line.lstrip("#").strip().lower()
            cur_section = Section(name=name, filepath=filepath, lines=[])

        if cur_section:
            line = Line(raw_line=raw_line, number=i + 1)
            cur_section.lines.append(line)

    sections.append(cur_section)

    return [s for s in sections if s is not None]


def split_into_sections(filepath: str) -> list[Section]:
    """Parse the CV file and split it into sections based on markdown headers."""
    with Path(filepath).open("r", encoding="utf-8") as f:
        content = f.read()
    return split_markdown_into_sections(content, filepath=filepath)


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


def do_check(sections: list[Section]) -> list[Error]:  # noqa: C901, PLR0912, PLR0915
    """Run validation checks on the CV sections to identify structural or chronological errors."""
    errors = []

    def check_chronological(line_and_dates: list, section: Section, *, double_error: bool = False) -> None:
        for i in range(len(line_and_dates) - 1):
            line1_obj, (key1, _, line_str1) = line_and_dates[i]
            line2_obj, (key2, _, line_str2) = line_and_dates[i + 1]
            if key1 < key2:
                errors.append(
                    Error(
                        msg=f"Chronological order broken in {section.name}: '{line_str1}' is before '{line_str2}'",
                        filepath=section.filepath,
                        line_num=line1_obj.number,
                        line=line1_obj.raw_line,
                    )
                )
                if double_error:
                    errors.append(
                        Error(
                            msg=f"Chronological order broken in {section.name}: '{line_str2}' is after '{line_str1}'",
                            filepath=section.filepath,
                            line_num=line2_obj.number,
                            line=line2_obj.raw_line,
                        )
                    )

    def add_entry(lst: list, line_obj: Line, date_str: str, line_str: str) -> None:
        skey = get_sort_key(date_str)
        lst.append((line_obj, (skey, date_str, line_str)))

    for section in sections:
        heading_title = section.name.lower()

        if "work experience" in heading_title:
            line_and_dates = []
            for line_obj in section.lines:
                line_str = line_obj.raw_line.strip()
                if line_str.startswith("**") and "_ " in line_str:
                    if not RE_WORK_EXP.match(line_str):
                        errors.append(
                            Error(
                                msg=f"{section.name} format mismatch",
                                filepath=section.filepath,
                                line_num=line_obj.number,
                                line=line_obj.raw_line,
                            )
                        )
                    else:
                        date_str = RE_PIPE_SPLIT.split(line_str)[-1].strip()
                        add_entry(line_and_dates, line_obj, date_str, line_str)

            check_chronological(line_and_dates, section)

        elif "courses and certificates" in heading_title:
            line_and_dates = []
            for line_obj in section.lines:
                line_str = line_obj.raw_line.strip()
                if not line_str:
                    continue
                if RE_ENDS_WITH_YEAR.search(line_str):
                    if not RE_COURSE_FORMAT.match(line_str):
                        errors.append(
                            Error(
                                msg=f"{section.name} format mismatch",
                                filepath=section.filepath,
                                line_num=line_obj.number,
                                line=line_obj.raw_line,
                            )
                        )
                        parts = RE_PIPE_SPLIT.split(line_str)
                        if len(parts) >= 2:  # noqa: PLR2004
                            date_str = parts[-1].strip()
                        else:
                            match = RE_COURSE_DATE.search(line_str)
                            date_str = match.group(1) if match else line_str
                        add_entry(line_and_dates, line_obj, date_str, line_str)
                    else:
                        date_str = RE_PIPE_SPLIT.split(line_str)[-1].strip()
                        add_entry(line_and_dates, line_obj, date_str, line_str)

            check_chronological(line_and_dates, section)

        elif "projects" in heading_title:
            line_and_dates = []
            for line_obj in section.lines:
                line_str = line_obj.raw_line.strip()
                if line_str.startswith("**["):
                    date_str = RE_PIPE_SPLIT.split(line_str)[-1].strip()
                    add_entry(line_and_dates, line_obj, date_str, line_str)

            check_chronological(line_and_dates, section, double_error=True)

    filepath = sections[0].filepath if sections else ""
    section_names = [s.name.lower() for s in sections if s.name]
    required_headers = ["work experience", "projects", "courses and certificates"]

    errors.extend(
        Error(
            msg=f"Missing '{req}' section in headers",
            filepath=filepath,
            line_num=1,
            line="",
        )
        for req in required_headers
        if not any(req in name for name in section_names)
    )

    return errors


def _fix_skills_section(section: Section) -> None:
    if section.name.lower() != "skills":
        return

    new_lines = []
    for line_obj in section.lines:
        line_str = line_obj.raw_line
        # fix markdown new flie with 2 spaces at the end
        if (line_str.startswith("**") or ":" in line_str) and not line_str.endswith("  "):
            line_obj.raw_line = line_str.rstrip() + "  "

        new_lines.append(line_obj)

    section.lines = new_lines


def do_fix(sections: list[Section], *, keep_thesis: bool = True) -> list[Section]:  # noqa: C901
    """Apply sorting, formatting and structure fixes to CV sections."""
    if not keep_thesis:
        logger.warning("Thesis will be removed")

    for section in sections:
        heading_title = section.name.lower()
        if heading_title == "skills":
            _fix_skills_section(section)
            continue

        filtered_lines = []
        for line_obj in section.lines:
            if not keep_thesis and line_obj.raw_line.strip().startswith("- Thesis"):
                continue

            line_str = line_obj.raw_line
            for full_m_re, short_m in MONTHS_TO_SHORT_RE.items():
                line_str = full_m_re.sub(short_m, line_str)

            if "work experience" in heading_title or "projects" in heading_title:
                line_str = RE_TRAILING_DOT.sub(r"\1", line_str)

            if "courses and certificates" in heading_title:
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

        section.lines = filtered_lines

    return sections


def check_file(filepath: str) -> None:
    """Run verification checks on a CV file path."""
    logger.debug("Checking file {}", filepath)

    sections = split_into_sections(filepath)
    errors = do_check(sections)
    if errors:
        logger.error("Found {} errors", len(errors))
        for err in errors:
            logger.error(f"{err.msg}\n{err.filepath}:{err.line_num}: `{err.line}`")
        sys.exit(1)
    logger.info("No errors found")


def fix_file(filepath: str, *, keep_thesis: bool = True) -> None:
    """Apply auto-formatting and structure fixes to a CV file path."""
    logger.debug("Fixing file {}", filepath)

    sections = split_into_sections(filepath)
    do_fix(sections, keep_thesis=keep_thesis)
    with Path(filepath).open("w", encoding="utf-8") as f:
        for section in sections:
            f.writelines(line_obj.raw_line + "\n" for line_obj in section.lines)
    logger.info("Fixes applied and file written")


def check_markdown(md: str, *, filepath: str = "CV.md") -> list[Error]:
    """Run verification checks on a CV markdown string, returning a list of Error objects."""
    sections = split_markdown_into_sections(md, filepath=filepath)
    return do_check(sections)


def fix_markdown(md: str, *, keep_thesis: bool = True) -> str:
    """Apply auto-formatting and structure fixes to a CV markdown string, returning the fixed string."""
    sections = split_markdown_into_sections(md)
    do_fix(sections, keep_thesis=keep_thesis)
    output_lines = []
    for section in sections:
        output_lines.extend(line_obj.raw_line for line_obj in section.lines)
    return "\n".join(output_lines) + ("\n" if output_lines else "")


def main() -> None:
    """Main CLI entry point for checking and fixing CV files."""
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
