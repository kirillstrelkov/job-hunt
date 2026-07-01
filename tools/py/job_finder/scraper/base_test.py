"""Unit tests for the scraper base classes and utilities."""

from scraper.base import Job, make_job


def test_uniq_jobs() -> None:
    # same title
    title = "Software engineer"
    assert (
        len(
            {
                make_job(title=title),
                make_job(title=title),
            }
        )
        == 1
    )

    # same title but different companies
    assert (
        len(
            {
                make_job(title=title, company="A"),
                make_job(title=title, company="B"),
            }
        )
        == 2
    )

    # same title but different urls (should be equal and deduplicated)
    assert (
        len(
            {
                make_job(title=title, url="a", description="one two"),
                make_job(title=title, url="b", description="one two"),
            }
        )
        == 1
    )


def test_job_equality() -> None:
    # Arrange
    job_url1 = Job(
        title="Software Engineer",
        company="Google",
        url="https://google.com/job-first",
        description="Write Python code",
        error="",
    )
    job_url2 = Job(
        title="Software Engineer",
        company="Google",
        url="https://google.com/job-second",
        description="Write Python code",
        error="",
    )

    # Assert
    # Jobs should be equal even with different URLs
    assert job_url1 == job_url2

    # Their hashes should also match
    assert hash(job_url1) == hash(job_url2)

    # Set deduplication should keep only one
    jobs_set = {job_url1, job_url2}
    assert len(jobs_set) == 1
