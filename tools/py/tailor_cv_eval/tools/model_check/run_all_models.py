#!/usr/bin/env python
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

# Find workspace root directory dynamically starting from current file
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from config import ConfigManager  # noqa: E402
from tools.config_generator import create_config  # noqa: E402
from tools.ollama_helper import run_model  # noqa: E402

RESULTS_DIR = ROOT_DIR / "tmp/outputs/model_check"
CONFIG_DIR = ROOT_DIR / "tmp/inputs/model_check"


def save_and_log_statistics(stats: list[dict], results_dir: Path, run_name: str | None = None) -> None:
    """Create a DataFrame from statistics, save it as CSV, and print a Markdown table to logs."""
    df = pd.DataFrame(stats)

    # Reorder columns for presentation
    columns_order = [
        "model",
        "total_time",
        "load_time",
        "prompt_tokens",
        "gen_tokens",
        "tokens_per_sec",
        "char_count",
        "word_count",
        "gpu_usage",
        "gpu_info",
        "options_str",
    ]

    # Ensure all columns exist
    for col in columns_order:
        if col not in df.columns:
            df[col] = None

    df = df[columns_order]

    # Rename columns for presentation
    df.columns = [
        "Model",
        "Total Time (s)",
        "Load Time (s)",
        "Prompt Tokens",
        "Gen Tokens",
        "Gen Speed (t/s)",
        "Response Chars",
        "Response Words",
        "GPU Usage",
        "GPU Info",
        "Options",
    ]

    # Make sure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    # Output file base name
    suffix = f"_{run_name}" if run_name else ""
    csv_name = f"model_comparison{suffix}.csv"

    # Save DataFrame as CSV
    csv_output_path = results_dir / csv_name
    df.to_csv(csv_output_path, index=False)
    logger.info(f"Saved statistics data table to CSV: {csv_output_path}")

    # Generate Markdown representation for logging
    markdown_table = df.to_markdown(index=False)

    # Log data table to stdout
    logger.info(f"\nModel Evaluation Statistics ({run_name or 'custom'}):\n\n{markdown_table}\n")


def run_evaluation_for_config(config_path: Path, run_name: str | None = None):
    # Output file base name
    suffix = f"_{run_name}" if run_name else ""
    csv_name = f"model_comparison{suffix}.csv"
    csv_output_path = RESULTS_DIR / csv_name

    if csv_output_path.exists():
        logger.warning(
            f"CSV output file already exists at {csv_output_path}. Skipping evaluation for run: {run_name or 'custom'}."
        )
        return

    logger.info(f"Loading configuration from: {config_path}")
    config_manager = ConfigManager(config_path)
    try:
        config = config_manager.get_config()
    except Exception as e:
        logger.error(f"Error parsing config YAML: {e}")
        return

    models_config = config["models"]
    if not models_config:
        logger.error("No models defined in configuration.")
        return

    # Determine prompt path from config
    tmp_dir_str = config["tmp_output_dir"]
    tmp_output_dir = Path(tmp_dir_str)
    if not tmp_output_dir.is_absolute():
        tmp_output_dir = ROOT_DIR / tmp_output_dir

    prompt_file_name = config["llm_prompt_output_file"]
    prompt_path = tmp_output_dir / "job1" / prompt_file_name

    if not prompt_path.exists():
        logger.error(f"Prompt file not found at: {prompt_path}")
        return

    logger.info(f"Loaded prompt file from: {prompt_path}")
    try:
        prompt_content = prompt_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Error reading prompt file: {e}")
        return

    stats = []
    for model_item in models_config:
        model_name = model_item["name"]
        options = model_item["options"]
        if not model_name:
            continue

        logger.info(f"Running model '{model_name}'...")
        try:
            model_stat = run_model(model_name, prompt_content, options=options)
            stats.append(model_stat)
            logger.info(
                f"Finished '{model_name}': Total Time: {model_stat['total_time']:.2f}s, "
                f"Tokens/sec: {model_stat['tokens_per_sec']:.2f}, "
                f"Response Length: {model_stat['char_count']} chars"
            )
        except Exception as e:
            logger.error(f"Error executing model '{model_name}': {e}")

    if not stats:
        logger.error("No statistics collected.")
        return

    # Process and save collected stats
    save_and_log_statistics(stats, RESULTS_DIR, run_name)



def generate_run_configs() -> list[tuple[Path, str]]:
    models = [
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

    active_count = len(models)
    runs_data = [
        {
            "run_name": f"m{active_count}_ctx16k_pred3k",
            "models": models,
            "models_data": None,
            "default_options": {
                "num_ctx": 16384,
                "num_predict": 3072,
            },
        },
        {
            "run_name": f"m{active_count}_ctx12k_temp03_pred2k",
            "models": models,
            "models_data": None,
            "default_options": {
                "num_ctx": 12288,
                "num_predict": 2560,
                "temperature": 0.3,
            },
        },
        {
            "run_name": f"m{active_count}_ctx10k_temp03_pred2k",
            "models": models,
            "models_data": None,
            "default_options": {
                "num_ctx": 10240,
                "num_predict": 2560,
                "temperature": 0.3,
            },
        },
    ]

    configs_to_run = []
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    for run in runs_data:
        run_name = run["run_name"]
        out_path = CONFIG_DIR / f"{run_name}.yaml"
        create_config(
            models=run["models"],
            models_data=run["models_data"],
            default_options=run["default_options"],
            output=out_path,
        )
        logger.info(f"Generated config {out_path} from programmatic specification.")
        configs_to_run.append((out_path, run_name))

    return configs_to_run


def main():
    # Generate configs under tmp/ and run all 3
    configs_to_run = generate_run_configs()
    assert len(configs_to_run) == len(set(configs_to_run)), f"Generated duplicate configs: {configs_to_run}"
    if not configs_to_run:
        logger.error("No run configurations could be generated.")
        sys.exit(1)

    for config_path, run_name in configs_to_run:
        logger.info(f"Executing evaluation for run configuration: {run_name}")
        run_evaluation_for_config(config_path, run_name)


if __name__ == "__main__":
    main()
