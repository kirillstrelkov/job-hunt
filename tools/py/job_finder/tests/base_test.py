"""Unit tests for the scraper base classes and utilities."""

from datetime import UTC, datetime, timedelta, timezone

from job_finder.reviewer.match import JobMatch
from job_finder.scraper.base import Job, make_job


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


def test_job_created_at_string_conversion() -> None:
    # Arrange
    job = Job(
        title="Software Engineer",
        company="Google",
        url="https://google.com/job-first",
        description="Write Python code",
        error="",
        created_at="2026-07-10T08:54:21Z",
    )

    # Assert

    assert isinstance(job.created_at, datetime)
    assert job.created_at == datetime(2026, 7, 10, 8, 54, 21, tzinfo=UTC)

    # Arrange with timezone offset
    job2 = Job(
        title="Software Engineer",
        company="Google",
        url="https://google.com/job-first",
        description="Write Python code",
        error="",
        created_at="2026-07-10T08:54:21+02:00",
    )

    assert isinstance(job2.created_at, datetime)
    assert job2.created_at == datetime(2026, 7, 10, 8, 54, 21, tzinfo=timezone(timedelta(hours=2)))

    # Arrange with space, microseconds, and timezone offset
    job3 = Job(
        title="Software Engineer",
        company="Google",
        url="https://google.com/job-first",
        description="Write Python code",
        error="",
        created_at="2026-07-07 13:03:48.020672+00:00",
    )
    assert isinstance(job3.created_at, datetime)
    assert job3.created_at == datetime(2026, 7, 7, 13, 3, 48, 20672, tzinfo=UTC)


def test_job_match_processed_at_string_conversion() -> None:
    # Arrange
    match = JobMatch(
        title="Software Engineer",
        company="Google",
        url="https://google.com/job-first",
        description="Write Python code",
        error="",
        created_at="2026-07-07 13:03:48.020672+00:00",
        processed_at="2026-07-08 14:05:50.123456+00:00",
    )

    assert isinstance(match.created_at, datetime)
    assert match.created_at == datetime(2026, 7, 7, 13, 3, 48, 20672, tzinfo=UTC)
    assert isinstance(match.processed_at, datetime)
    assert match.processed_at == datetime(2026, 7, 8, 14, 5, 50, 123456, tzinfo=UTC)
