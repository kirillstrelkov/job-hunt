from pathlib import Path
import pytest

from job_hunt.resume.filter_and_replace_resume import (
    is_full_resume,
    process_files,
    replace_resume_header_footer,
)


def test_is_full_resume_valid() -> None:
    valid_md = """# John Doe

## Summary
Experienced engineer.

## Work Experience
- Software Developer at ACME.

## Education
- BS Computer Science.
"""
    assert is_full_resume(valid_md) is True


def test_is_full_resume_missing_heading() -> None:
    # Missing single '#' header
    no_h1 = """## John Doe

## Summary
Summary text

## Work Experience
Work text

## Education
Education text
"""
    assert is_full_resume(no_h1) is False


def test_is_full_resume_missing_required_section() -> None:
    missing_summary = """# John Doe

## Work Experience
Work text

## Education
Education text
"""
    assert is_full_resume(missing_summary) is False


def test_replace_resume_header_footer() -> None:
    original = """# Old Header
Contact: old@email.com

## Summary
Strong problem solver.

## Work Experience
- Built systems.

## Education
- Degree in CS.
"""
    new_header = "# New Header\nEmail: new@email.com"
    new_footer = "## Education\n- MS Computer Science\n\n## Skills\n- Python"

    result = replace_resume_header_footer(original, new_header, new_footer)

    expected = """# New Header
Email: new@email.com

## Summary
Strong problem solver.

## Work Experience
- Built systems.

## Education
- MS Computer Science

## Skills
- Python
"""
    assert result == expected


def test_process_files_directory_mode(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    header_file = tmp_path / "header.md"
    footer_file = tmp_path / "footer.md"
    header_file.write_text("# Header Content", encoding="utf-8")
    footer_file.write_text("## Education\n- Stanford", encoding="utf-8")

    resume1 = input_dir / "cv1.md"
    resume1.write_text(
        "# Candidate One\n\n## Summary\nSum 1\n\n## Work Experience\nExp 1\n\n## Education\nEdu 1",
        encoding="utf-8",
    )

    non_resume = input_dir / "notes.md"
    non_resume.write_text("# Just Notes\nNo summary here.", encoding="utf-8")

    processed = process_files(input_dir, output_dir, header_file, footer_file)

    assert len(processed) == 1
    assert (output_dir / "cv1.md").exists()
    assert not (output_dir / "notes.md").exists()

    content = (output_dir / "cv1.md").read_text(encoding="utf-8")
    assert "# Header Content" in content
    assert "## Summary\nSum 1" in content
    assert "## Work Experience\nExp 1" in content
    assert "## Education\n- Stanford" in content


def test_process_files_single_file_mode(tmp_path: Path) -> None:
    input_file = tmp_path / "cv.md"
    output_file = tmp_path / "processed_cv.md"
    header_file = tmp_path / "header.md"
    footer_file = tmp_path / "footer.md"

    header_file.write_text("# New Header", encoding="utf-8")
    footer_file.write_text("## Education\n- New Edu", encoding="utf-8")
    input_file.write_text(
        "# Candidate\n\n## Summary\nSummary\n\n## Work Experience\nWork\n\n## Education\nOld Edu",
        encoding="utf-8",
    )

    processed = process_files(input_file, output_file, header_file, footer_file)

    assert len(processed) == 1
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "# New Header" in content
    assert "## Education\n- New Edu" in content
