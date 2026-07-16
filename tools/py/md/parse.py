"""Parser logic to convert markdown text into structured Pydantic models."""

import re
from pathlib import Path

from pydantic import BaseModel, Field

_TMP_MARKDOWN_FILE = Path("/tmp/dummy")
_REGEXP_HEADER_GROUP = re.compile(r"^(#+)\s*(.*)\s*$")


class IndexedLine(BaseModel):
    """Represents a single line from the CV with its content and line index."""

    line: str
    index: int


class Heading(BaseModel):
    """Represents a heading from the CV."""

    text: str
    heading_prefix: str


class Section(BaseModel):
    """Base Pydantic model representing a structured section of a CV."""

    heading: Heading = Field(...)
    filepath: Path | None = Field(default_factory=lambda: _TMP_MARKDOWN_FILE)
    indexed_lines: list[IndexedLine] | None = Field(default_factory=list)

    @property
    def lines(self) -> list[str]:
        """Return the lines of the section."""
        return [il.line for il in self.indexed_lines]

    def __str__(self) -> str:
        """Return the section as a string."""
        return "\n".join(self.lines)


def split_markdown_into_sections(md: str, filepath: Path | None = None) -> list[Section]:
    """Parse the CV markdown string and split it into sections based on markdown headers."""
    lines_raw = md.splitlines()
    sections = []
    cur_section = None
    filepath = filepath or _TMP_MARKDOWN_FILE

    for i, raw_line in enumerate(lines_raw):
        if raw_line.startswith("#"):
            if cur_section is not None:
                if "\n".join([l.line for l in cur_section.indexed_lines]).strip() and cur_section.heading.text:
                    # skip sections with empty content
                    sections.append(cur_section)

                cur_section = None

            header_match = _REGEXP_HEADER_GROUP.match(raw_line)
            if header_match:
                prefix = header_match.group(1)
                name = header_match.group(2).strip()
            else:
                prefix = "#"
                name = raw_line.lstrip("#").strip()

            line = IndexedLine(line=raw_line, index=i + 1)
            cur_section = Section(
                heading=Heading(text=name, heading_prefix=prefix),
                filepath=filepath,
                indexed_lines=[line],
            )
        else:
            if cur_section is None:
                cur_section = Section(
                    heading=Heading(text="", heading_prefix=""),
                    filepath=filepath,
                    indexed_lines=[],
                )
            line = IndexedLine(line=raw_line, index=i + 1)
            cur_section.indexed_lines.append(line)

    if cur_section is not None:
        sections.append(cur_section)

    return sections
