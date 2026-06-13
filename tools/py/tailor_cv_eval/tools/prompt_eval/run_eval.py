import subprocess
import sys
from pathlib import Path

import yaml
from loguru import logger

# Add root directory to path to import shared_config and ollama_helper
sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parents[3]))
from helpers.config import LLM_PROMPT_OUTPUT_FILE, ROOT_DIR, TMP_OUTPUT_DIR
from helpers.ollama_helper import get_eval_model, get_model_options, get_model_names

PROMPTFOO_CONFIG_TEMPLATE = (
    """
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
      - type: contains-any
        value:
          - PART 3"
          - "Additional Options"
      - type: regex
        value: |
          (?s)Work Experience.*Projects.*Courses and Certificates
      - type: contains
        value: "**Software Engineer** | _CARIAD SE, Berlin, Germany_ | Oct 2023 - Aug 2025"
      - type: contains
        value: "Certified Kubernetes Application Developer, _Cloud Native Computing Foundation_ | Feb 2026"
      - type: contains
"""
    '        value: "**[University of Helsinki DevOps Labs: '
    'Cloud-Native Microservices](https://github.com/kirillstrelkov/KubernetesSubmissions)** | 2026"\n'
    """      - type: python
        value: len(output) > 4000
      - type: python
        value: len(output.splitlines()) > 70
      - type: similar
        value: '{{expected}}'
        threshold: 0.7
        provider: ollama:embeddings:{{EVAL_MODEL}} # Dynamically resolved evaluation model for embeddings
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
"""
)


def generate_config(prompt_files: list[Path], gt_file: Path, output_file: Path) -> None:
    """Load configuration template, resolve placeholder values, and write output config file."""
    eval_model = get_eval_model()
    models = get_model_names()

    template_text = PROMPTFOO_CONFIG_TEMPLATE.replace("{{EVAL_MODEL}}", eval_model)
    template_text = template_text.replace("{{GT_FILE}}", str(gt_file.resolve()))

    config = yaml.safe_load(template_text)
    config["prompts"] = [f"file://{pf.resolve()}" for pf in prompt_files]

    # Dynamically build the providers list starting with the EVAL_MODEL provider
    providers = [
        {
            "id": f"ollama:chat:{eval_model}",
            "config": {"passthrough": {"keep_alive": "0"}, **get_model_options(eval_model)},
        }
    ]

    # Add the remaining models from config.yaml
    for m in models:
        if m != eval_model:
            providers.append(
                {"id": f"ollama:chat:{m}", "config": {"passthrough": {"keep_alive": "0"}, **get_model_options(m)}}
            )

    config["providers"] = providers

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
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, default_flow_style=False)
    logger.info(f"Generated Promptfoo config at {output_file.relative_to(ROOT_DIR)}")


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

    return prompt_files


def main():
    logger.info("=== Starting Promptfoo Prompt Evaluation ===")

    tmp_eval_dir = Path(TMP_OUTPUT_DIR) / "prompt_eval"
    tmp_eval_dir.mkdir(parents=True, exist_ok=True)

    prompts_dir = Path(ROOT_DIR) / "tools" / "prompt_eval" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    baseline_prompt_file = Path(TMP_OUTPUT_DIR) / "job1" / LLM_PROMPT_OUTPUT_FILE

    prompt_files = get_prompt_files(prompts_dir, baseline_prompt_file)

    logger.info(f"Evaluating {len(prompt_files)} prompts:")
    for pf in prompt_files:
        logger.info(f"  - {pf.name}")

    gt_file = Path(ROOT_DIR) / "inputs" / "job1" / "gt.md"
    config_file = tmp_eval_dir / "promptfoo_cfg.yaml"

    generate_config(prompt_files, gt_file, config_file)

    logger.info("Running Promptfoo evaluation...")
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
        ],
        check=False,
    )
    if res.returncode in [0, 100]:
        logger.info("Evaluation completed!")
        logger.info("To view results in the dashboard, run: just view-promptfoo")
    else:
        logger.error(f"Error running Promptfoo: exit code {res.returncode}")
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()
