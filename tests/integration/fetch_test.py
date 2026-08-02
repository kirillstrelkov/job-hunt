from unittest.mock import patch

import pytest

from job_hunt.config.config import DEFAULT_CONFIG
from job_hunt.job_finder.scraper.fetch import get_jobs
from job_hunt.job_finder.utils.models import BaseJob


def test_get_jobs() -> None:
    url = next(url for url in DEFAULT_CONFIG.scraper.urls if "indeed" in url)
    jobs = get_jobs(url, limit=3)
    assert len(jobs) == 3


@pytest.mark.parametrize(
    "board_name",
    [
        "indeed",
        "linkedin",
        "stepstone",
    ],
)
def test_base_filter(board_name: str) -> None:
    base_jobs = [
        BaseJob(
            title="Laser Spectroscopy Working Student",
            company="Quantune Technologies GmbH",
            url="https://de.indeed.com/viewjob?jk=fcbc8a23abbe4291",
        ),
        BaseJob(
            title="Working Student/Intern v&v",
            company="Verolt Technology Solutions GmbH",
            url="https://de.indeed.com/viewjob?jk=004bb61e18f7c14e",
        ),
        BaseJob(
            title="AI Engineer",
            company="Turing",
            url="https://turing.com/job1",
        ),
        BaseJob(
            title="Freelance Writer",
            company="Mindrift Corp",
            url="https://mindrift.ai/job1",
        ),
        BaseJob(
            title="Internship: Generative AI & Deepfake Detection unpaid",
            company="HOPn",
            url="https://www.linkedin.com/jobs/view/4431027734",
        ),
        BaseJob(
            title="Head of Marketing",
            company="ai-coustics UG (haftungsbeschränkt)",
            url="https://www.stepstone.de/stellenangebote--14023999-inline.html",
        ),
        BaseJob(
            title="ICT Risk Assessment Manager",
            company="N26 GmbH",
            url="https://www.stepstone.de/stellenangebote--14138670-inline.html",
        ),
        BaseJob(
            title="IT Audit Manager",
            company="N26 GmbH",
            url="https://www.stepstone.de/stellenangebote--13960647-inline.html",
        ),
    ]

    url = next(url for url in DEFAULT_CONFIG.scraper.urls if board_name in url)

    with (
        patch("job_finder.scraper.base._get_browser"),
        patch("job_finder.scraper.base.JobBoard._get_base_jobs_from_current_page", return_value=base_jobs),
        patch("job_finder.scraper.base.JobBoard._has_next_page", return_value=False),
    ):
        jobs = get_jobs(url)
        assert not jobs
