"""Script to generate test cases and run Promptfoo evaluations on different LLMs."""

import csv
import json
import subprocess
import sys
from pathlib import Path

from loguru import logger

# Add target directories to sys.path to import reviewer package and helpers
PRJ_ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(PRJ_ROOT_DIR))
sys.path.append(str(PRJ_ROOT_DIR.parent))

from reviewer.llm import CV_PROMPT, JD_PROMPT, SYSTEM_PROMPT_CANDIDATE  # noqa: E402

from helpers.ollama_helper import get_model_names  # noqa: E402
from helpers.promptfoo_helper import run_promptfoo_eval, write_yaml_config  # noqa: E402
from helpers.tmp_helper import get_tmp_folder  # noqa: E402

MODELS = get_model_names()


def generate_config(models: list[str], tests: list[dict], output_file: Path) -> None:
    """Write static Promptfoo config file."""
    config = {
        "description": "Evaluation of LLM screening and match prompts",
        "prompts": ["{{prompt_content}}"],
        "providers": [
            {
                "id": f"ollama:chat:{model}",
                "config": {
                    "temperature": 0,
                    "num_ctx": 16384,
                    "num_predict": 3072,
                    "seed": 42,
                    "keep_alive": 0,
                },
            }
            for model in models
        ],
        "tests": tests,
    }

    write_yaml_config(config, output_file)


def load_data() -> tuple[str, list[Path]]:
    """Load CV text and test Job Descriptions."""
    cv_path = PRJ_ROOT_DIR / "data" / "private" / "cv.txt"
    if not cv_path.exists():
        logger.error(f"CV file not found at: {cv_path}")
        sys.exit(1)

    try:
        cv_text = cv_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error(f"Failed to read CV file: {e}")
        sys.exit(1)

    test_jds = list((PRJ_ROOT_DIR / "data" / "test").glob("*.txt"))
    if not test_jds:
        logger.error("No test JDs found in data/test/*.txt")
        sys.exit(1)

    return cv_text, test_jds


def generate_prompts_and_test_cases(
    cv_text: str, jd_files: list[Path], tmp_dir: Path
) -> list[dict]:
    """Combine system, CV, and JD prompts, save them under tmp_dir, and construct test cases list."""
    tests = []

    # Map each JD to its corresponding expected screening gate or match percentage
    test_metadata = {
        "tesla_go.txt": {"min_match": 60},
        "moia.txt": {"min_match": 60},
        "not_manager.txt": {"min_match": 60},
        "manager.txt": {"min_match": 30},
        "staff.txt": {"min_match": 30},
        "contract.txt": {"min_match": 60},
        "sen_qa.txt": {"min_match": 70},
        "intern.txt": {"min_match": 60},
    }

    for jd_file in jd_files:
        jd_text = jd_file.read_text(encoding="utf-8")

        # Combine system prompt, cv, and job description
        cv_content = CV_PROMPT.format(cv=cv_text.strip())
        jd_content = JD_PROMPT.format(job_description=jd_text.strip())
        system_content = SYSTEM_PROMPT_CANDIDATE
        combined_prompt = (
            f"{system_content.strip()}\n\n{cv_content.strip()}\n\n{jd_content.strip()}"
        )

        # Save prompt under tmp/promptfoo/
        prompt_out_file = tmp_dir / f"{jd_file.stem}_prompt.txt"
        prompt_out_file.write_text(combined_prompt, encoding="utf-8")
        logger.info(
            f"Generated prompt for {jd_file.name} at {prompt_out_file.relative_to(PRJ_ROOT_DIR)}"
        )

        # Fetch assertions metadata
        meta = test_metadata.get(jd_file.name, {"min_match": 0})

        # Build test case
        tests.append(
            {
                "vars": {
                    "prompt_content": f"file://{jd_file.stem}_prompt.txt",
                    "min_match": meta["min_match"],
                },
                "assert": [
                    {"type": "python", "value": "file://../../promptfoo/assert_llm.py"}
                ],
            }
        )

    return tests


# run_promptfoo_eval is imported from helpers.promptfoo_helper


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
            provider = run.get("provider", {}).get("id", "unknown")
            model = provider.replace("ollama:chat:", "")

            vars_dict = run.get("vars", {})
            prompt_file = vars_dict.get("prompt_content", "").replace("file://", "")
            jd_name = Path(prompt_file).name.replace("_prompt.txt", "")

            success = run.get("success", False)
            latency = run.get("latencyMs", 0) / 1000.0

            token_usage = (
                run.get("tokenUsage") or run.get("response", {}).get("tokenUsage") or {}
            )
            prompt_tokens = token_usage.get("prompt", 0)
            completion_tokens = token_usage.get("completion", 0)
            total_tokens = token_usage.get("total", 0)

            fail_reason = ""
            if not success:
                grading_reason = run.get("gradingResult", {}).get("reason")
                fail_reason = (
                    grading_reason
                    or run.get("failureReason")
                    or "Unknown Assertion Error"
                )
                # Strip excessive whitespace or newlines if any
                if isinstance(fail_reason, str):
                    fail_reason = fail_reason.strip().replace("\n", " ")

            records.append(
                {
                    "Model": model,
                    "Job Description": jd_name,
                    "Success": "PASS" if success else "FAIL",
                    "Latency (s)": latency,
                    "Prompt Tokens": prompt_tokens,
                    "Completion Tokens": completion_tokens,
                    "Total Tokens": total_tokens,
                    "Failure Reason": fail_reason,
                }
            )

        fieldnames = [
            "Model",
            "Job Description",
            "Success",
            "Latency (s)",
            "Prompt Tokens",
            "Completion Tokens",
            "Total Tokens",
            "Failure Reason",
        ]
        with results_csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        # Count passed / total per model
        model_stats = {}
        for r in records:
            m = r["Model"]
            if m not in model_stats:
                model_stats[m] = {"passed": 0, "total": 0}
            model_stats[m]["total"] += 1
            if r["Success"] == "PASS":
                model_stats[m]["passed"] += 1

        logger.info("=== Model Performance (Passed / Total) ===")
        for m, stats in sorted(model_stats.items()):
            logger.info(f"Model: {m:<30} | Passed: {stats['passed']}/{stats['total']}")

        logger.info(
            f"Successfully created: {results_csv_path.relative_to(PRJ_ROOT_DIR)}"
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to process JSON results: {e}")
        sys.exit(1)


def main() -> None:
    """Generate prompts, execute Promptfoo evaluation, and run Jupyter notebook."""
    logger.info("=== Generating Prompts and Running Promptfoo Evaluation ===")

    tmp_dir = get_tmp_folder(__file__)
    results_json_path = tmp_dir / f"eval_results_for_{len(MODELS)}_models.json"
    results_csv_path = results_json_path.with_suffix(".csv")

    skip_eval = results_json_path.exists()
    if skip_eval:
        logger.warning(
            f"Evaluation results JSON already exists at {results_json_path.relative_to(PRJ_ROOT_DIR)}. "
            "Skipping Promptfoo evaluation step."
        )

    tmp_dir.mkdir(parents=True, exist_ok=True)

    cv_text, test_jds = load_data()
    tests = generate_prompts_and_test_cases(cv_text, test_jds, tmp_dir)

    config_file = tmp_dir / "promptfoo_config.yaml"
    generate_config(MODELS, tests, config_file)
    logger.info(
        f"Generated promptfoo_config.yaml config at {config_file.relative_to(PRJ_ROOT_DIR)}"
    )

    if not skip_eval:
        run_promptfoo_eval(config_file, results_json_path)

    convert_json_to_csv(results_json_path, results_csv_path)

    notebook_path = PRJ_ROOT_DIR / "promptfoo" / "models_analys.ipynb"
    run_jupyter_notebook(notebook_path)


def run_jupyter_notebook(notebook_path: Path) -> None:
    """Execute all cells in the Jupyter notebook in-place."""
    logger.info(f"Executing Jupyter notebook: {notebook_path.name}...")
    if not notebook_path.exists():
        logger.error(f"Jupyter notebook not found at: {notebook_path}")
        sys.exit(1)

    res = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "uv",
            "run",
            "--with",
            "nbconvert",
            "--with",
            "ipykernel",
            "--with",
            "pandas",
            "--with",
            "matplotlib",
            "--with",
            "seaborn",
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--inplace",
            str(notebook_path),
        ],
        check=False,
    )

    if res.returncode != 0:
        logger.error(f"Error executing Jupyter notebook: exit code {res.returncode}")
        sys.exit(res.returncode)

    logger.info("Jupyter notebook executed successfully.")


if __name__ == "__main__":
    main()
