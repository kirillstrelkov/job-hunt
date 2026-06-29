"""Reviewer package for evaluating job postings and CVs."""

# TODO: fix imports - rename llm_.py to something better
from llm_ import (
    JobMatchResult,
    _get_analysis,
    _get_screening,
    analyze_cv,
    get_checked_passed,
    get_match_percentage,
)
