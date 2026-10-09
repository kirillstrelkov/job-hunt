"""Unit tests for OKF (Markdown + Frontmatter) reader and writer."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from job_hunt.job_finder.utils.models import BaseJob, Job, JobMatch
from job_hunt.job_finder.utils.okf import read_job, write_job


def test_write_and_read_base_job(tmp_path: Path) -> None:
    """Test round-trip serialization of BaseJob."""
    job = BaseJob(
        title="Software Engineer",
        company="Tech Corp",
        url="https://example.com/job/1",
        error="",
    )
    file_path = tmp_path / "job.md"
    write_job(job, file_path)

    assert file_path.exists()
    content = file_path.read_text(encoding="utf-8")
    assert "model_type: BaseJob" in content
    assert "title: Software Engineer" in content
    assert "# Software Engineer" in content
    # Error is empty, so ## Error should be omitted
    assert "## Error" not in content

    loaded = read_job(file_path)
    assert isinstance(loaded, BaseJob)
    assert loaded == job


def test_write_and_read_job(tmp_path: Path) -> None:
    """Test round-trip serialization of Job with description and created_at."""
    created_at = datetime(2026, 9, 8, 8, 30, 0, tzinfo=UTC)
    job = Job(
        title="Backend Developer",
        company="Startup Inc",
        url="https://example.com/job/2",
        description="We are looking for a Python developer.\nKey skills: FastAPI, Docker.",
        created_at=created_at,
        error="Warning: test error message",
    )
    file_path = tmp_path / "job.md"
    write_job(job, file_path)

    content = file_path.read_text(encoding="utf-8")
    assert "model_type: Job" in content
    assert "## Description" in content
    assert "We are looking for a Python developer." in content
    assert "## Error" in content
    assert "Warning: test error message" in content

    loaded = read_job(file_path)
    assert isinstance(loaded, Job)
    assert loaded == job
    assert loaded.description == job.description
    assert loaded.created_at == job.created_at
    assert loaded.error == job.error


def test_write_and_read_job_match(tmp_path: Path) -> None:
    """Test round-trip serialization of JobMatch with all metadata."""
    created_at = datetime(2026, 9, 8, 8, 0, 0, tzinfo=UTC)
    processed_at = datetime(2026, 9, 8, 8, 15, 0, tzinfo=UTC)
    job = JobMatch(
        title="Full Stack Engineer",
        company="Global Enterprises",
        url="https://example.com/job/3",
        description="Senior Full Stack role with React and Python.",
        created_at=created_at,
        match_percentage=88,
        check_passed=True,
        llm_text='{\n  "fit": "Strong",\n  "matched_skills": ["Python", "React"]\n}',
        processed_at=processed_at,
        error="",
    )
    file_path = tmp_path / "job.md"
    write_job(job, file_path)

    content = file_path.read_text(encoding="utf-8")
    assert "model_type: JobMatch" in content
    assert "match_percentage: 88" in content
    assert "check_passed: true" in content
    assert "## Description" in content
    assert "## LLM Text" in content
    assert "## Error" not in content  # empty error omitted

    loaded = read_job(file_path)
    assert isinstance(loaded, JobMatch)
    assert loaded == job
    assert loaded.match_percentage == 88
    assert loaded.check_passed is True
    assert loaded.llm_text == job.llm_text
    assert loaded.processed_at == processed_at


def test_adaptive_code_fence_for_backticks(tmp_path: Path) -> None:
    """Test that text containing triple backticks uses a longer fence."""
    description_with_code = (
        "Job requires Python coding:\n```python\ndef solution():\n    return True\n```\nEnd of requirements."
    )
    job = Job(
        title="Python Lead",
        company="Code Co",
        url="https://example.com/job/4",
        description=description_with_code,
    )
    file_path = tmp_path / "job.md"
    write_job(job, file_path)

    content = file_path.read_text(encoding="utf-8")
    # Verify 4 backticks are used for the outer fence
    assert "````text\n" in content
    assert "\n````" in content

    loaded = read_job(file_path)
    assert loaded.description == description_with_code


def test_missing_model_type_raises_error(tmp_path: Path) -> None:
    """Test that missing model_type in frontmatter raises ValueError."""
    bad_content = "---\ntitle: Engineer\ncompany: Acme\nurl: https://example.com\n---\n\n# Engineer\n"
    file_path = tmp_path / "job.md"
    file_path.write_text(bad_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Missing or invalid 'model_type'"):
        read_job(file_path)


def test_missing_title_raises_error(tmp_path: Path) -> None:
    """Test that missing title in frontmatter raises ValueError."""
    bad_content = "---\nmodel_type: Job\ncompany: Acme\nurl: https://example.com\n---\n\n# Engineer\n"
    file_path = tmp_path / "job.md"
    file_path.write_text(bad_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required field 'title'"):
        read_job(file_path)


def test_missing_frontmatter_raises_error(tmp_path: Path) -> None:
    """Test that file without frontmatter raises ValueError."""
    bad_content = "# Just markdown without frontmatter\n"
    file_path = tmp_path / "job.md"
    file_path.write_text(bad_content, encoding="utf-8")

    with pytest.raises(ValueError, match="does not contain valid YAML frontmatter"):
        read_job(file_path)
