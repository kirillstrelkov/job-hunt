"""Helper functions for Promptfoo integration and evaluation execution."""

import json
import subprocess
import sys
from pathlib import Path
from typing import ClassVar

import yaml
from loguru import logger

_MAX_GOOD_LATENCY_SEC = 60


class PromptfooCsvCols:
    """CSV column headers for Promptfoo evaluation results."""

    PROVIDER_ID = "Provider Id"
    PROVIDER_LABEL = "Provider Label"
    PROMPT_LABEL = "Prompt Label"
    SUCCESS = "Success"
    SCORE = "Score"
    PASSED = "Passed"
    FAILED = "Failed"
    LATENCY = "Latency (s)"
    PROMPT_TOKENS = "Prompt Tokens"
    COMPLETION_TOKENS = "Completion Tokens"
    TOTAL_TOKENS = "Total Tokens"
    FAILURE_REASON = "Failure Reason"

    # Ordering of columns in the generated CSV
    COLUMNS: ClassVar[list[str]] = [
        PROVIDER_ID,
        PROVIDER_LABEL,
        PROMPT_LABEL,
        SUCCESS,
        SCORE,
        PASSED,
        FAILED,
        LATENCY,
        PROMPT_TOKENS,
        COMPLETION_TOKENS,
        TOTAL_TOKENS,
        FAILURE_REASON,
    ]


def write_yaml_config(config: dict, output_file: Path) -> None:
    """Write Promptfoo configuration dict to a YAML file, using block style for multiline strings."""
    # Setup PyYAML to dump multiline strings using block scalar style (|)
    yaml.SafeDumper.add_representer(
        str,
        lambda dumper, data: (
            dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            if "\n" in data
            else dumper.represent_scalar("tag:yaml.org,2002:str", data)
        ),
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, default_flow_style=False)


def run_promptfoo_eval(config_file: Path, results_json_path: Path) -> None:
    """Execute Promptfoo eval command line tool via subprocess."""
    if results_json_path.exists():
        logger.warning(f"Evaluation results JSON already exists at {results_json_path}. Skipping evaluation.")
        return

    logger.info("Executing Promptfoo evaluation...")
    cmd = [
        "npx",
        "-y",
        "promptfoo@latest",
        "eval",
        "-c",
        str(config_file),
        "--no-cache",
        "-j",
        "1",
        "-o",
        str(results_json_path),
    ]

    res = subprocess.run(cmd, check=False)  # noqa: S603

    if res.returncode not in [0, 100]:
        logger.error(f"Error running Promptfoo: exit code {res.returncode}")
        sys.exit(res.returncode)


def convert_json_to_csv(results_json_path: Path, results_csv_path: Path) -> None:
    """Parse output JSON results and write them as simplified CSV table."""
    logger.info("Evaluation completed. Processing results to CSV...")

    if not results_json_path.exists():
        logger.error(f"Evaluation results JSON not found at: {results_json_path}")
        sys.exit(1)

    try:
        with results_json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        results_list = data.get("results", {}).get("results", [])
        records = []
        for run in results_list:
            provider = run.get("provider", {})
            provider_id = provider.get("id", "unknown")
            provider_label = provider.get("label", "")

            # Set model as provider id
            model = provider_id

            prompt_info = run.get("prompt", {})
            prompt_label = prompt_info.get("label", "")
            if "{{" in prompt_label:
                vars = run["testCase"]["vars"]
                prompt_label = prompt_label.replace("{{", "{").replace("}}", "}").format(**vars)

            success = run.get("success", False)
            latency = run.get("latencyMs", 0) / 1000.0

            token_usage = run.get("tokenUsage") or run.get("response", {}).get("tokenUsage") or {}
            prompt_tokens = token_usage.get("prompt", 0)
            completion_tokens = token_usage.get("completion", 0)
            total_tokens = token_usage.get("total", 0)

            score = run.get("score")
            grading_result = run.get("gradingResult") or {}
            if score is None:
                score = grading_result.get("score", 0.0)

            # Analyze componentResults for Passed and Failed counts
            component_results = grading_result.get("componentResults") or []
            passed_count = sum(1 for res in component_results if isinstance(res, dict) and res.get("pass") is True)
            failed_count = sum(1 for res in component_results if isinstance(res, dict) and res.get("pass") is False)

            fail_reason = ""
            if not success:
                grading_reason = grading_result.get("reason")
                fail_reason = grading_reason or run.get("failureReason") or "Unknown Assertion Error"
                # Strip excessive whitespace or newlines if any
                if isinstance(fail_reason, str):
                    fail_reason = fail_reason.strip().replace("\n", " ")

            if prompt_tokens + completion_tokens > total_tokens:
                logger.warning(
                    f"Prompt tokens {prompt_tokens} + completion tokens {completion_tokens} > total tokens {total_tokens} for {model}."
                )

            records.append(
                {
                    PromptfooCsvCols.PROVIDER_ID: model,
                    PromptfooCsvCols.PROVIDER_LABEL: provider_label,
                    PromptfooCsvCols.PROMPT_LABEL: prompt_label,
                    PromptfooCsvCols.SUCCESS: "PASS" if success else "FAIL",
                    PromptfooCsvCols.SCORE: score,
                    PromptfooCsvCols.PASSED: passed_count,
                    PromptfooCsvCols.FAILED: failed_count,
                    PromptfooCsvCols.LATENCY: latency,
                    PromptfooCsvCols.PROMPT_TOKENS: prompt_tokens,
                    PromptfooCsvCols.COMPLETION_TOKENS: completion_tokens,
                    PromptfooCsvCols.TOTAL_TOKENS: total_tokens,
                    PromptfooCsvCols.FAILURE_REASON: fail_reason,
                }
            )

        import pandas as pd

        # Save to CSV using pandas
        df = pd.DataFrame(records)[PromptfooCsvCols.COLUMNS]
        df.to_csv(results_csv_path, index=False)

        # Warn if latency is too big using df
        slow_runs = df[df[PromptfooCsvCols.LATENCY] > _MAX_GOOD_LATENCY_SEC]
        for _, row in slow_runs.iterrows():
            logger.warning(
                "Latency is too big {} for {}: {}",
                row[PromptfooCsvCols.LATENCY],
                row[PromptfooCsvCols.PROVIDER_ID],
                row[PromptfooCsvCols.PROMPT_LABEL],
            )

        # Print Provider Performance using pandas DataFrame and grouping
        perf_df = df.groupby(PromptfooCsvCols.PROVIDER_ID).agg(
            Passed=(PromptfooCsvCols.PASSED, "sum"),
            Failed=(PromptfooCsvCols.FAILED, "sum"),
        )
        perf_df = (
            perf_df[[PromptfooCsvCols.PASSED, PromptfooCsvCols.FAILED]]
            .reset_index()
            .sort_values(by=PromptfooCsvCols.PASSED, ascending=False)
        )

        logger.info("Provider Performance (Passed / Failed):\n" + perf_df.to_string(index=False))

        logger.info(f"Successfully created: {results_csv_path}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to process JSON results: {e}")
        sys.exit(1)
