"""Unit tests for the Indeed scraper."""

import os

import pytest
from easelenium.browser import Browser
from job_finder.utils.caching_utils import ENV_VAR_DISABLE_CACHED

from job_finder.scraper.base import get_browser
from job_finder.scraper.indeed import IndeedBoard


@pytest.fixture
def browser() -> Browser:
    # skip caching
    os.environ[ENV_VAR_DISABLE_CACHED] = "1"
    return get_browser()


@pytest.fixture
def page(browser: Browser) -> IndeedBoard:
    return IndeedBoard(browser)


def test_login(browser: Browser) -> None:
    for _ in range(3):
        page = IndeedBoard(browser)
        assert page._signin()
        page.open("https://de.indeed.com/")
        assert page._signin()
        page.open("https://secure.indeed.com/auth")
        assert page._signin()


def test_get_job(page: IndeedBoard) -> None:
    job = page._get_job("https://de.indeed.com/viewjob?jk=230221f283dacab0&tk=1jncgok7shbu7800&from=serp&vjs=3")
    assert "230221f283dacab0" in job.url
    assert "https" in job.url
    assert "Senior Python Developer" in job.title
    assert "Sloboda Studio" in job.company
    description = job.description
    assert "Sloboda Studio" in description
    assert "Quarterly teambuilding activities and company corporate events" in description


def test_get_job_with_company(page: IndeedBoard) -> None:
    job = page._get_job("https://de.indeed.com/viewjob?jk=f61ba1a6e8f452c9&from=serp&vjs=3")
    assert "Principal Field Engineer" in job.title
    assert "Cognite - AI for Industry" in job.company
    description = job.description
    assert "Cognite operates" in description
    assert "Impact 2025" in description


def test_get_jobs(page: IndeedBoard) -> None:
    url = "https://de.indeed.com/jobs?q=software&l=berlin&fromage=14&radius=50&from=searchOnDesktopSerp"
    limit = 21
    page.open(url)
    jobs = page.get_jobs(limit=limit)
    assert len(jobs) == limit
    assert len(jobs[0].description) > 100
