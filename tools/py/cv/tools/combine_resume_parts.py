"""Combine CV header, body, and footer markdown parts into a single document."""

import argparse
from pathlib import Path

DEFAULT_SEPARATOR = "\n\n"


def combine_resume_parts(header: str, body: str, footer: str, *, separator: str = DEFAULT_SEPARATOR) -> str:
    """Join header, body, and footer markdown strings into one CV document."""
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


def main() -> None:
    """CLI entrypoint to combine CV header, body, and footer markdown files."""
    parser = argparse.ArgumentParser(description="Combine CV header, body, and footer markdown files.")
    parser.add_argument("--header", required=True, type=Path)
    parser.add_argument("--body", required=True, type=Path)
    parser.add_argument("--footer", required=True, type=Path)
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output path; prints to stdout if omitted.")
    args = parser.parse_args()

    combined = combine_resume_part_files(args.header, args.body, args.footer)
    if args.output:
        args.output.write_text(combined, encoding="utf-8")
    else:
        print(combined)  # noqa: T201


if __name__ == "__main__":
    main()
