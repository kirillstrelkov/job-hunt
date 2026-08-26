"""Unit tests for the StepStone scraper."""

import pytest
from easelenium.browser import Browser

from job_hunt.job_finder.scraper.base import get_browser
from job_hunt.job_finder.scraper.hiring_cafe import HiringCafeBoard


@pytest.fixture
def browser() -> Browser:
    return get_browser()


@pytest.fixture
def page(browser: Browser) -> HiringCafeBoard:
    return HiringCafeBoard(browser)


def test_get_urls(page: HiringCafeBoard) -> None:
    limit = 45
    jobs = page._get_all_jobs_from_all_pages(
        url="https://hiringcafe.com/?searchState=%7B%22locations%22%3A%5B%7B%22formatted_address%22%3A%22Netherlands%22%2C%22types%22%3A%5B%22country%22%5D%2C%22geometry%22%3A%7B%22location%22%3A%7B%22lat%22%3A52.3716%2C%22lon%22%3A4.8883%7D%7D%2C%22id%22%3A%22user_country%22%2C%22address_components%22%3A%5B%7B%22long_name%22%3A%22Netherlands%22%2C%22short_name%22%3A%22NL%22%2C%22types%22%3A%5B%22country%22%5D%7D%5D%2C%22options%22%3A%7B%22flexible_regions%22%3A%5B%22anywhere_in_continent%22%2C%22anywhere_in_world%22%5D%7D%7D%5D%2C%22searchQuery%22%3A%22python%22%7D",
        limit=limit,
    )
    assert len(set(jobs)) == limit
    assert len(jobs[0].description) > 100


def test_get_urls_check_title(page: HiringCafeBoard) -> None:
    limit = 1
    jobs = page._get_all_jobs_from_all_pages(
        url="https://hiringcafe.com/?searchState=%7B%22locations%22%3A%5B%7B%22formatted_address%22%3A%22Netherlands%22%2C%22types%22%3A%5B%22country%22%5D%2C%22geometry%22%3A%7B%22location%22%3A%7B%22lat%22%3A52.3716%2C%22lon%22%3A4.8883%7D%7D%2C%22id%22%3A%22user_country%22%2C%22address_components%22%3A%5B%7B%22long_name%22%3A%22Netherlands%22%2C%22short_name%22%3A%22NL%22%2C%22types%22%3A%5B%22country%22%5D%7D%5D%2C%22options%22%3A%7B%22flexible_regions%22%3A%5B%22anywhere_in_continent%22%2C%22anywhere_in_world%22%5D%7D%7D%5D%2C%22searchQuery%22%3A%22python%22%7D",
        limit=limit,
    )
    assert len(set(jobs)) == limit
    assert len(jobs[0].description) > 100
    assert "job" not in jobs[0].title.lower()


def test_login(page: HiringCafeBoard) -> None:
    assert page._signin()
    assert page._signin()


def test_get_job(page: HiringCafeBoard) -> None:
    url = "https://hiringcafe.com/job/senior-software-engineer-f-m-x-enpal-berlin-berlin-duckvbhe36kfoxn6"
    job = page._get_job_with_description(url=url)
    assert "Senior Software Engineer (f/m/x)" in job.title
    assert "Enpal" in job.company
    assert job.url == url
    assert len(job.description) > 100
    assert "Our goal is to" in job.description
    assert "good work-life balance" in job.description
