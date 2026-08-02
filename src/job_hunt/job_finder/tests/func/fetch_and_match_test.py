from pathlib import Path
from unittest.mock import patch

from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.job_finder.cli.fetch_and_match import _main
from job_hunt.job_finder.scraper.fetch import get_jobs
from job_hunt.job_finder.utils.models import Job


def test_fetch_and_match() -> None:
    url = next(url for url in DEFAULT_CONFIG.scraper.urls if "indeed" in url)
    tmp_output = Path("/tmp/testing_featch_and_match")
    tmp_output.mkdir(parents=True, exist_ok=True)

    testing_limit = 3

    def _get_jobs_with_limit(*urls: str, limit: int | None = None, use_cache: bool = False) -> list[Job]:
        return get_jobs(*urls, limit=testing_limit, use_cache=use_cache)

    with (
        patch("job_finder.scraper.fetch.get_jobs", side_effect=_get_jobs_with_limit),
    ):
        _main(urls=[url], output_dir=tmp_output)

    jobs_file = tmp_output / "jobs.csv"
    matches_file = tmp_output / "job_matches.csv"

    assert jobs_file.exists()
    assert matches_file.exists()
