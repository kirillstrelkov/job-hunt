"""Unit tests for the StepStone scraper."""

import pytest
from easelenium.browser import Browser

from job_finder.scraper.base import get_browser
from job_finder.scraper.stepstone import StepstoneBoard


@pytest.fixture
def browser() -> Browser:
    return get_browser()


@pytest.fixture
def page(browser: Browser) -> StepstoneBoard:
    return StepstoneBoard(browser)


def test_get_urls(page: StepstoneBoard) -> None:
    limit = 3
    jobs = page._get_all_jobs_from_all_pages(
        url="https://www.stepstone.de/jobs/rust/in-potsdam?radius=50&action=facet_selected%3bage%3bage_7&ag=age_7&searchOrigin=Resultlist_top-search",
        limit=limit,
    )
    assert len(jobs) == limit
    assert len(jobs[0].description) > 100


def test_login(page: StepstoneBoard) -> None:
    assert page._signin()
    assert page._signin()


def test_get_job(page: StepstoneBoard) -> None:
    url = "https://www.stepstone.de/stellenangebote--Software-Test-QA-Engineer-m-w-d-im-NET-Umfeld-HR-Workforce-Logistics-Muenster-Koeln-Berlin-flaschenpost-SE--14121843-inline.html"
    job = page._get_job_with_description(url=url)
    assert "Software Test-/QA-Engineer" in job.title
    assert "flaschenpost" in job.company
    assert job.url == url
    assert len(job.description) > 100
