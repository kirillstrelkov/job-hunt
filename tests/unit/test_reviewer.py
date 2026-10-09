"""Unit tests for Job Finder reviewer prompts, models, and both LLM approaches."""

from unittest.mock import patch

from job_hunt.job_finder.reviewer import llm, llm_with_pydantic
from job_hunt.job_finder.reviewer.models import Analysis, JobMatchResult, Screening


def test_prompts_loaded_correctly() -> None:
    """Verify prompt templates are loaded from markdown files and non-empty."""
    assert len(llm.SYSTEM_PROMPT_SCREENING.strip()) > 0
    assert "technical reverse recruiter" in llm.SYSTEM_PROMPT_SCREENING
    assert "is_german_text" in llm.SYSTEM_PROMPT_SCREENING
    assert "gate_failed_reasons" in llm.SYSTEM_PROMPT_SCREENING

    assert len(llm.SYSTEM_PROMPT_CANDIDATE.strip()) > 0
    assert "Resume against the Target Job Description" in llm.SYSTEM_PROMPT_CANDIDATE
    assert "match_percentage" in llm.SYSTEM_PROMPT_CANDIDATE

    assert "{resume}" in llm.RESUME_PROMPT
    assert "{job_description}" in llm.JD_PROMPT

    # Verify Pydantic AI approach also shares the same prompts
    assert "technical reverse recruiter" in llm_with_pydantic.SYSTEM_PROMPT_SCREENING
    assert "is_german_text" in llm_with_pydantic.SYSTEM_PROMPT_SCREENING

    # Verify model is taken from default config fix_model
    from job_hunt.config.config import DEFAULT_CONFIG

    assert DEFAULT_CONFIG.llm.fix_model == llm.MODEL


def test_screening_model_gate_passed() -> None:
    """Test Screening model post-init when all flags are false."""
    screening = Screening(
        reasoning="All checks passed.",
        is_german_text=False,
        is_german_required=False,
        is_manager=False,
        is_staff=False,
        is_contract=False,
        is_excluded_role=False,
    )
    assert screening.gate_passed is True
    assert screening.gate_failed_reasons == []


def test_screening_model_gate_failed_single_reason() -> None:
    """Test Screening model post-init automatically populates failed flag reasons."""
    screening = Screening(
        reasoning="Manager role identified.",
        is_german_text=False,
        is_german_required=False,
        is_manager=True,
        is_staff=False,
        is_contract=False,
        is_excluded_role=False,
    )
    assert screening.gate_passed is False
    assert "is_manager" in screening.gate_failed_reasons


def test_screening_model_gate_failed_multiple_reasons() -> None:
    """Test Screening model post-init handles multiple failed flags."""
    screening = Screening(
        reasoning="Contract position and German required.",
        is_german_text=False,
        is_german_required=True,
        is_manager=False,
        is_staff=False,
        is_contract=True,
        is_excluded_role=False,
    )
    assert screening.gate_passed is False
    assert "is_german_required" in screening.gate_failed_reasons
    assert "is_contract" in screening.gate_failed_reasons


def test_get_match_percentage_and_checked_passed() -> None:
    """Test helper functions extract values accurately from JobMatchResult."""
    screening_ok = Screening(
        reasoning="Good match",
        is_german_text=False,
        is_german_required=False,
        is_manager=False,
        is_staff=False,
        is_contract=False,
        is_excluded_role=False,
    )
    analysis = Analysis(
        match_percentage=85,
        fit_label="Strong",
        summary="Great background fit.",
        matched_skills=["Python", "AWS"],
        missing_skills=[],
        strengths=["Backend architecture"],
        gaps=[],
    )
    result = JobMatchResult(screening=screening_ok, analysis=analysis)
    assert llm.get_match_percentage(result) == 85
    assert llm.get_checked_passed(result) is True
    assert llm_with_pydantic.get_match_percentage(result) == 85
    assert llm_with_pydantic.get_checked_passed(result) is True

    screening_fail = Screening(
        reasoning="Staff engineer position",
        is_german_text=False,
        is_german_required=False,
        is_manager=False,
        is_staff=True,
        is_contract=False,
        is_excluded_role=False,
    )
    failed_result = JobMatchResult(screening=screening_fail, analysis=None)
    assert llm.get_match_percentage(failed_result) == -1
    assert llm.get_checked_passed(failed_result) is False

    empty_result = JobMatchResult()
    assert llm.get_match_percentage(empty_result) == -1
    assert llm.get_checked_passed(empty_result) is False


def test_review_job_helper() -> None:
    """Test review_job helper executes analyze_resume and returns percentage."""
    mock_result = JobMatchResult(
        analysis=Analysis(
            match_percentage=92,
            fit_label="Excellent",
            summary="Target fit.",
            matched_skills=["Python"],
            missing_skills=[],
            strengths=["Engineering"],
            gaps=[],
        )
    )
    with patch("job_hunt.job_finder.reviewer.llm.analyze_resume", return_value=mock_result):
        score = llm.review_job(job_description="Python developer role", resume="Senior Python dev")
        assert score == 92


def test_both_approaches_supported() -> None:
    """Verify both direct Ollama and Pydantic AI pipelines can be invoked."""
    mock_screening = Screening(
        reasoning="Passed",
        is_german_text=False,
        is_german_required=False,
        is_manager=False,
        is_staff=False,
        is_contract=False,
        is_excluded_role=False,
    )
    mock_analysis = Analysis(
        match_percentage=90,
        fit_label="Strong",
        summary="Matches well",
        matched_skills=["Python"],
        missing_skills=[],
        strengths=["Coding"],
        gaps=[],
    )

    # 1. Test direct Ollama approach in llm.py
    with (
        patch("job_hunt.job_finder.reviewer.llm._get_screening", return_value=mock_screening),
        patch("job_hunt.job_finder.reviewer.llm._get_analysis", return_value=mock_analysis),
    ):
        res1 = llm.analyze_resume("My resume", "Job desc")
        assert res1.screening.gate_passed is True
        assert res1.analysis.match_percentage == 90

    # 2. Test Pydantic AI approach in llm_with_pydantic.py
    with (
        patch("job_hunt.job_finder.reviewer.llm_with_pydantic._get_screening", return_value=mock_screening),
        patch("job_hunt.job_finder.reviewer.llm_with_pydantic._get_analysis", return_value=mock_analysis),
    ):
        res2 = llm_with_pydantic.analyze_resume("My resume", "Job desc")
        assert res2.screening.gate_passed is True
        assert res2.analysis.match_percentage == 90

    # 3. Test delegating from llm.analyze_resume with use_pydantic=True
    with patch("job_hunt.job_finder.reviewer.llm_with_pydantic.analyze_resume") as mock_pydantic_analyze:
        mock_pydantic_analyze.return_value = JobMatchResult(screening=mock_screening, analysis=mock_analysis)
        res3 = llm.analyze_resume("My resume", "Job desc", use_pydantic=True)
        assert mock_pydantic_analyze.called
        assert res3.analysis.match_percentage == 90
