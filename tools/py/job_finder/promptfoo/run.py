import sys
from pathlib import Path

from loguru import logger

# Add target directories to sys.path to import reviewer package and helpers
PRJ_ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(PRJ_ROOT_DIR))
sys.path.append(str(PRJ_ROOT_DIR.parent))

from reviewer.llm import CV_PROMPT, JD_PROMPT, SYSTEM_PROMPT_CANDIDATE  # noqa: E402

from helpers.notebook import run_jupyter_notebook  # noqa: E402
from helpers.ollama_helper import get_model_options, get_top_model_names  # noqa: E402
from helpers.promptfoo_helper import convert_json_to_csv, run_promptfoo_eval, write_yaml_config  # noqa: E402
from helpers.tmp_helper import get_tmp_folder  # noqa: E402

MODELS = get_top_model_names()
TMP_DIR = get_tmp_folder(__file__)


def generate_config(models: list[str], tests: list[dict], output_file: Path) -> None:
    """Write static Promptfoo config file."""
    config = {
        "description": "Evaluation of LLM screening and match prompts",
        "prompts": ["{{prompt_content}}"],
        "providers": [
            {
                "id": f"ollama:chat:{model}",
                "config": get_model_options(model),
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


def generate_prompts_and_test_cases(cv_text: str, jd_files: list[Path], tmp_dir: Path) -> list[dict]:
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
        combined_prompt = f"{system_content.strip()}\n\n{cv_content.strip()}\n\n{jd_content.strip()}"

        # Save prompt under tmp/promptfoo/
        prompt_out_file = tmp_dir / f"{jd_file.stem}_prompt.txt"
        prompt_out_file.write_text(combined_prompt, encoding="utf-8")
        logger.info(f"Generated prompt for {jd_file.name} at {prompt_out_file}")

        # Fetch assertions metadata
        meta = test_metadata.get(jd_file.name, {"min_match": 0})

        assert_path = (PRJ_ROOT_DIR / "promptfoo" / "assert_llm.py").resolve()
        tests.append(
            {
                "vars": {
                    "prompt_content": f"file://{jd_file.stem}_prompt.txt",
                    "min_match": meta["min_match"],
                },
                "assert": [{"type": "python", "value": f"file://{assert_path}"}],
            }
        )

    return tests


# run_promptfoo_eval is imported from helpers.promptfoo_helper


def main() -> None:
    """Generate prompts, execute Promptfoo evaluation, and run Jupyter notebook."""
    logger.info("Generating Prompts and Running Promptfoo Evaluation")

    results_json_path = TMP_DIR / f"eval_results_for_{len(MODELS)}_models.json"
    results_csv_path = results_json_path.with_suffix(".csv")

    skip_eval = results_json_path.exists()
    if skip_eval:
        logger.warning(
            f"Evaluation results JSON already exists at {results_json_path}. Skipping Promptfoo evaluation step."
        )

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    cv_text, test_jds = load_data()
    tests = generate_prompts_and_test_cases(cv_text, test_jds, TMP_DIR)

    config_file = TMP_DIR / "promptfoo_config.yaml"
    generate_config(MODELS, tests, config_file)
    logger.info(f"Generated promptfoo_config.yaml config at {config_file}")

    if not skip_eval:
        run_promptfoo_eval(config_file, results_json_path)

    convert_json_to_csv(results_json_path, results_csv_path)

    notebook_path = PRJ_ROOT_DIR / "promptfoo" / "models_analys.ipynb"
    run_jupyter_notebook(notebook_path)


if __name__ == "__main__":
    main()
