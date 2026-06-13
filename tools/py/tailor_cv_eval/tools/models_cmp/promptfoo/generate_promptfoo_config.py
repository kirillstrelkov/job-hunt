import sys
from pathlib import Path

from loguru import logger

sys.path.append(str(Path(__file__).resolve().parents[3]))
sys.path.append(str(Path(__file__).resolve().parents[4]))
from config import LLM_PROMPT_OUTPUT_FILE, ROOT_DIR, TMP_OUTPUT_DIR
from helpers.ollama_helper import get_eval_model, get_models


def main():
    models = get_models()
    eval_model = get_eval_model()
    if eval_model not in models:
        logger.error(
            f"Evaluator model '{eval_model}' is not installed in Ollama. Please run 'ollama pull {eval_model}' first."
        )
        sys.exit(1)

    providers_list = []
    for m in models:
        providers_list.append(f"""  - id: ollama:chat:{m}
    config:
      passthrough:
        keep_alive: "0" """)
    providers_yaml = "\n".join(providers_list)

    # Generate JD config
    jd_config_content = f"""description: 'CV Tailoring Job Description Evaluation'

commandLineOptions:
  maxConcurrency: 1

prompts:
  - file://{Path(TMP_OUTPUT_DIR).resolve()}/job1/{LLM_PROMPT_OUTPUT_FILE}

providers:
{providers_yaml}

tests:
  - vars:
      expected: file://{Path(ROOT_DIR).resolve()}/inputs/job1/gt.md
    assert:
      - type: similar
        value: "{{{{expected}}}}"
        threshold: 0.7
        provider: ollama:embeddings:{eval_model}
      - type: llm-rubric
        value: "Determine whether the actual output is factually correct based on the expected output: {{{{expected}}}}"
        provider: ollama:chat:{eval_model}
      - type: rouge-n
        value: "{{{{expected}}}}"
        threshold: 0.3
"""

    # Write config to proper subfolder under TMP_OUTPUT_DIR
    jd_config_dir = Path(TMP_OUTPUT_DIR) / "job1" / "promptfoo"
    jd_config_dir.mkdir(parents=True, exist_ok=True)

    jd_config_file = jd_config_dir / "promptfooconfig_jd.yaml"
    jd_config_file.write_text(jd_config_content, encoding="utf-8")

    logger.info(f"Generated {jd_config_file.relative_to(ROOT_DIR)} successfully.")


if __name__ == "__main__":
    main()
