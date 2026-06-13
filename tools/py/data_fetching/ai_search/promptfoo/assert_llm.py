"""Assertion module for Promptfoo evaluation matching tests/llm_test.py."""

import traceback
from reviewer.llm import Analysis
import json
import sys
from pathlib import Path
from typing import Any

# Add the tests directory directly to sys.path to avoid package namespace conflicts with 'tests'

AI_SEARCH_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_SEARCH_DIR))

from reviewer.llm_test import assert_llm_response  # noqa: E402
from reviewer.llm import JobMatchResult


def get_assert(output: str, context: Any) -> dict[str, Any]:  # noqa: ANN401
    """Evaluate LLM output against expected screening gates and match percentage."""
    try:
        raw = output.strip()
        if not raw:
            return {"pass": False, "score": 0.0, "reason": "Empty output received from LLM."}

        try:
            res = JobMatchResult(analysis=Analysis(**json.loads(raw)))
        except json.JSONDecodeError as je:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Failed to parse LLM output as JSON: {je}. Raw output was: {raw!r}",
            }
        except Exception as e:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Unexpected error creating JobMatchResult from JSON: {e}. Raw output was: {raw!r}",
            }

        test_vars = context.get("vars", {})
        min_match = test_vars.get("min_match", 0)

        try:
            assert_llm_response(res, min_match)
        except AssertionError as ae:
            return {"pass": False, "score": 0.0, "reason": f"Assertion failed: {ae}"}
    except Exception:  # noqa: BLE001
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Unexpected error during assertion evaluation: {traceback.format_exc()}",
        }
    else:
        return {"pass": True, "score": 1.0, "reason": "All checks passed successfully."}
