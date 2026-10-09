"""Unit tests for the Indeed scraper."""

import os

import pytest
from easelenium.browser import Browser

from job_hunt.job_finder.scraper.base import get_browser
from job_hunt.job_finder.scraper.indeed import IndeedBoard
from job_hunt.job_finder.utils.caching_utils import ENV_VAR_DISABLE_CACHED


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
    job = page._get_job_with_description(
        url="https://de.indeed.com/viewjob?jk=f23b823465986e07&from=serp&vjs=3",
    )
    assert "f23b823465986e07" in job.url
    assert "https" in job.url
    assert "Senior Cloud Software Engineer AI" in job.title
    assert "Brighter AI" in job.company
    description = job.description
    assert "brighter AI and Milestone" in description


def test_get_job_with_company(page: IndeedBoard) -> None:
    job = page._get_job_with_description(url="https://de.indeed.com/viewjob?jk=f61ba1a6e8f452c9&from=serp&vjs=3")
    assert "Principal Field Engineer" in job.title
    assert "Cognite - AI for Industry" in job.company
    description = job.description
    assert "Cognite operates" in description
    assert "Impact 2025" in description


def test_get_jobs(page: IndeedBoard) -> None:
    url = "https://de.indeed.com/jobs?q=software&l=berlin&fromage=30&radius=50&from=searchOnDesktopSerp"
    limit = 21
    jobs = page._get_all_jobs_from_all_pages(url=url, limit=limit)
    assert len(jobs) == limit
    assert len(jobs[0].description) > 100


def test_get_no_jobs(page: IndeedBoard) -> None:
    url = "https://de.indeed.com/jobs?q=fgdfgfdg&l=berlin&fromage=30&radius=50&from=searchOnDesktopSerp"
    jobs = page._get_all_jobs_from_all_pages(url=url)
    assert not jobs
