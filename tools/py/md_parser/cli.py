import os
import sys
from pydantic import ValidationError
from md_parser.parse import parse


def main() -> None:
    """CLI entrypoint to parse CV markdown file and report errors."""
    if len(sys.argv) < 2:
        print("Usage: uv run python md_parser/cli.py <path_to_markdown_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' does not exist.")
        sys.exit(1)

    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:  # noqa: BLE001
        print(f"Error reading file: {e}")
        sys.exit(1)

    try:
        cv_obj = parse(content)
        print(f"Successfully parsed CV from {filepath}!")
        body = cv_obj.body
        print(f"  Header present: {cv_obj.header is not None}")
        print(f"  Work experiences: {len(body.work_experience)}")
        print(f"  Personal projects: {len(body.personal_projects)}")
        print(f"  Courses & Certificates: {len(body.courses_and_certificates)}")
        print(f"  Footer present: {cv_obj.footer is not None}")
    except ValidationError as ve:
        print(f"Validation errors encountered in {filepath}:")
        for err in ve.errors():
            loc = " -> ".join(str(l) for l in err["loc"])
            msg = err["msg"]
            print(f"  - Field '{loc}': {msg}")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"Parsing errors encountered in {filepath}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
