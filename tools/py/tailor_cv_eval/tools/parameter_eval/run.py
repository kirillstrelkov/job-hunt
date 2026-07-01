import os
import shutil
import subprocess
import sys
from pathlib import Path

from helpers.config import DEFAULT_CONFIG
from loguru import logger

from helpers.ollama_helper import get_eval_model
from helpers.promptfoo_helper import get_provider_id
from helpers.tmp_helper import get_root_dir, get_tmp_folder


def get_npx_command():
    # Check if npx is in the system path
    npx_path = shutil.which("npx")
    if npx_path:
        return npx_path

    # Try typical NVM paths
    home = Path.home()
    nvm_dir = home / ".nvm" / "versions" / "node"
    if nvm_dir.exists():
        # Find the latest node version subdirectory
        node_versions = sorted(nvm_dir.glob("v*"), reverse=True)
        for version in node_versions:
            npx_bin = version / "bin" / "npx"
            if npx_bin.exists():
                # We need to add the bin directory to PATH so node is also found by npx
                os.environ["PATH"] = str(version / "bin") + os.pathsep + os.environ.get("PATH", "")
                return str(npx_bin)

    return "npx"


def main():
    logger.info("=== Starting Promptfoo Parameter Evaluation ===")
    eval_model = get_eval_model()

    # 1. Define paths
    tmp_eval_dir = get_tmp_folder(__file__)

    provider_script = Path(get_root_dir()).parent / "helpers" / "ollama_helper.py"
    job = DEFAULT_CONFIG.get_jobs()[0]
    llm_prompt_file = job.llm_prompt_path

    # 2. Generate target prompt if not present
    if not llm_prompt_file.exists():
        logger.info(f"Generating target prompt since {llm_prompt_file} is missing...")
        script_path = DEFAULT_CONFIG.get_config_value_as_path(".prepare_llm_prompt_script")
        jd_input = Path(get_root_dir()) / "inputs" / "job1" / "input.txt"
        llm_prompt_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [
                    "uv",
                    "run",
                    str(script_path),
                    "--output",
                    str(llm_prompt_file),
                    "--tailor-for-description",
                    "--job-description",
                    str(jd_input),
                ],
                check=True,
                capture_output=True,
            )
            logger.info(f"Target prompt written to {llm_prompt_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running prepare_llm_prompt.py: {e.stderr.decode()}")
            sys.exit(1)

    # 3. Define the parameter variations/configurations to test
    param_variations = [
        {"label": "Temp=0.0 (Baseline)", "config": {"temperature": 0.0}},
        {"label": "Temp=0.5", "config": {"temperature": 0.5}},
        {"label": "Temp=1.0", "config": {"temperature": 1.0}},
        {"label": "Temp=0.7, Top_P=0.9", "config": {"temperature": 0.7, "top_p": 0.9}},
        {"label": "Temp=0.7, Penalty=1.2", "config": {"temperature": 0.7, "repeat_penalty": 1.2}},
    ]

    providers_yaml_list = []
    for variation in param_variations:
        label = variation["label"]
        config = variation["config"]

        config_lines = [f"      model: {eval_model}"]
        for k, v in config.items():
            config_lines.append(f"      {k}: {v}")
        config_yaml = "\n".join(config_lines)

        providers_yaml_list.append(
            f"""  - id: file://{provider_script.resolve()}
    label: '{label}'
    config:
{config_yaml}"""
        )

    providers_yaml = "\n".join(providers_yaml_list)
    gt_file = Path(get_root_dir()) / "inputs" / "job1" / "gt.md"

    # 4. Generate promptfooconfig.yaml
    config_content = f"""description: 'Evaluation of Ollama generation parameters'

commandLineOptions:
  maxConcurrency: 1

prompts:
  - file://{llm_prompt_file.resolve()}

providers:
{providers_yaml}

tests:
  - vars:
      expected: file://{gt_file.resolve()}
    assert:
      - type: similar
        value: "{{{{expected}}}}"
        threshold: 0.7
        provider: ollama:embeddings:{eval_model}
      - type: llm-rubric
        value: "Determine whether the actual output is factually correct based on the expected output: {{{{expected}}}}"
        provider: {get_provider_id(eval_model)}
      - type: rouge-n
        value: "{{{{expected}}}}"
        threshold: 0.3
"""

    config_file = tmp_eval_dir / "promptfooconfig.yaml"
    config_file.write_text(config_content, encoding="utf-8")
    logger.info(f"Generated Promptfoo config at {config_file.relative_to(get_root_dir())}")

    # 5. Run promptfoo
    logger.info("Running Promptfoo parameter evaluation...")
    res = subprocess.run(
        [
            get_npx_command(),
            "-y",
            "promptfoo@latest",
            "eval",
            "-c",
            str(config_file),
            "--no-cache",
        ],
        check=False,
    )
    if res.returncode in [0, 100]:
        logger.info("Evaluation completed!")
        logger.info("To view results in the dashboard, run: npx promptfoo view")
    else:
        logger.error(f"Error running Promptfoo: exit code {res.returncode}")
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()
