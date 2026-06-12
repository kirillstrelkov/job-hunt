import csv
import json
import subprocess
import sys
from pathlib import Path

import yaml
from loguru import logger

# Add target directories to sys.path to import llm.py
AI_SEARCH_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(AI_SEARCH_DIR))

try:
    from llm import CV_PROMPT, JD_PROMPT, SYSTEM_PROMPT
except ImportError as e:
    logger.error(f"Failed to import from llm.py: {e}")
    sys.exit(1)


MODELS = [
    "deepseek-r1:1.5b",
    "gemma4:e2b",
    "gemma4:e2b-it-qat",
    "llama3.2:3b-instruct-q8_0",
    "qwen2.5:3b-instruct-q8_0",
    "gemma4:e4b-it-qat",
    "qwen3.5:4b-q8_0",
    "deepseek-r1:7b",
    "qwen2.5:7b",
    "qwen2.5-coder:7b",
    "codegemma:7b-code",
    "mistral:7b-instruct-v0.3-q4_K_M",
    "qwen2.5:7b-instruct-q4_K_M",
    "llama3.1:8b",
    "llama3.1:8b-instruct-q6_K",
    "llama3.1:8b-text-q4_K_M",
    "gemma2:9b-instruct-q5_K_M",
    "qwen3.5:9b-q4_K_M",
    "gemma4:12b-it-qat",
]


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

    # Setup PyYAML to dump multiline strings using block scalar style (|)
    yaml.SafeDumper.add_representer(
        str,
        lambda dumper, data: (
            dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            if "\n" in data
            else dumper.represent_scalar("tag:yaml.org,2002:str", data)
        ),
    )

    with output_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, default_flow_style=False)


def load_data() -> tuple[str, list[Path]]:
    """Load CV text and test Job Descriptions."""
    cv_path = AI_SEARCH_DIR / "data" / "private" / "cv.txt"
    if not cv_path.exists():
        logger.error(f"CV file not found at: {cv_path}")
        sys.exit(1)

    try:
        cv_text = cv_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error(f"Failed to read CV file: {e}")
        sys.exit(1)

    test_jds = list((AI_SEARCH_DIR / "data" / "test").glob("*.txt"))
    if not test_jds:
        logger.error("No test JDs found in data/test/*.txt")
        sys.exit(1)

    return cv_text, test_jds


def generate_prompts_and_test_cases(cv_text: str, jd_files: list[Path], tmp_dir: Path) -> list[dict]:
    """Combine system, CV, and JD prompts, save them under tmp_dir, and construct test cases list."""
    tests = []

    # Map each JD to its corresponding expected screening gate or match percentage
    test_metadata = {
        "tesla_go.txt": {"min_match": 60, "fail_reason": ""},
        "moia.txt": {"min_match": 30, "fail_reason": ""},
        "not_manager.txt": {"min_match": 60, "fail_reason": ""},
        "manager.txt": {"min_match": 0, "fail_reason": "is_manager"},
        "staff.txt": {"min_match": 0, "fail_reason": "is_staff"},
        "contract.txt": {"min_match": 0, "fail_reason": "is_contract"},
        "sen_qa.txt": {"min_match": 20, "fail_reason": ""},
        "intern.txt": {"min_match": 0, "fail_reason": "is_excluded_role"},
    }

    for jd_file in jd_files:
        jd_text = jd_file.read_text(encoding="utf-8")

        # Combine system prompt, cv, and job description
        cv_content = CV_PROMPT.format(cv=cv_text.strip())
        jd_content = JD_PROMPT.format(job_description=jd_text.strip())
        system_content = SYSTEM_PROMPT.replace("80%%", "80%")
        combined_prompt = f"{system_content.strip()}\n\n{cv_content.strip()}\n\n{jd_content.strip()}"

        # Save prompt under tmp/promptfoo/
        prompt_out_file = tmp_dir / f"{jd_file.stem}_prompt.txt"
        prompt_out_file.write_text(combined_prompt, encoding="utf-8")
        logger.info(f"Generated prompt for {jd_file.name} at {prompt_out_file.relative_to(AI_SEARCH_DIR)}")

        # Fetch assertions metadata
        meta = test_metadata.get(jd_file.name, {"min_match": 0, "fail_reason": ""})

        # Build test case
        tests.append(
            {
                "vars": {
                    "prompt_content": f"file://{jd_file.stem}_prompt.txt",
                    "min_match": meta["min_match"],
                    "fail_reason": meta["fail_reason"],
                },
                "assert": [{"type": "python", "value": "file://../../promptfoo/assert_llm.py"}],
            }
        )

    return tests


def run_promptfoo_eval(config_file: Path, results_json_path: Path) -> None:
    """Execute Promptfoo eval command line tool."""
    logger.info("Executing Promptfoo evaluation...")
    res = subprocess.run(
        [
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
    )

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
            provider = run.get("provider", {}).get("id", "unknown")
            model = provider.replace("ollama:chat:", "")

            vars_dict = run.get("vars", {})
            prompt_file = vars_dict.get("prompt_content", "").replace("file://", "")
            jd_name = Path(prompt_file).name.replace("_prompt.txt", "")

            success = run.get("success", False)
            latency = run.get("latencyMs", 0) / 1000.0

            token_usage = run.get("tokenUsage") or run.get("response", {}).get("tokenUsage") or {}
            prompt_tokens = token_usage.get("prompt", 0)
            completion_tokens = token_usage.get("completion", 0)
            total_tokens = token_usage.get("total", 0)

            fail_reason = ""
            if not success:
                grading_reason = run.get("gradingResult", {}).get("reason")
                fail_reason = grading_reason or run.get("failureReason") or "Unknown Assertion Error"
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

        logger.info(f"Successfully created: {results_csv_path.relative_to(AI_SEARCH_DIR)}")
    except Exception as e:
        logger.error(f"Failed to process JSON results: {e}")
        sys.exit(1)


def main():
    logger.info("=== Generating Prompts and Running Promptfoo Evaluation ===")

    tmp_dir = AI_SEARCH_DIR / "tmp" / "promptfoo"
    results_json_path = tmp_dir / f"eval_results_for_{len(MODELS)}_models.json"
    results_csv_path = results_json_path.with_suffix(".csv")

    skip_eval = results_json_path.exists()
    if skip_eval:
        logger.warning(
            f"Evaluation results JSON already exists at {results_json_path.relative_to(AI_SEARCH_DIR)}. "
            "Skipping Promptfoo evaluation step."
        )

    tmp_dir.mkdir(parents=True, exist_ok=True)

    cv_text, test_jds = load_data()
    tests = generate_prompts_and_test_cases(cv_text, test_jds, tmp_dir)

    config_file = tmp_dir / "promptfoo_config.yaml"
    generate_config(MODELS, tests, config_file)
    logger.info(f"Generated promptfoo_config.yaml config at {config_file.relative_to(AI_SEARCH_DIR)}")

    if not skip_eval:
        run_promptfoo_eval(config_file, results_json_path)

    convert_json_to_csv(results_json_path, results_csv_path)

    notebook_path = AI_SEARCH_DIR / "promptfoo" / "models_analys.ipynb"
    run_jupyter_notebook(notebook_path)


def run_jupyter_notebook(notebook_path: Path) -> None:
    """Execute all cells in the Jupyter notebook in-place."""
    logger.info(f"Executing Jupyter notebook: {notebook_path.name}...")
    if not notebook_path.exists():
        logger.error(f"Jupyter notebook not found at: {notebook_path}")
        sys.exit(1)

    res = subprocess.run(
        [
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
        ]
    )

    if res.returncode != 0:
        logger.error(f"Error executing Jupyter notebook: exit code {res.returncode}")
        sys.exit(res.returncode)

    logger.info("Jupyter notebook executed successfully.")


if __name__ == "__main__":
    main()
