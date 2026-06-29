"""Unit tests for the LLM CV matching and screening reviewer."""

from pathlib import Path
from pprint import pformat

import pytest
from loguru import logger

from job_finder.reviewer.llm import (
    JobMatchResult,
    _get_analysis,
    _get_screening,
    analyze_cv,
    get_checked_passed,
    get_match_percentage,
)

__DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def assert_llm_response(
    result: JobMatchResult, min_match: int = 0, fail_reason: str | None = None, max_match: int = 100
) -> None:
    """Assert that LLM response matches expected screening and fit thresholds."""
    if fail_reason:
        assert result.screening is not None
        assert fail_reason in result.screening.gate_failed_reasons, f"Failed : {pformat(result.screening)}"
        return

    if result.screening:
        assert get_checked_passed(result), f"Failed : {result.model_dump()}"
    assert get_match_percentage(result) >= min_match
    assert get_match_percentage(result) <= max_match


def _run_and_assert(sub_path: str, min_match: int, fail_reason: str | None = None) -> None:
    logger.debug("Path: {}", sub_path)
    job_desc = (__DATA_DIR / sub_path).read_text(encoding="utf-8")

    res = analyze_cv(CV_TEXT, job_desc)
    assert_llm_response(res, min_match, fail_reason)


CV_TEXT = (__DATA_DIR / "private/cv.txt").read_text(encoding="utf-8")

_SCREENING_DATA = (
    (
        "test/manager.txt",
        "is_manager",
    ),  # https://www.stepstone.de/stellenangebote--Product-Marketing-Manager-m-f-d-Legal-AI-Tech-Start-up-Remote-Berlin-Germany-XAYN-AG--12536908-inline.html
    ("test/staff.txt", "is_staff"),  # https://www.linkedin.com/jobs/view/4387430504/
    ("test/contract.txt", "is_contract"),  # https://www.linkedin.com/jobs/view/4370016911/
    ("test/intern.txt", "is_excluded_role"),  # https://www.linkedin.com/jobs/view/4409739015
)
_ANALYSIS_DATA = (
    ("test/tesla_go.txt", 60),  # https://www.tesla.com/de_DE/careers/search/job/
    ("test/moia.txt", 30),  # https://job-boards.eu.greenhouse.io/moia/jobs/4777984101
    ("test/not_manager.txt", 60),  # https://www.linkedin.com/jobs/view/4425676559/
    ("test/sen_qa.txt", 20),  # https://zertificon.jobs.personio.de/job/2053203?language=en
)


@pytest.mark.parametrize(
    ("file_path", "fail_reason"),
    _SCREENING_DATA,
)
def test_screening_reason(file_path: str, fail_reason: str) -> None:
    """Test that jobs failing pre-screening are rejected with the correct flag."""
    _run_and_assert(file_path, 0, fail_reason)


@pytest.mark.parametrize(
    ("file_path", "min_match"),
    _ANALYSIS_DATA,
)
def test_min_match_percentage(file_path: str, min_match: int) -> None:
    """Test that acceptable jobs pass screening with at least the minimum match percentage."""
    _run_and_assert(file_path, min_match)


@pytest.mark.parametrize(
    ("file_path", "expected_flag"),
    _SCREENING_DATA,
)
def test_screening_output(file_path: str, expected_flag: str) -> None:
    """Test that _get_screening correctly catches excluded roles or requirements."""
    job_desc = (__DATA_DIR / file_path).read_text(encoding="utf-8")
    scr = _get_screening(job_desc)
    assert not scr.gate_passed
    assert expected_flag in scr.gate_failed_reasons
    assert getattr(scr, expected_flag) is True


@pytest.mark.parametrize(
    ("file_path", "min_match"),
    _ANALYSIS_DATA,
)
def test_analysis_output(file_path: str, min_match: int) -> None:
    """Test that _get_analysis returns correct fit and match thresholds."""
    job_desc = (__DATA_DIR / file_path).read_text(encoding="utf-8")
    analysis = _get_analysis(CV_TEXT, job_desc)
    assert analysis.match_percentage > min_match
