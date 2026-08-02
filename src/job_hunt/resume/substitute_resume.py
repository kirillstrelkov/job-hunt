"""Filter markdown resume files and replace header/footer sections.

Scans *.md files in a folder (or a single markdown file), filters for full resumes that:
- Start with a single `# ` heading
- Contain `## Summary`, `## Work Experience`, and `## Education` sections

Replaces everything before `## Summary` with `--header` content,
and everything from/including `## Education` with `--footer` content.

Usage:
  python substitute_resume.py <input> <output> --header <header_path> --footer <footer_path>
"""

import re
from pathlib import Path

from loguru import logger


def is_full_resume(content: str) -> bool:
    """Check if the markdown content matches full resume criteria."""
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return False

    # Must start with a single '#' heading (e.g. '# John Doe')
    first_line = lines[0]
    if not first_line.startswith("# ") or first_line.startswith("##"):
        return False

    # Must contain required section headings
    has_summary = bool(re.search(r"^##\s+Summary\b", content, re.MULTILINE | re.IGNORECASE))
    has_work_exp = bool(re.search(r"^##\s+Work Experience\b", content, re.MULTILINE | re.IGNORECASE))
    has_education = bool(re.search(r"^##\s+Education\b", content, re.MULTILINE | re.IGNORECASE))

    return has_summary and has_work_exp and has_education


def replace_resume_header_footer(content: str, header_content: str, footer_content: str) -> str:
    """Replace content before ## Summary with header_content, and content from ## Education with footer_content."""
    summary_match = re.search(r"^##\s+Summary\b", content, re.MULTILINE | re.IGNORECASE)
    education_match = re.search(r"^##\s+Education\b", content, re.MULTILINE | re.IGNORECASE)

    if not summary_match or not education_match:
        msg = "Content missing required '## Summary' or '## Education' sections."
        raise ValueError(msg)

    summary_idx = summary_match.start()
    education_idx = education_match.start()

    if summary_idx >= education_idx:
        msg = "'## Summary' section must appear before '## Education' section."
        raise ValueError(msg)

    body_part = content[summary_idx:education_idx].rstrip()

    header_clean = header_content.strip()
    footer_clean = footer_content.strip()

    return f"{header_clean}\n\n{body_part}\n\n{footer_clean}\n"


def process_files(input_path: Path, output_path: Path, header_path: Path, footer_path: Path) -> list[Path]:
    """Process markdown input file(s) and write output to output_path."""
    if not input_path.exists():
        msg = f"Input path does not exist: {input_path}"
        raise FileNotFoundError(msg)
    if not header_path.is_file():
        msg = f"Header file does not exist: {header_path}"
        raise FileNotFoundError(msg)
    if not footer_path.is_file():
        msg = f"Footer file does not exist: {footer_path}"
        raise FileNotFoundError(msg)

    header_content = header_path.read_text(encoding="utf-8")
    footer_content = footer_path.read_text(encoding="utf-8")

    processed_files: list[Path] = []

    if input_path.is_file():
        md_files = [input_path]
        is_single_file_mode = True
    else:
        md_files = sorted(list(input_path.glob("*.md")) + list(input_path.glob("*.MD")))
        is_single_file_mode = False

    for file in md_files:
        try:
            content = file.read_text(encoding="utf-8")
        except Exception as err:
            logger.warning("Skipping {}: Error reading file ({})", file, err)
            continue

        if not is_full_resume(content):
            logger.info("Skipping {}: Does not match full resume criteria.", file)
            continue

        try:
            new_content = replace_resume_header_footer(content, header_content, footer_content)
        except Exception as err:
            logger.error("Error processing {}: {}", file, err)
            continue

        # Determine output file location
        if is_single_file_mode and not output_path.is_dir() and (output_path.suffix or not output_path.exists()):
            target_file = output_path
        else:
            output_path.mkdir(parents=True, exist_ok=True)
            target_file = output_path / file.name

        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(new_content, encoding="utf-8")
        processed_files.append(target_file)
        logger.info("Processed: {} -> {}", file, target_file)

    return processed_files


def main(src: Path, output: Path, header: Path, footer: Path) -> None:
    """Execute resume filtering and replacement."""
    processed = process_files(src, output, header, footer)
    logger.info("Successfully processed {} resume file(s).", len(processed))
