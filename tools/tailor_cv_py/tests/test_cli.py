from typer.testing import CliRunner

from tailor_cv.cli import app

runner = CliRunner()


def test_invalid_output_extension(tmp_path):
    cv = tmp_path / "cv.txt"
    jd = tmp_path / "jd.txt"
    cv.write_text("CV content", encoding="utf-8")
    jd.write_text("Job description", encoding="utf-8")

    result = runner.invoke(app, ["-i", str(cv), "-j", str(jd), "-o", "out.docx"])

    assert result.exit_code != 0
    assert ".md or .pdf" in result.output


def test_valid_md_extension_accepted(tmp_path, mocker):
    cv = tmp_path / "cv.txt"
    jd = tmp_path / "jd.txt"
    out = tmp_path / "out.md"
    cv.write_text("CV content", encoding="utf-8")
    jd.write_text("Job description", encoding="utf-8")
    mocker.patch("tailor_cv.cli.call_ollama", return_value="# Tailored CV")

    result = runner.invoke(app, ["-i", str(cv), "-j", str(jd), "-o", str(out)])

    assert result.exit_code == 0
    content = out.read_text()
    assert "# Tailored CV" in content
    assert "Name Lastname" in content   # default header present
    assert "Education" in content       # default footer present


def test_cov_flag_generates_cover_letter(tmp_path, mocker):
    cv = tmp_path / "cv.txt"
    jd = tmp_path / "jd.txt"
    out = tmp_path / "out.md"
    cv.write_text("CV content", encoding="utf-8")
    jd.write_text("Job description", encoding="utf-8")
    mocker.patch(
        "tailor_cv.cli.call_ollama",
        side_effect=["# Tailored CV", "Dear Hiring Manager..."],
    )

    result = runner.invoke(app, ["-i", str(cv), "-j", str(jd), "-o", str(out), "--cov"])

    assert result.exit_code == 0
    assert "# Tailored CV" in out.read_text()
    cover = tmp_path / "out_cover.md"
    assert cover.read_text() == "Dear Hiring Manager..."


def test_custom_header_footer(tmp_path, mocker):
    cv = tmp_path / "cv.txt"
    jd = tmp_path / "jd.txt"
    out = tmp_path / "out.md"
    header = tmp_path / "header.md"
    footer = tmp_path / "footer.md"
    cv.write_text("CV content", encoding="utf-8")
    jd.write_text("Job description", encoding="utf-8")
    header.write_text("# John Doe\n", encoding="utf-8")
    footer.write_text("## Education\nBSc CS\n", encoding="utf-8")
    mocker.patch("tailor_cv.cli.call_ollama", return_value="## Experience")

    result = runner.invoke(
        app, ["-i", str(cv), "-j", str(jd), "-o", str(out), "--header", str(header), "--footer", str(footer)]
    )

    assert result.exit_code == 0
    content = out.read_text()
    assert "# John Doe" in content
    assert "## Experience" in content
    assert "BSc CS" in content
