from pathlib import Path
from unittest.mock import patch

import pytest

from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.resume.compose_resume import compose_resume
from job_hunt.resume.models import Footer, Header

LLM_RESPONSE = """Some preamble the model shouldn't have written.

## Summary

Test Engineer with hands-on experience in Python automation.

## Skills

**Languages**: Python, Java

## Work experience

**QA Engineer** | _TestCorp, Berlin, Germany_ | Jan 2022 - Present

- Automated regression tests using Selenium and pytest
- Skills: Python, Selenium, pytest

## Personal projects

**[Test Framework](https://github.com/johndoe/test-fw)** | Jan 2023

- Built an automation framework for API testing
- Skills: Python, pytest

## Courses and certificates

- ISTQB Certified Tester | _ISTQB_ | 2021

TAILORING JUSTIFICATION REPORT

This section should be trimmed away and never reach the final Resume.
"""


@pytest.fixture
def job_folder(tmp_path: Path) -> Path:
    """Job folder with a jd.txt; header/body/footer/prompt come from the default config."""
    folder = tmp_path / "job"
    folder.mkdir()
    (folder / "jd.txt").write_text("QA Engineer role requiring Python and Selenium skills.", encoding="utf-8")
    return folder


@patch("job_hunt.resume.compose_resume.check_pdf")
@patch("job_hunt.resume.compose_resume.convert_md_to_pdf")
@patch("job_hunt.resume.compose_resume.decide_keep_thesis")
@patch("job_hunt.resume.compose_resume.run_ollama")
def test_compose_resume_pipeline_includes_header_and_footer(
    mock_run_ollama,
    mock_decide_keep_thesis,
    mock_convert_md_to_pdf,
    mock_check_pdf,
    job_folder: Path,
) -> None:
    """Run the full compose_resume pipeline with the LLM and PDF conversion mocked out."""
    mock_run_ollama.return_value = {"gen_tokens": 200, "response": LLM_RESPONSE}
    mock_decide_keep_thesis.return_value = True
    mock_check_pdf.return_value = []

    compose_resume(folder=str(job_folder), model="mock-model", force=True)

    assembled_resume = job_folder / "gen" / "resume-mock-model.md"
    assert assembled_resume.exists()
    content = assembled_resume.read_text(encoding="utf-8")

    # Header content (from the default config's header.md) survived the pipeline.
    expected_header = Header.from_string(DEFAULT_CONFIG.composer.header.read_text(encoding="utf-8"))
    assert expected_header.name in content
    assert expected_header.email in content

    # Tailored body content (from the mocked LLM) survived the pipeline.
    assert "QA Engineer" in content
    assert "Test Engineer with hands-on experience in Python automation." in content

    # Footer content (from the default config's footer.md) survived the pipeline.
    expected_footer = Footer.from_string(DEFAULT_CONFIG.composer.footer.read_text(encoding="utf-8"))
    assert expected_footer.educations[0].institution in content
    assert all(lang.name in content for lang in expected_footer.languages)

    # Content the LLM produced after the justification marker must not leak into the Resume.
    assert "TAILORING JUSTIFICATION REPORT" not in content
    assert "should be trimmed away" not in content

    # PDF conversion and layout check were invoked as the final pipeline steps.
    pdf_output = job_folder / "gen" / "resume-mock-model.pdf"
    mock_convert_md_to_pdf.assert_called_once_with(assembled_resume, pdf_output)
    mock_check_pdf.assert_called_once_with(pdf_output)
