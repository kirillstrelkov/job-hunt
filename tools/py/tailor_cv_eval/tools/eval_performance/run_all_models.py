"""Run evaluation configurations across multiple Ollama models."""

import sys
from pathlib import Path

import pandas as pd
from loguru import logger
from tqdm import tqdm

from config.config import (
    DEFAULT_CONFIG,
    ConfigManager,
)
from helpers.config_generator import create_config
from helpers.df_helper import ModelStatsCols
from helpers.notebook import run_jupyter_notebook
from helpers.ollama_helper import _get_ollama_models, run_model
from helpers.tmp_helper import get_llm_prompt_for_job, get_tmp_input_folder, get_tmp_output_folder

RESULTS_DIR = get_tmp_output_folder(__file__)
CONFIG_DIR = get_tmp_input_folder(__file__)


def save_and_log_statistics(stats: list[dict], output: Path) -> None:
    """Create a DataFrame from statistics, save it as CSV, and print a Markdown table to logs."""
    if output.exists():
        logger.warning(f"Output file {output} already exists. Skipping saving statistics.")
        return

    df = pd.DataFrame(stats)

    # Reorder columns for presentation
    columns_order = ModelStatsCols.COLUMNS_ORDER

    # Ensure all columns exist
    for col in columns_order:
        if col not in df.columns:
            df[col] = None

    df = df[columns_order]

    # Rename columns for presentation
    df.columns = ModelStatsCols.DISPLAY_COLUMNS

    # Make sure parent directory exists
    output.parent.mkdir(parents=True, exist_ok=True)

    # Save DataFrame as CSV
    df.to_csv(output, index=False)
    logger.info(f"Saved statistics data table to CSV: {output}")

    # Generate Markdown representation for logging
    markdown_table = df.to_markdown(index=False)

    # Log data table to stdout
    logger.info(f"\nModel Evaluation Statistics ({output.stem}):\n\n{markdown_table}\n")


def run_evaluation_for_config(config_path: Path, run_name: str | None = None) -> None:
    """Run Ollama models evaluation for a specific configuration path."""
    # Output file base name
    suffix = f"_{run_name}" if run_name else ""
    csv_name = f"model_comparison{suffix}.csv"
    output = RESULTS_DIR / csv_name

    if output.exists():
        logger.warning(f"Output file already exists at {output}. Skipping evaluation for run: {run_name or 'custom'}.")
        return

    logger.debug(f"Loading configuration from: {config_path}")
    config_manager = ConfigManager(config_path)
    try:
        config = config_manager.get_config()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error parsing config YAML: {e}")
        return

    models_config = config["models"]
    if not models_config:
        logger.error("No models defined in configuration.")
        return

    # Determine prompt path from config
    prompt_path = get_llm_prompt_for_job(DEFAULT_CONFIG.get_jobs()[0])
    if not prompt_path.exists():
        logger.error(f"Prompt file not found at: {prompt_path}")
        return

    logger.debug(f"Loaded prompt file from: {prompt_path}")
    try:
        prompt_content = prompt_path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error reading prompt file: {e}")
        return

    stats = []
    for model_item in models_config:
        model_name = model_item["name"]
        options = model_item["options"]
        if not model_name:
            continue

        logger.debug(f"Running model '{model_name}'...")
        try:
            model_stat = run_model(model_name, prompt_content, options=options)
            stats.append(model_stat)
            logger.debug(
                f"Finished '{model_name}': Total Time: {model_stat['total_time']:.2f}s, "
                f"Tokens/sec: {model_stat['tokens_per_sec']:.2f}, "
                f"Response Length: {model_stat['char_count']} chars"
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error executing model '{model_name}': {e}")

    if not stats:
        logger.error("No statistics collected.")
        return

    # Process and save collected stats
    save_and_log_statistics(stats, output)


def generate_run_configs() -> list[tuple[Path, str]]:
    """Generate YAML configuration files programmatically for different evaluation parameters."""
    models = _get_ollama_models()
    active_count = len(models)
    logger.info(f"Number of models to be used: {active_count} ({', '.join(models)})")

    temperatures = [0.1]
    num_ctx_values = [16384 * 2]
    num_predict_values = [-1]

    runs_data = []
    for temp in temperatures:
        for num_ctx in num_ctx_values:
            for num_predict in num_predict_values:
                temp_str = f"{temp:.1f}".replace(".", "")
                ctx_str = f"{num_ctx // 1024}k"
                pred_str = f"neg{abs(num_predict)}" if num_predict < 0 else f"{num_predict // 1024}k"

                run_name = f"m{active_count}_ctx{ctx_str}_temp{temp_str}_pred{pred_str}"
                runs_data.append(
                    {
                        "run_name": run_name,
                        "models": models,
                        "models_data": None,
                        "default_options": {
                            "num_ctx": num_ctx,
                            "num_predict": num_predict,
                            "temperature": temp,
                        },
                    }
                )

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


def main() -> None:
    """Generate configuration variations and run evaluations on all models."""
    configs_to_run = generate_run_configs()
    if len(configs_to_run) != len(set(configs_to_run)):
        msg = f"Generated duplicate configs: {configs_to_run}"
        raise ValueError(msg)
    if not configs_to_run:
        logger.error("No run configurations could be generated.")
        sys.exit(1)

    for config_path, run_name in tqdm(configs_to_run, desc="Evaluating configurations"):
        run_evaluation_for_config(config_path, run_name)

    run_jupyter_notebook(Path(__file__).parent / "result_analysis.ipynb")


if __name__ == "__main__":
    main()
