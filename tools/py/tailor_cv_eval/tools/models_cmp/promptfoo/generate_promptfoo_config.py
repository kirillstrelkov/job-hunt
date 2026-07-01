import sys

from helpers.config import DEFAULT_CONFIG
from loguru import logger

from helpers.ollama_helper import get_eval_model, get_model_names
from helpers.promptfoo_helper import get_provider_id
from helpers.tmp_helper import get_root_dir


def main() -> None:
    models = get_model_names()
    eval_model = get_eval_model()
    if eval_model not in models:
        logger.error(
            f"Evaluator model '{eval_model}' is not installed in Ollama. Please run 'ollama pull {eval_model}' first."
        )
        sys.exit(1)

    # Resolve job1_ground_truth path from config
    gt_path = DEFAULT_CONFIG.get_config_value_as_path(".job1_ground_truth")

    providers_list = []
    for m in models:
        providers_list.append(f"""  - id: {get_provider_id(m)}
    config:
      passthrough:
        keep_alive: "0" """)
    providers_yaml = "\n".join(providers_list)

    job = DEFAULT_CONFIG.get_jobs()[0]

    # Generate JD config
    jd_config_content = f"""description: 'CV Tailoring Job Description Evaluation'

commandLineOptions:
  maxConcurrency: 1

prompts:
  - file://{job.llm_prompt_path.resolve()}

providers:
{providers_yaml}

tests:
  - vars:
      expected: file://{gt_path}
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

    # Write config to proper subfolder under get_tmp_output_dir()
    jd_config_dir = job.llm_prompt_path.parent / "promptfoo"
    jd_config_dir.mkdir(parents=True, exist_ok=True)

    jd_config_file = jd_config_dir / "promptfooconfig_jd.yaml"
    jd_config_file.write_text(jd_config_content, encoding="utf-8")

    logger.info(f"Generated {jd_config_file.relative_to(get_root_dir())} successfully.")


if __name__ == "__main__":
    main()
