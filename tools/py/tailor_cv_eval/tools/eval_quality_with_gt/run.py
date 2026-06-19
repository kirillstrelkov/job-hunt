import argparse
import shutil
import sys
from pathlib import Path

import yaml
from loguru import logger

# Add root directory to path to import shared_config and ollama_helper
sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parents[3]))
from helpers.config import DEFAULT_CONFIG  # noqa: E402
from helpers.notebook import run_jupyter_notebook  # noqa: E402
from helpers.ollama_helper import (
    check_if_file_fits_into_ctx_num,
    get_eval_model,
    get_model_options,
    get_top_model_names,
)  # noqa: E402
from helpers.promptfoo_helper import (  # noqa: E402
    convert_json_to_csv,
    run_promptfoo_eval,
    write_yaml_config,
)
from helpers.tmp_helper import get_root_dir, get_tmp_folder  # noqa: E402

# Global path definitions for Promptfoo evaluation
TMP_EVAL_DIR = get_tmp_folder(__file__)
CONFIG_FILE = TMP_EVAL_DIR / "promptfoo_cfg.yaml"
RESULTS_JSON = TMP_EVAL_DIR / "promptfoo_results.json"
RESULTS_CSV = RESULTS_JSON.with_suffix(".csv")
NOTEBOOK_PATH = Path(__file__).resolve().parent / "result_analysis.ipynb"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

PROMPTFOO_CONFIG_TEMPLATE = """
description: Evaluation of prepare_llm_prompt.py prompts
commandLineOptions:
  maxConcurrency: 1
prompts: [] # Dynamically populated from candidate prompt files
providers: [] # Dynamically populated from config.yaml models
tests:
  - vars:
      expected: file://{{GT_FILE}} # Dynamically populated ground truth file path
    assert:
      - type: contains
        value: "PART 1"
      - type: contains
        value: "PART 2"
      - type: icontains-any
        value:
          - "PART 3"
          - "ADDITIONAL OPTIONS"
      - type: contains
        value: "CARIAD SE"
      - type: contains
        value: "Argo AI GmbH"
      - type: contains
        value: "Airbus Operations GmbH"
      - type: contains
        value: "ESR Labs AG"
      - type: contains
        value: "HERE Deutschland GmbH"
      - type: contains
        value: "Helpling GmbH"
      - type: contains
        value: "Satprof"
      - type: contains
        value: "Betsson Group"
      - type: contains
        value: "Ixonos Estonia OÜ"
      - type: not-icontains-all
        value:
          - "Spearhead"
          - "Streamline"
          - "Adept"
      - type: javascript
        value: /Work Experience.*Projects.*Courses and Certificates/is.test(output)
      - type: contains
        value: "**Software Engineer** | _CARIAD SE, Berlin, Germany_ | Oct 2023 - Aug 2025"
      - type: contains
        value: "Certified Kubernetes Application Developer, _Cloud Native Computing Foundation_ | Feb 2026"
      - type: contains
        value: "**[University of Helsinki DevOps Labs: Cloud-Native Microservices](https://github.com/kirillstrelkov/KubernetesSubmissions)** | 2026"
      - type: python
        value: len(output) > 4000
      - type: python
        value: len(output.splitlines()) > 70
      - type: similar
        value: '{{expected}}'
        threshold: 0.7
        provider: 
          id: ollama:embeddings:qwen3-embedding:0.6b
          config:
            num_ctx: 32768
      - type: llm-rubric
        value: |
          Compare the actual output to the expected output: {{expected}}.
          Ensure that:
          1. The 'PART 1' tailored resume is factually aligned with the expected
          resume, without hallucinating jobs or skills.
          2. The justifications and additional options (PART 2 and 3)
          make logical sense and match the expected reasoning.
          3. The output is in pure Markdown without conversational filler.
        provider: ollama:chat:{{EVAL_MODEL}} # Dynamically resolved evaluation model for grading
      - type: rouge-n
        value: '{{expected}}'
        threshold: 0.3
      - type: factuality
        value: '{{expected}}'
        provider: ollama:chat:{{EVAL_MODEL}} # Dynamically resolved evaluation model for grading
"""


def generate_config(prompt_files: list[Path], gt_file: Path, output_file: Path) -> None:
    """Load configuration template, resolve placeholder values, and write output config file."""
    eval_model = get_eval_model()

    template_text = PROMPTFOO_CONFIG_TEMPLATE.replace("{{EVAL_MODEL}}", eval_model)
    template_text = template_text.replace("{{GT_FILE}}", str(gt_file.resolve()))

    config = yaml.safe_load(template_text)
    config["prompts"] = [f"file://{pf.resolve()}" for pf in prompt_files]

    models = get_top_model_names()
    models_str = "\n".join(models)
    logger.debug(f"Using {len(models)} models:\n{models_str}")

    providers = []
    for model in models:
        base_options = get_model_options(model)
        ctx_num = base_options["num_ctx"]
        label = f"{model} (ctx={ctx_num}, pred={base_options['num_predict']}, temp={base_options['temperature']})"
        providers.append(
            {
                "id": f"ollama:chat:{model}",
                "label": label,
                "config": base_options,
            }
        )

        for prompt_file in prompt_files:
            if not check_if_file_fits_into_ctx_num(prompt_file, ctx_num):
                raise ValueError(f"File {prompt_file} does not fit into context window of {ctx_num} tokens.")

    config["providers"] = providers

    write_yaml_config(config, output_file)
    logger.info(f"Generated Promptfoo config at {output_file.relative_to(get_root_dir())}")


def get_prompt_files(prompts_dir: Path, baseline_prompt_file: Path) -> list[Path]:
    """Retrieve candidate prompt files from prompts_dir, prompting the user if none are found."""
    prompt_files = list(prompts_dir.glob("*.md"))
    if not prompt_files:
        logger.warning(f"No prompt files (*.md) found in: {prompts_dir}")
        if baseline_prompt_file.exists():
            logger.info(
                f"You can use the baseline prompt generated at:\n  {baseline_prompt_file}\n"
                f"as a base. Copy it or create your candidate prompt *.md files in: {prompts_dir}"
            )
        else:
            logger.info(
                f"No baseline prompt was found at:\n  {baseline_prompt_file}\n"
                f"Please create your candidate prompt *.md files in: {prompts_dir}"
            )
        logger.error(f"Add your prompts to {prompts_dir}")
        sys.exit(1)

    prompt_files.append(baseline_prompt_file)

    return prompt_files


def main():
    parser = argparse.ArgumentParser(description="Run Promptfoo prompt evaluation")
    parser.add_argument("--force", action="store_true", help="Remove evaluation temp directory before starting")
    parser.add_argument("--gt-only", action="store_true", help="Use only the baseline ground truth prompt file")
    parser.add_argument(
        "--prompt",
        action="extend",
        nargs="+",
        type=Path,
        help="Path(s) to candidate prompt files to evaluate. Supports multiple paths.",
    )
    args = parser.parse_args()

    logger.info("Starting Promptfoo Prompt Evaluation")

    if args.force:
        if TMP_EVAL_DIR.exists():
            logger.info(f"Removing temporary evaluation directory: {TMP_EVAL_DIR}")
            shutil.rmtree(TMP_EVAL_DIR)

    TMP_EVAL_DIR.mkdir(parents=True, exist_ok=True)

    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    job = DEFAULT_CONFIG.get_jobs()[0]
    baseline_prompt_file = job.llm_prompt_path

    if args.prompt:
        if args.gt_only:
            logger.error("Cannot specify both --prompt and --gt-only")
            sys.exit(1)
        prompt_files = []
        for pf in args.prompt:
            if not pf.exists():
                logger.error(f"Prompt file not found: {pf}")
                sys.exit(1)
            prompt_files.append(pf)
    elif args.gt_only:
        if not baseline_prompt_file.exists():
            logger.error(f"Baseline prompt file not found: {baseline_prompt_file}")
            sys.exit(1)
        prompt_files = [baseline_prompt_file]
    else:
        prompt_files = get_prompt_files(PROMPTS_DIR, baseline_prompt_file)

    logger.info(f"Evaluating {len(prompt_files)} prompts:")
    for pf in prompt_files:
        logger.info(f"  - {pf.name}")

    gt_file = job.ground_truth_path
    if not gt_file.exists():
        logger.error(f"Ground truth file not found: {gt_file}")
        sys.exit(1)

    generate_config(prompt_files, gt_file, CONFIG_FILE)

    run_promptfoo_eval(CONFIG_FILE, RESULTS_JSON)
    convert_json_to_csv(RESULTS_JSON, RESULTS_CSV)

    # Run the Jupyter Notebook for visual/markdown analysis
    run_jupyter_notebook(NOTEBOOK_PATH)

    logger.info("Evaluation completed!")
    logger.info("To view results in the dashboard, run: just view-promptfoo")


if __name__ == "__main__":
    main()
