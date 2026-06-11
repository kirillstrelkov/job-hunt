import pytest

from tailor_cv.reader import read_file


def test_read_file_returns_content(tmp_path):
    f = tmp_path / "cv.md"
    f.write_text("# My CV", encoding="utf-8")
    assert read_file(str(f)) == "# My CV"


def test_read_file_missing_raises():
    with pytest.raises(FileNotFoundError, match="not found"):
        read_file("/nonexistent/path/cv.txt")


def test_read_file_empty_raises(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("   \n  ", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        read_file(str(f))
