"""Assertion module for Promptfoo evaluation matching tests/llm_test.py."""

import json
import sys
from pathlib import Path
from typing import Any

# Add the tests directory directly to sys.path to avoid package namespace conflicts with 'tests'

TESTS_DIR = Path("/home/kirill/prj/gh/job-hunt/tools/data_fetching/ai_search/tests")
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(TESTS_DIR.parent))

from llm_test import assert_llm_response  # noqa: E402


def get_assert(output: str, context: Any) -> dict:
    """Evaluate LLM output against expected screening gates and match percentage."""
    try:
        raw = output.strip()
        if not raw:
            return {
                "pass": False,
                "score": 0.0,
                "reason": "Empty output received from LLM."
            }

        # Strip markdown code fences if wrapped by the LLM
        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw = "\n".join(lines).strip()

        try:
            res = json.loads(raw)
        except json.JSONDecodeError as je:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Failed to parse LLM output as JSON: {je}. Raw output was: {raw!r}"
            }

        test_vars = context.get("vars", {})
        min_match = test_vars.get("min_match", 0)
        fail_reason = test_vars.get("fail_reason", None)

        try:
            assert_llm_response(res, min_match, fail_reason)
        except AssertionError as ae:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Assertion failed: {ae}"
            }

        return {
            "pass": True,
            "score": 1.0,
            "reason": "All checks passed successfully."
        }
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Unexpected error during assertion evaluation: {e}"
        }

