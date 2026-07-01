"""Unit tests for the StepStone scraper."""

import pytest
from easelenium.browser import Browser

from job_finder.scraper.base import get_browser
from job_finder.scraper.stepstone import StepstonePage

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
    url = "https://www.stepstone.de/stellenangebote--Automation-Engineer-m-w-d-Bonn-bundesweit-Home-Office-Dedalus-HealthCare-GmbH--14208893-inline.html"
    job = page._get_job(url)
    assert "Automation Engineer" in job.title
    assert "Dedalus HealthCare" in job.company
    assert job.url == url
    assert len(job.description) > 100
