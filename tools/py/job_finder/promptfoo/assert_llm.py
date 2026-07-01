"""Assertion module for Promptfoo evaluation matching tests/llm_test.py."""

import json
import re
import traceback
from typing import Any

from reviewer.llm import (
    Analysis,
    JobMatchResult,
)
from reviewer.llm_test import assert_llm_response


def extract_json_from_text(text: str) -> str | None:
    """Bulletproof JSON extraction that ignores stray '{' in reasoning text."""
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # 1. First, check if the LLM politely used markdown fences

    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence_match:
        try:
            # Validate it's actually JSON before returning
            json.loads(fence_match.group(1))
            return fence_match.group(1)
        except json.JSONDecodeError:
            pass  # Fall back to brute force if the fenced code was invalid

    # 2. If no valid fences, use an iterative brute-force search
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        current_start = start
        while current_start != -1 and current_start < end:
            substring = text[current_start : end + 1]
            try:
                # If this parses without error, we found the REAL JSON block
                json.loads(substring)
                return substring
            except json.JSONDecodeError:
                # If it fails, skip this '{' and find the next one
                current_start = text.find("{", current_start + 1)

    return None


def get_assert(output: str, context: Any) -> dict[str, Any]:  # noqa: ANN401
    """Evaluate LLM output against expected screening gates and match percentage."""
    try:
        raw = output.strip()
        if not raw:
            return {"pass": False, "score": 0.0, "reason": "Empty output received from LLM."}

        # Use the bulletproof extractor
        clean_json_str = extract_json_from_text(raw)

        if not clean_json_str:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Failed to find JSON object in LLM output. Raw output was: {raw!r}",
            }

        try:
            res = JobMatchResult(analysis=Analysis(**json.loads(clean_json_str)))
        except json.JSONDecodeError as je:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Failed to parse LLM output as JSON: {je}. Raw output was: {raw!r}",
            }
        except Exception as e:  # noqa: BLE001
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Unexpected error creating JobMatchResult from JSON: {e}. Raw output was: {raw!r}",
            }

        test_vars = context.get("vars", {})
        min_match = test_vars.get("min_match", 0)
        max_match = test_vars.get("max_match", 100)

        try:
            assert_llm_response(res, min_match, max_match=max_match)
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
