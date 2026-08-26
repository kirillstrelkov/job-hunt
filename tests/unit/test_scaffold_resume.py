"""Unit tests for the resume scaffold module."""

from pathlib import Path

import pandas as pd
import pytest

from job_hunt.resume.scaffold_resume import (
    filter_job_listings,
    print_scaffold_summary,
    scaffold_jobs_from_csv,
)


def test_filter_job_listings_basic() -> None:
    data = {
        "title": ["Python Developer", "QA Engineer", "Intern", "DevOps Engineer"],
        "company": ["Tesla", "Google", "Amazon", "Apple"],
        "description": ["Build apps", "Test apps", "Learn stuff", "Deploy apps"],
        "check_passed": [True, "true", False, 1],
        "match_percentage": [85, 90, 95, 75],
    }
    df = pd.DataFrame(data)

    # Filter with default min_score=80
    filtered = filter_job_listings(df, min_score=80)

    # Python Developer (85 >= 80, True), QA Engineer (90 >= 80, "true") should pass
    # Intern (check_passed=False) and DevOps (75 < 80) should be excluded
    assert len(filtered) == 2
    assert list(filtered["company"]) == ["Tesla", "Google"]


def test_filter_job_listings_custom_min_score() -> None:
    data = {
        "title": ["Python Developer", "DevOps Engineer"],
        "company": ["Tesla", "Apple"],
        "description": ["Build apps", "Deploy apps"],
        "check_passed": [True, True],
        "match_percentage": [85, 70],
    }
    df = pd.DataFrame(data)

    filtered = filter_job_listings(df, min_score=60)
    assert len(filtered) == 2


def test_filter_job_listings_missing_columns() -> None:
    data = {
        "title": ["Python Developer"],
        "description": ["Build apps"],
    }
    df = pd.DataFrame(data)

    with pytest.raises(ValueError, match="must contain 'title', 'company', and 'description'"):
        filter_job_listings(df)


def test_filter_job_listings_empty_fields() -> None:
    data = {
        "title": ["Python Developer", "", "QA Engineer"],
        "company": ["Tesla", "Google", ""],
        "description": ["Build apps", "Test apps", "More test"],
        "check_passed": [True, True, True],
        "match_percentage": [90, 90, 90],
    }
    df = pd.DataFrame(data)

    filtered = filter_job_listings(df)
    assert len(filtered) == 1
    assert filtered.iloc[0]["company"] == "Tesla"


def test_scaffold_jobs_from_csv(tmp_path: Path) -> None:
    csv_file = tmp_path / "test_jobs.csv"
    data = {
        "title": ["Senior Python Engineer", "Frontend Developer"],
        "company": ["Tesla Inc", "Acme Corp"],
        "description": ["Python backend role with distributed systems.", "React role."],
        "check_passed": [True, False],
        "match_percentage": [88, 92],
    }
    pd.DataFrame(data).to_csv(csv_file, index=False)

    out_folder = tmp_path / "scaffold_out"

    records = scaffold_jobs_from_csv(
        path=csv_file,
        folder=out_folder,
        min_score=80,
    )

    assert len(records) == 1
    record = records[0]
    assert record["company"] == "Tesla Inc"
    assert record["title"] == "Senior Python Engineer"
    assert record["status"] == "Scaffolded"

    job_dir = Path(record["folder"])
    assert job_dir.exists()
    assert (job_dir / "jd.txt").exists()
    assert (job_dir / "prompt.md").exists()

    jd_content = (job_dir / "jd.txt").read_text(encoding="utf-8")
    assert "Python backend role" in jd_content

    prompt_content = (job_dir / "prompt.md").read_text(encoding="utf-8")
    assert "Python backend role" in prompt_content


def test_scaffold_jobs_from_csv_no_matches(tmp_path: Path) -> None:
    csv_file = tmp_path / "low_score_jobs.csv"
    data = {
        "title": ["Junior Dev"],
        "company": ["Startup"],
        "description": ["General programming"],
        "check_passed": [True],
        "match_percentage": [40],
    }
    pd.DataFrame(data).to_csv(csv_file, index=False)

    out_folder = tmp_path / "scaffold_out"
    records = scaffold_jobs_from_csv(path=csv_file, folder=out_folder, min_score=80)
    assert records == []


def test_scaffold_jobs_from_csv_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        scaffold_jobs_from_csv(path=tmp_path / "non_existent.csv")


def test_print_scaffold_summary(capsys: pytest.CaptureFixture) -> None:
    records = [
        {
            "index": 1,
            "job_id": "tesla_senior_qa",
            "company": "Tesla",
            "title": "Senior QA Engineer",
            "score": "92%",
            "folder": "/tmp/tesla_senior_qa",
            "prompt": "/tmp/tesla_senior_qa/prompt.md",
            "status": "Scaffolded",
        }
    ]
    print_scaffold_summary(records)
    captured = capsys.readouterr()
    assert "Tesla" in captured.out
    assert "Senior QA Engineer" in captured.out
    assert "tesla_senior_qa" in captured.out
