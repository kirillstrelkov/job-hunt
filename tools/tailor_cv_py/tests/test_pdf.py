from unittest.mock import MagicMock

import pytest

from tailor_cv.pdf import convert_to_pdf


def test_convert_to_pdf_calls_pandoc(mocker):
    mock_run = mocker.patch("tailor_cv.pdf.subprocess.run")
    mock_run.return_value = MagicMock(returncode=0, stderr="")

    convert_to_pdf("input.md", "output.pdf")

    mock_run.assert_called_once_with(
        [
            "pandoc", "-f", "gfm", "-t", "pdf",
            "-V", "geometry:margin=1.5cm",
            "input.md", "-o", "output.pdf",
        ],
        capture_output=True,
        text=True,
    )


def test_convert_to_pdf_raises_on_failure(mocker):
    mock_run = mocker.patch("tailor_cv.pdf.subprocess.run")
    mock_run.return_value = MagicMock(returncode=1, stderr="pandoc error")

    with pytest.raises(RuntimeError, match="pandoc failed"):
        convert_to_pdf("input.md", "output.pdf")
