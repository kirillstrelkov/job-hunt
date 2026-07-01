"""Unit tests for the fetch scraper coordinator."""

from job_finder.scraper.base import make_job
from job_finder.scraper.fetch import _filter_jobs


def test_filter_jobs() -> None:
    jobs = [
        make_job(
            title="Laser Spectroscopy Working Student",
            company="Quantune Technologies GmbH",
            url="https://de.indeed.com/viewjob?jk=fcbc8a23abbe4291",
            description="Laser physics",
        ),
        make_job(
            title="Working Student/Intern v&v",
            company="Verolt Technology Solutions GmbH",
            url="https://de.indeed.com/viewjob?jk=004bb61e18f7c14e",
            description="Verification and validation",
        ),
        make_job(
            title="AI Engineer",
            company="Turing",
            url="https://turing.com/job1",
            description="Solve algorithms",
        ),
        make_job(
            title="Freelance Writer",
            company="Mindrift Corp",
            url="https://mindrift.ai/job1",
            description="Write text",
        ),
        make_job(
            title="Internship: Generative AI & Deepfake Detection unpaid",
            company="HOPn",
            url="https://www.linkedin.com/jobs/view/4431027734",
            description="Generative AI testing",
        ),
        make_job(
            title="Head of Marketing",
            company="ai-coustics UG (haftungsbeschränkt)",
            url="https://www.stepstone.de/stellenangebote--14023999-inline.html",
            description="Marketing leadership",
        ),
        make_job(
            title="ICT Risk Assessment Manager",
            company="N26 GmbH",
            url="https://www.stepstone.de/stellenangebote--14138670-inline.html",
            description="Risk management",
        ),
        make_job(
            title="IT Audit Manager",
            company="N26 GmbH",
            url="https://www.stepstone.de/stellenangebote--13960647-inline.html",
            description="IT auditing",
        ),
    ]

    result = _filter_jobs(jobs)
    assert len(result) == 0
