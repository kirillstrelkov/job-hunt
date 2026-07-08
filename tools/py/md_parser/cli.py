"""CLI tool for parsing CV markdown files and checking validation errors."""

import sys
from pathlib import Path

from pydantic import ValidationError

from md_parser.parse import parse


def main() -> None:
    """CLI entrypoint to parse CV markdown file and report errors."""
    if len(sys.argv) < 2:  # noqa: PLR2004
        print("Usage: uv run python md_parser/cli.py <path_to_markdown_file>")  # noqa: T201
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File '{filepath}' does not exist.")  # noqa: T201
        sys.exit(1)

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}")  # noqa: T201
        sys.exit(1)

    try:
        cv_obj = parse(content)
        print(f"Successfully parsed CV from {filepath}!")  # noqa: T201
        body = cv_obj.body
        print(f"  Header present: {cv_obj.header is not None}")  # noqa: T201
        print(f"  Work experiences: {len(body.work_experience)}")  # noqa: T201
        print(f"  Personal projects: {len(body.personal_projects)}")  # noqa: T201
        print(f"  Courses & Certificates: {len(body.courses_and_certificates)}")  # noqa: T201
        print(f"  Footer present: {cv_obj.footer is not None}")  # noqa: T201
    except ValidationError as ve:
        print(f"Validation errors encountered in {filepath}:")  # noqa: T201
        for err in ve.errors():
            loc = " -> ".join(str(field_loc) for field_loc in err["loc"])
            msg = err["msg"]
            print(f"  - Field '{loc}': {msg}")  # noqa: T201
        sys.exit(1)
    except Exception as e:
        print(f"Parsing errors encountered in {filepath}: {e}")  # noqa: T201
        sys.exit(1)


if __name__ == "__main__":
    main()
