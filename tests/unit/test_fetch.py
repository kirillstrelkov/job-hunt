"""Unit tests for the scraper coordinator, with the browser/board fully mocked out."""

from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from job_hunt.job_finder.scraper.fetch import get_jobs
from job_hunt.job_finder.utils.models import Job


@contextmanager
def _fake_browser_context() -> Generator[MagicMock]:
    yield MagicMock()


def test_get_jobs_passes_existing_jobs_to_board_constructor() -> None:
    existing_job = Job(
        title="Old",
        company="Acme",
        url="https://de.indeed.com/viewjob?jk=old",
        description="already scraped",
    )
    url = "https://de.indeed.com/viewjob?jk=new"

    mock_board_instance = MagicMock()
    mock_board_instance.get_all_jobs.return_value = []
    mock_board_cls = MagicMock(return_value=mock_board_instance)

    with (
        patch("job_hunt.job_finder.scraper.fetch.browser_context", _fake_browser_context),
        patch("job_hunt.job_finder.scraper.fetch.IndeedBoard", mock_board_cls),
    ):
        get_jobs(url, existing_jobs=[existing_job])

    assert mock_board_cls.call_args.kwargs["existing_jobs"] == [existing_job]
    mock_board_instance.get_all_jobs.assert_called_once_with(url=url, limit=None)


def test_get_jobs_without_existing_jobs_passes_none() -> None:
    url = "https://de.indeed.com/viewjob?jk=new"

    mock_board_instance = MagicMock()
    mock_board_instance.get_all_jobs.return_value = []
    mock_board_cls = MagicMock(return_value=mock_board_instance)

    with (
        patch("job_hunt.job_finder.scraper.fetch.browser_context", _fake_browser_context),
        patch("job_hunt.job_finder.scraper.fetch.IndeedBoard", mock_board_cls),
    ):
        get_jobs(url)

    assert mock_board_cls.call_args.kwargs["existing_jobs"] is None
    mock_board_instance.get_all_jobs.assert_called_once_with(url=url, limit=None)
