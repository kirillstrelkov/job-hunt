import os
import sys
from pathlib import Path

import pandas as pd
import pytest
from loguru import logger

sys.path.append(str(Path(__file__).resolve().parents[3]))
from config import TMP_OUTPUT_DIR

# Global list to aggregate evaluation results across test cases
EVALUATION_RESULTS = []


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Called before runtest loop starts."""
    # Ensure outputs directory exists
    os.makedirs(TMP_OUTPUT_DIR, exist_ok=True)


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished, right before returning the exit status."""
    if not EVALUATION_RESULTS:
        logger.warning("No evaluation results gathered.")
        return

    # Generate Markdown Report
    report_path = TMP_OUTPUT_DIR.parent / "evaluation_report.md"
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
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Evaluation complete. Summary report written to: {report_path}")


def pytest_addoption(parser):
    parser.addoption(
        "--variant",
        action="store",
        default="jd",
        choices=["jd"],
        help="Variant to run (jd)",
    )


def pytest_generate_tests(metafunc):
    if "variant" in metafunc.fixturenames:
        variant = metafunc.config.getoption("variant")
        metafunc.parametrize("variant", [variant])
