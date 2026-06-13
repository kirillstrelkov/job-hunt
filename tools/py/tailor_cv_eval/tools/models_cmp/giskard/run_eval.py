import sys
from pathlib import Path

import giskard
import pandas as pd
from giskard import Dataset, test
from loguru import logger

sys.path.append(str(Path(__file__).resolve().parents[3]))
sys.path.append(str(Path(__file__).resolve().parents[4]))
from helpers.config import LLM_PROMPT_OUTPUT_FILE, TMP_OUTPUT_DIR
from helpers.ollama_helper import get_eval_model, get_models


def run_eval():
    eval_model = get_eval_model()
    models = get_models()
    subfolder = "job1"
    variant = "jd"
    gt_file = Path(f"inputs/{subfolder}/gt.md")
    prompt_file = Path(TMP_OUTPUT_DIR) / subfolder / LLM_PROMPT_OUTPUT_FILE

    if not gt_file.exists():
        logger.error(f"Ground truth file {gt_file} is missing.")
        return
    if not prompt_file.exists():
        logger.error(f"Prompt file {prompt_file} is missing. Please run prompt generation first.")
        return

    expected = gt_file.read_text(encoding="utf-8")
    prompt_content = prompt_file.read_text(encoding="utf-8")

    logger.info(f"--- Giskard Evaluation (Variant: {variant}) ---")

    for model in models:
        logger.info(f"Generating CV with {model}...")
        try:
            from helpers.ollama_helper import get_model_output

            model_output_file = (
                Path(TMP_OUTPUT_DIR) / subfolder / "model_output" / f"{model.replace(':', '_')}_{variant}_cv.md"
            )
            actual = get_model_output(model, prompt_content, model_output_file)
        except Exception as e:
            logger.error(f"Ollama generation failed for {model}: {e}")
            continue

        # Save output
        out_file = Path(f"{TMP_OUTPUT_DIR}/{subfolder}/giskard/{model.replace(':', '_')}_{variant}_cv.md")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(actual, encoding="utf-8")

        # Create a Giskard dataset for this run
        df = pd.DataFrame(
            [
                {
                    "prompt": prompt_content,
                    "actual": actual,
                    "expected": expected,
                }
            ]
        )

        dataset = Dataset(df=df, name=f"CV Tailoring {model} Dataset", target=None)
        logger.info(f"  Created Giskard Dataset: {dataset.name}")

        # Custom Giskard test for factual correctness
        @test(name="Factual Correctness Test", tags=["llm"])
        def test_factual_correctness(actual=actual, expected=expected):
            prompt = (
                f"Ground Truth:\n{expected}\n\n"
                f"Generated Output:\n{actual}\n\n"
                f"Instruction: Is the Generated Output factually correct and consistent with the Ground Truth? "
                f"Respond with 'YES' or 'NO'."
            )
            try:
                from helpers.ollama_helper import generate_response

                eval_text = generate_response(eval_model, prompt).strip().upper()
                passed = "YES" in eval_text
                return giskard.TestResult(passed=passed, metric=1.0 if passed else 0.0)
            except Exception as e:
                return giskard.TestResult(passed=False, messages=[str(e)])

        # Run test
        try:
            test_res = test_factual_correctness().execute()
            logger.info(f"Model: {model}")
            logger.info(f"  Factual Correctness Pass: {test_res.passed}")
            logger.info(f"  Metric Score: {test_res.metric}")
        except Exception as e:
            logger.error(f"Giskard test failed to execute for {model}: {e}")


if __name__ == "__main__":
    run_eval()
