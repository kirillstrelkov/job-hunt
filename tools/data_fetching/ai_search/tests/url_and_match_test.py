import os
from unittest.mock import patch
import pytest
from base import get_browser
from caching_utils import ENV_VAR_DISABLE_CACHED
from easelenium.browser import Browser
from job.ai_search.cli import _get_job_matches, get_jobs
from stepstone import StepstonePage

__URL = "https://www.stepstone.de/jobs/rust/in-potsdam?radius=50&action=facet_selected%3bage%3bage_7&ag=age_7&searchOrigin=Resultlist_top-search"

os.environ[ENV_VAR_DISABLE_CACHED] = "1"
os.environ["DEBUG"] = "1"


def test_n26_not_german() -> None:
    url = "https://www.stepstone.de/stellenangebote--Senior-Backend-Engineer-Berlin-N26-GmbH--13903661-inline.html"
    with patch("base.Page._get_job_links", return_value=[url]):
        jobs = get_jobs(url)  # url is needed to initiaze proper class
        matches = _get_job_matches(jobs)
        print(jobs[0].description)
        assert len(matches) == 1
        m = matches[0]
        assert m.match_percentage > 30, f"Wrong result for {m}"
