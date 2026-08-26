"""Unit tests for the centralized binary helper module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from job_hunt.core.binary_helper import (
    BinaryName,
    BinaryNotFoundError,
    get_binary,
    get_codesign,
    get_npx,
    get_pandoc,
    get_pdfinfo,
    get_pdftotext,
    get_streamlit,
)


def test_binary_name_enum() -> None:
    assert BinaryName.PANDOC == "pandoc"
    assert BinaryName.PDFINFO == "pdfinfo"
    assert BinaryName.PDFTOTEXT == "pdftotext"
    assert BinaryName.NPX == "npx"
    assert BinaryName.STREAMLIT == "streamlit"
    assert BinaryName.CODESIGN == "codesign"


def test_get_binary_success() -> None:
    with patch("shutil.which", return_value="/usr/local/bin/pandoc"):
        pandoc_path = get_binary(BinaryName.PANDOC)
        assert pandoc_path == "/usr/local/bin/pandoc"


def test_get_binary_not_found_raises_exception() -> None:
    with patch("shutil.which", return_value=None):
        with pytest.raises(BinaryNotFoundError) as exc_info:
            get_binary("non_existent_binary_xyz", hint="Custom installation instruction")

        err = exc_info.value
        assert err.binary_name == "non_existent_binary_xyz"
        assert "Required binary 'non_existent_binary_xyz' was not found" in str(err)
        assert "Custom installation instruction" in str(err)


def test_get_binary_not_found_not_required() -> None:
    with patch("shutil.which", return_value=None):
        res = get_binary("non_existent_binary_xyz", required=False)
        assert res == ""


def test_convenience_getters() -> None:
    with patch("shutil.which", side_effect=lambda name: f"/usr/local/bin/{name}"):
        assert get_pandoc() == "/usr/local/bin/pandoc"
        assert get_pdfinfo() == "/usr/local/bin/pdfinfo"
        assert get_pdftotext() == "/usr/local/bin/pdftotext"
        assert get_npx() == "/usr/local/bin/npx"
        assert get_streamlit() == "/usr/local/bin/streamlit"
        assert get_codesign() == "/usr/local/bin/codesign"


def test_convenience_getters_missing_raises() -> None:
    with patch("shutil.which", return_value=None):
        with pytest.raises(BinaryNotFoundError) as exc_info:
            get_pandoc()
        assert "pandoc" in str(exc_info.value)
        assert "Please install Pandoc" in str(exc_info.value)


def test_npx_nvm_resolution_fallback(tmp_path: Path) -> None:
    fake_npx = tmp_path / ".nvm" / "versions" / "node" / "v20.0.0" / "bin" / "npx"
    fake_npx.parent.mkdir(parents=True)
    fake_npx.write_text("#!/bin/sh\n")

    with patch("shutil.which", return_value=None), patch("pathlib.Path.home", return_value=tmp_path):
        resolved = get_npx()
        assert resolved == str(fake_npx)
