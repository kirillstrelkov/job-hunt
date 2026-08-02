"""Combine Resume header, body, and footer markdown parts into a single document."""

from pathlib import Path

DEFAULT_SEPARATOR = "\n\n"


def combine_resume_parts(header: str, body: str, footer: str, *, separator: str = DEFAULT_SEPARATOR) -> str:
    """Join header, body, and footer markdown strings into one Resume document."""
    return separator.join([header, body, footer])


def combine_resume_part_files(
    header_path: Path,
    body_path: Path,
    footer_path: Path,
    *,
    separator: str = DEFAULT_SEPARATOR,
) -> str:
    """Read header/body/footer files and combine their contents."""
    return combine_resume_parts(
        header_path.read_text(encoding="utf-8"),
        body_path.read_text(encoding="utf-8"),
        footer_path.read_text(encoding="utf-8"),
        separator=separator,
    )
