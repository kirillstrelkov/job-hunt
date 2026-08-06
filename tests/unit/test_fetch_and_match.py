"""Unit tests for the fetch-and-match CLI pipeline, with scraping/matching mocked out."""

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from job_hunt.job_finder.cli.fetch_and_match import _main
from job_hunt.job_finder.utils.models import Job, JobMatch


def _make_job(url: str, title: str = "Engineer", company: str = "Acme") -> Job:
    return Job(title=title, company=company, url=url, description=f"Description for {title}")


def _make_match(job: Job, match_percentage: int = 80) -> JobMatch:
    return JobMatch(
        title=job.title,
        company=job.company,
        url=job.url,
        description=job.description,
        match_percentage=match_percentage,
        check_passed=True,
    )


def test_main_writes_jobs_and_matches_csv(tmp_path: Path) -> None:
    urls = ["https://www.indeed.com/viewjob?jk=abc", "https://www.linkedin.com/jobs/view/123"]
    fake_jobs = [_make_job(url, title=f"Engineer {i}") for i, url in enumerate(urls)]
    fake_matches = [_make_match(job) for job in fake_jobs]

    with (
        patch("job_hunt.job_finder.cli.fetch_and_match.get_jobs", return_value=fake_jobs) as mock_get_jobs,
        patch(
            "job_hunt.job_finder.cli.fetch_and_match.get_job_matches", return_value=fake_matches
        ) as mock_get_job_matches,
    ):
        _main(urls, tmp_path)

    mock_get_jobs.assert_called_once_with(*urls, use_cache=True, existing_jobs=[])
    mock_get_job_matches.assert_called_once()

    jobs_file = tmp_path / "jobs.csv"
    matches_file = tmp_path / "job_matches.csv"
    assert jobs_file.exists()
    assert matches_file.exists()

    jobs_df = pd.read_csv(jobs_file)
    assert sorted(jobs_df["url"]) == sorted(urls)

    matches_df = pd.read_csv(matches_file)
    assert sorted(matches_df["url"]) == sorted(urls)
    assert set(matches_df["match_percentage"]) == {80}


def test_main_passes_use_cache_flag(tmp_path: Path) -> None:
    url = "https://de.indeed.com/viewjob?jk=xyz"
    job = _make_job(url)

    with (
        patch("job_hunt.job_finder.cli.fetch_and_match.get_jobs", return_value=[job]) as mock_get_jobs,
        patch("job_hunt.job_finder.cli.fetch_and_match.get_job_matches", return_value=[_make_match(job)]),
    ):
        _main([url], tmp_path, use_cache=False)

    mock_get_jobs.assert_called_once_with(url, use_cache=False, existing_jobs=[])


def test_main_reuses_existing_jobs_csv(tmp_path: Path) -> None:
    existing_url = "https://www.stepstone.de/stellenangebote--1"
    new_url = "https://www.stepstone.de/stellenangebote--2"

    existing_job = _make_job(existing_url, title="Existing")
    new_job = _make_job(new_url, title="New")

    jobs_file = tmp_path / "jobs.csv"
    pd.DataFrame([dict(existing_job)]).to_csv(jobs_file, index=False)

    with (
        patch("job_hunt.job_finder.cli.fetch_and_match.get_jobs", return_value=[new_job]) as mock_get_jobs,
        patch(
            "job_hunt.job_finder.cli.fetch_and_match.get_job_matches",
            return_value=[_make_match(existing_job), _make_match(new_job)],
        ),
    ):
        _main([new_url], tmp_path)

    # already-known jobs are passed through so get_jobs can skip re-scraping them
    passed_existing_jobs = mock_get_jobs.call_args.kwargs["existing_jobs"]
    assert [j.url for j in passed_existing_jobs] == [existing_url]

    jobs_df = pd.read_csv(jobs_file)
    assert sorted(jobs_df["url"]) == sorted([existing_url, new_url])
