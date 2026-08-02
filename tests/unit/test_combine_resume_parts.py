from pathlib import Path

from job_hunt.resume.combine_resume_parts import combine_resume_part_files, combine_resume_parts


def test_combine_resume_parts_default_separator() -> None:
    combined = combine_resume_parts("# Header", "## Body", "Footer text")
    assert combined == "# Header\n\n## Body\n\nFooter text"


def test_combine_resume_parts_custom_separator() -> None:
    combined = combine_resume_parts("Header", "Body", "Footer", separator="\n")
    assert combined == "Header\nBody\nFooter"


def test_combine_resume_part_files(tmp_path: Path) -> None:
    header_path = tmp_path / "header.md"
    body_path = tmp_path / "body.md"
    footer_path = tmp_path / "footer.md"
    header_path.write_text("# John Doe", encoding="utf-8")
    body_path.write_text("## Work experience", encoding="utf-8")
    footer_path.write_text("## Education", encoding="utf-8")

    combined = combine_resume_part_files(header_path, body_path, footer_path)

    assert combined == "# John Doe\n\n## Work experience\n\n## Education"
