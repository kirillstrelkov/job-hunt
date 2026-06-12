from pathlib import Path
from pprint import pformat

from loguru import logger

from llm import analyze_cv, get_checked_passed, get_match_percentage

__DATA_DIR = Path(__file__).parent.parent / "data"


CV_TEXT = (__DATA_DIR / "private/cv.txt").read_text(encoding="utf-8")


def assert_llm_response(res: dict, min_match: int, fail_reason: str | None = None) -> None:
    """Assert that LLM response dictionary matches expected screening and fit thresholds."""
    if fail_reason:
        assert fail_reason in res.get("screening", {}).get("gate_failed_reasons", []), (
            f"Failed : {pformat(res.get('screening', {}))}"
        )
        return

    assert get_checked_passed(res), f"Failed : {pformat(res.get('screening', {}))}"
    assert get_match_percentage(res) > min_match


def _run_and_assert(sub_path: str, min_match: int, fail_reason: str | None = None) -> None:
    logger.debug("Path: {}", sub_path)
    job_desc = (__DATA_DIR / sub_path).read_text(encoding="utf-8")

    res = analyze_cv(CV_TEXT, job_desc)
    assert_llm_response(res, min_match, fail_reason)


def test_match_tesla() -> None:
    # https://www.tesla.com/de_DE/careers/search/job/software-engineer-golang-m-w-d-gigafactory-berlin-brandenburg-267468
    _run_and_assert("test/tesla_go.txt", 60)


def test_match_moia() -> None:
    # https://job-boards.eu.greenhouse.io/moia/jobs/4777984101
    _run_and_assert("test/moia.txt", 30)


def test_match_not_manager() -> None:
    # https://www.linkedin.com/jobs/view/4425676559/
    _run_and_assert("test/not_manager.txt", 60)


def test_match_manager() -> None:
    # https://www.stepstone.de/stellenangebote--Product-Marketing-Manager-m-f-d-Legal-AI-Tech-Start-up-Remote-Berlin-Germany-XAYN-AG--12536908-inline.html
    _run_and_assert("test/manager.txt", 0, "is_manager")


def test_match_staff() -> None:
    # https://www.linkedin.com/jobs/view/4387430504/
    _run_and_assert("test/staff.txt", 0, "is_staff")


def test_match_contract() -> None:
    # https://www.linkedin.com/jobs/view/4370016911/
    _run_and_assert("test/contract.txt", 0, "is_contract")


def test_match_qa() -> None:
    # https://zertificon.jobs.personio.de/job/2053203?language=en
    _run_and_assert("test/sen_qa.txt", 20)


def test_intern() -> None:
    # https://www.linkedin.com/jobs/view/4409739015
    _run_and_assert("test/intern.txt", 0, "is_excluded_role")

