"""Unit tests for the StepStone scraper."""

import pytest
from easelenium.browser import Browser

from scraper.base import get_browser
from scraper.stepstone import StepstonePage

__URL = "https://www.stepstone.de/jobs/rust/in-potsdam?radius=50&action=facet_selected%3bage%3bage_7&ag=age_7&searchOrigin=Resultlist_top-search"


@pytest.fixture
def browser() -> Browser:
    return get_browser()


@pytest.fixture
def page(browser: Browser) -> None:
    return StepstonePage(browser)


def test_get_urls(page: StepstonePage) -> None:
    page.open(__URL)
    limit = 5
    jobs = page.get_jobs(limit=limit)
    assert len(jobs) == limit
    assert len(jobs[0].description) > 100


def test_login(page: StepstonePage) -> None:
    assert page._signin()
    assert page._signin()


def test_get_job(page: StepstonePage) -> None:
    url = "https://www.stepstone.de/jobs--Senior-Software-Developer-m-w-d-Berlin-meinestadt-de--13929237-inline.html"
    job = page._get_job(url)
    assert "Senior Software Developer" in job.title
    assert "meinestadt.de" in job.company
    assert job.url == url
    assert len(job.description) > 100
