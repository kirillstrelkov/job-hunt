"""Parser logic to convert markdown text into structured Pydantic models."""

import re
from pathlib import Path

from md_tools.models import CV, Line, Section


def split_markdown_into_sections(md: str, filepath: Path | None = None) -> list[Section]:
    """Parse the CV markdown string and split it into sections based on markdown headers."""
    lines_raw = md.splitlines()
    sections = []
    cur_section = None

    for i, raw_line in enumerate(lines_raw):
        if raw_line.startswith("#"):
            if cur_section is not None:
                sections.append(cur_section)
                cur_section = None

            header_match = re.match(r"^(#+)\s*(.*)$", raw_line)
            if header_match:
                prefix = header_match.group(1)
                name = header_match.group(2).strip()
            else:
                prefix = "#"
                name = raw_line.lstrip("#").strip()

            line = Line(raw_line=raw_line, number=i + 1)
            cur_section = Section(
                name=name, md_prefix=prefix, filepath=filepath or Path("/tmp/dummy"), raw_lines=[line]
            )
        elif cur_section:
            line = Line(raw_line=raw_line, number=i + 1)
            cur_section.raw_lines.append(line)

    if cur_section is not None:
        sections.append(cur_section)

    return sections


def parse(text: str) -> CV:
    """Parse CV markdown text into a CV Pydantic model.

    Args:
        text: The raw markdown content of the CV.

    Returns:
        CV: The parsed CV Pydantic model.

    """
    return CV.from_string(text)
