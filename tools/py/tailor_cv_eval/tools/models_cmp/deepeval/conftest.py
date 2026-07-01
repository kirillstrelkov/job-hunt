"""Pytest configuration and session hooks for DeepEval model comparisons."""

from typing import Any

import pandas as pd
import pytest
from loguru import logger

from helpers.tmp_helper import get_tmp_output_dir

# Global list to aggregate evaluation results across test cases
EVALUATION_RESULTS: list[dict[str, Any]] = []


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(_session: pytest.Session) -> None:
    """Run initial setup actions before the test session starts."""
    # Ensure outputs directory exists
    get_tmp_output_dir().mkdir(parents=True, exist_ok=True)


def pytest_sessionfinish(_session: pytest.Session, _exitstatus: int) -> None:
    """Analyze gathered results and write a Markdown comparison report when the session finishes."""
    if not EVALUATION_RESULTS:
        logger.warning("No evaluation results gathered.")
        return

    # Generate Markdown Report
    report_path = get_tmp_output_dir().parent / "evaluation_report.md"
    df = pd.DataFrame(EVALUATION_RESULTS)

    # Sort results first by prompt variant, then by DeepEval score descending
    df = df.sort_values(by=["Variant", "Score"], ascending=[True, False])

    # Convert dataframe to a readable markdown table
    markdown_table = df.to_markdown(index=False)

    report_content = f"""# LLM Evaluation Report: CV Tailoring

This report summarizes the performance of different Ollama models when
executing CV tailoring prompts.
Evaluations are executed using **DeepEval** with local models serving as
the evaluator where applicable.

## Model Performance & Comparison Matrix

{markdown_table}

## Context and Diagnostics
- **Prompt Variants**:
  - `jd`: Tailors the CV based on a comprehensive job description
    (`inputs/job1/input.txt`).
- **Outputs**: Detailed tailored CV markdowns are written to the
  `./tmp/outputs/job1` folder for manual review.
- **Scores**: Evaluated against the ground truth profile
  (`inputs/job1/gt.md`) using semantic alignment
  metrics.

*Report generated automatically on {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}.*
"""
    report_path.write_text(report_content, encoding="utf-8")
    logger.info(f"Evaluation complete. Summary report written to: {report_path}")


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line options to control the test run."""
    parser.addoption(
        "--variant",
        action="store",
        default="jd",
        choices=["jd"],
        help="Variant to run (jd)",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate dynamic parameterizations of test inputs during collection."""
    if "variant" in metafunc.fixturenames:
        variant = metafunc.config.getoption("variant")
        metafunc.parametrize("variant", [variant])
