import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import pytest

from job_hunt.resume.check_pdf import _page_visual_fill, check_pdf, get_pdf_page_count

XHTML_NS = "http://www.w3.org/1999/xhtml"


def make_page(height: float, lines: list[tuple[float, float]]) -> ET.Element:
    line_tags = "".join(f'<line xmlns="{XHTML_NS}" yMin="{y_min}" yMax="{y_max}"/>' for y_min, y_max in lines)
    xml = f'<page xmlns="{XHTML_NS}" height="{height}">{line_tags}</page>'
    return ET.fromstring(xml)  # noqa: S314


def test_get_pdf_page_count_missing_file(tmp_path: Path) -> None:
    assert get_pdf_page_count(tmp_path / "missing.pdf") == 0


def test_get_pdf_page_count_regex_fallback(tmp_path: Path) -> None:
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"not a real pdf /Type /Page ... /Type /Page")
    assert get_pdf_page_count(fake_pdf) == 2


def test_page_visual_fill_excludes_footer_line() -> None:
    page = make_page(height=841.89, lines=[(50, 60), (70, 80), (90, 100), (820, 830)])
    fill = _page_visual_fill(page)

    assert fill["top_margin"] == 50
    assert fill["body_bottom"] == 100  # footer line at y=820-830 dropped
    assert fill["fill_pct"] == pytest.approx(100 / (841.89 - 50) * 100)


def test_page_visual_fill_no_lines() -> None:
    page = make_page(height=841.89, lines=[])
    fill = _page_visual_fill(page)
    assert fill["fill_pct"] == 0.0


def test_check_pdf_wrong_page_count(tmp_path: Path) -> None:
    errors = check_pdf(tmp_path / "missing.pdf")
    assert len(errors) == 1
    assert "Expected exactly 2 pages, found 0" in errors[0]


def test_check_pdf_fill_threshold_success(tmp_path: Path) -> None:
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"fake")

    mock_fill_result = {
        "pages": 2,
        "pages_detail": [{"page": 1, "filled": True}, {"page": 2, "filled": True}],
        "fill_p1": 90.0,
        "fill_p2": 95.0,
        "measured": True,
        "measure_error": None,
        "is_filled": True,
    }

    with patch("job_hunt.resume.check_pdf.check_pdf_page_fill", return_value=mock_fill_result):
        errors = check_pdf(fake_pdf)
        assert errors == []


def test_check_pdf_fill_threshold_failure(tmp_path: Path) -> None:
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"fake")

    mock_fill_result = {
        "pages": 2,
        "pages_detail": [{"page": 1, "filled": True}, {"page": 2, "filled": False}],
        "fill_p1": 91.0,
        "fill_p2": 89.9,
        "measured": True,
        "measure_error": None,
        "is_filled": False,
    }

    with patch("job_hunt.resume.check_pdf.check_pdf_page_fill", return_value=mock_fill_result):
        errors = check_pdf(fake_pdf)
        assert len(errors) == 1
        assert ">= 90% filled" in errors[0]
        assert "page 1 = 91.0%" in errors[0]
        assert "page 2 = 89.9%" in errors[0]
