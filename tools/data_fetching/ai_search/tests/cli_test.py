import os
from pathlib import Path
from unittest.mock import patch
import pytest
from base import Job, get_browser
from caching_utils import ENV_VAR_DISABLE_CACHED
from easelenium.browser import Browser
from job.ai_search.cli import _OUTPUT_PATH, _main
from linkedin import LinkedinPage
import pandas as pd


def test_main_flow() -> None:
    os.environ[ENV_VAR_DISABLE_CACHED] = "1"

    output = Path("/tmp/jobmatches_test.csv")
    output.unlink(missing_ok=True)

    _main(
        [
            "https://www.linkedin.com/jobs/search/?currentJobId=4408500887&f_TPR=r86400&geoId=103035651&keywords=%22python%22&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true&spellCorrectionEnabled=true",
            "https://de.indeed.com/jobs?q=test&l=Potsdam%2C+Brandenburg&fromage=1&radius=50&from=searchOnDesktopSerp&vjk=f0b4d9a4fbf58a78",
        ],
        output,
    )
    assert output.exists()
    df = pd.read_csv(output)
    assert (df["match_percentage"] > 0).any()
