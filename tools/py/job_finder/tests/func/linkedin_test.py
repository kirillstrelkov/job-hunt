"""Unit tests for the LinkedIn scraper."""

import os
from unittest.mock import patch

import pytest
from easelenium.browser import Browser

from job_finder.scraper.base import Job, get_browser
from job_finder.scraper.linkedin import LinkedinBoard
from job_finder.utils.caching_utils import ENV_VAR_DISABLE_CACHED


@pytest.fixture
def browser() -> Browser:
    # skip caching
    os.environ[ENV_VAR_DISABLE_CACHED] = "1"
    return get_browser()


@pytest.fixture
def page(browser: Browser) -> LinkedinBoard:
    return LinkedinBoard(browser)


def test_login(browser: Browser) -> None:
    for _ in range(3):
        page = LinkedinBoard(browser)
        assert page._signin()
        page.open("https://www.linkedin.com/jobs/view/4354613359/")
        assert page._signin()
        page.open("https://www.linkedin.com/login")
        assert page._signin()


def test_linkedin_get_job(page: LinkedinBoard) -> None:
    job = page._get_job("https://www.linkedin.com/jobs/view/4354613359/")
    assert "4354613359" in job.url
    assert "http" in job.url
    assert "Golang Software Engineer" in job.title
    assert "Allianz Partners" in job.company
    description = job.description
    assert "simplesurance is a leading insurtech" in description
    assert "Sabbatical Programme" in description
    assert "Never stop playing" in description


def test_linkedin_get_job2(page: LinkedinBoard) -> None:
    job = page._get_job("https://www.linkedin.com/jobs/view/4393486078/")
    assert "4393486078" in job.url
    assert "http" in job.url
    description = job.description
    assert "Arbeitsplatz und viele Benefits" in description


def test_get_jobs(page: LinkedinBoard) -> None:
    url = "https://www.linkedin.com/jobs/search/?currentJobId=4352782750&f_TPR=r2592000&geoId=103035651&keywords=%22software%20engineer%22&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&spellCorrectionEnabled=true"
    limit = 5
    page.open(url)
    jobs = page.get_jobs(limit=limit)
    assert len(jobs) == limit
    assert len(jobs[0].description) > 100


def test_get_jobs_with_limit_and_mocked_get_job(page: LinkedinBoard) -> None:
    url = "https://www.linkedin.com/jobs/search/?currentJobId=4418748282&f_TPR=r604800&keywords=%22test%22&origin=JOB_SEARCH_PAGE_JOB_FILTER"

    def _get_job(url):
        return Job(title="", company="", url=url, description="", error="")

    limit = 31
    with patch.object(page, "get_job", side_effect=_get_job):
        jobs = page.get_jobs(url, limit=limit)
        assert len(jobs) == limit


def test_get_jobs_failing_url(page: LinkedinBoard) -> None:
    url = "https://www.linkedin.com/jobs/view/4399293689/"
    with (
        patch.object(page, "get_job_urls", return_value=[url]),
        patch.object(page, "_has_next_page", return_value=False),
    ):
        page.open(url)
        jobs = page.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].url == url


def test_get_jobs_failing_urls(page: LinkedinBoard) -> None:
    failed_urls = [
        "https://www.linkedin.com/jobs/view/4383013067",
        "https://www.linkedin.com/jobs/view/4398023509",
        "https://www.linkedin.com/jobs/view/4388373539",
    ]

    with (
        patch.object(page, "get_job_urls", return_value=failed_urls),
        patch.object(page, "_has_next_page", return_value=False),
    ):
        jobs = page.get_jobs()
        assert len(jobs) == len(failed_urls)


def test_linkedin_no_jobs(page: LinkedinBoard) -> None:
    url = "https://www.linkedin.com/jobs/search/?currentJobId=4377194485&f_TPR=r604800&f_WT=2&geoId=101282230&keywords=%22sdfpowe%22&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true"

    jobs = page.get_jobs(url)
    assert not jobs
