import os
from pathlib import Path

import pytest

# Set a dummy key to prevent DeepEval from complaining about missing OpenAI credentials
os.environ.setdefault("OPENAI_API_KEY", "dummy-key")


from conftest import EVALUATION_RESULTS
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase, SingleTurnParams
from loguru import logger

from config.config import DEFAULT_CONFIG
from helpers.ollama_helper import get_eval_model, get_model_names
from helpers.tmp_helper import get_tmp_output_dir


def run_assessment(prompt_content: str, actual_output: str, expected_output: str) -> tuple[float, str, bool]:
    """Evaluates the actual output against the expected ground truth using DeepEval."""
    # Use the configured evaluation model
    try:
        evaluator_model = OllamaModel(model=get_eval_model())
    except Exception as e:
        evaluator_model = None
        logger.error(f"Could not load custom evaluator model: {e}")

    metric = GEval(
        name="Correctness",
        criteria=("Determine whether the actual output is factually correct based on the expected output."),
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT,
        ],
        threshold=0.5,
        model=evaluator_model,
    )

    test_case = LLMTestCase(
        input=prompt_content,
        actual_output=actual_output,
        expected_output=expected_output,
    )

    score = 0.0
    reason = "Evaluation executed"
    passed = False

    try:
        assert_test(test_case, [metric])
        score = metric.score if metric.score is not None else 0.0
        reason = metric.reason
        passed = True
    except AssertionError as e:
        # DeepEval assert_test raises AssertionError if score is below threshold
        score = metric.score if metric.score is not None else 0.0
        reason = metric.reason or str(e)
    except Exception as e:
        # Catch JSON decoding / formatting issues of local evaluator model
        reason = f"Metric execution error: {e}"
        score = 0.0

    return score, reason, passed


@pytest.mark.parametrize("model_name", get_model_names(check=False))
def test_evaluate_llm_tailoring(model_name: str, variant: str):
    """Evaluates LLM tailored CV outputs against a reference ground truth

    across different Ollama models and prepare_llm_prompt options.
    """
    subfolder = "job1"
    gt_filepath = Path(f"inputs/{subfolder}/gt.md")
    assert gt_filepath.exists(), f"{gt_filepath} file is missing!"

    # Define temporary files and final outputs
    job = DEFAULT_CONFIG.get_jobs()[0]
    prompt_temp_file = job.llm_prompt_path
    output_dir = Path(get_tmp_output_dir()) / subfolder / "deepeval"
    output_dir.mkdir(parents=True, exist_ok=True)
    cv_output_file = output_dir / f"{model_name.replace(':', '_')}_{variant}_cv.md"

    # 1. Read the pre-generated prompt file
    assert prompt_temp_file.exists(), (
        f"Prompt file {prompt_temp_file} was not pre-generated. Run 'just generate-prompt-for-jd' first."
    )

    prompt_content = prompt_temp_file.read_text(encoding="utf-8")

    # 2. Get LLM response using Ollama helper
    try:
        from helpers.ollama_helper import get_model_output

        model_output_file = (
            Path(get_tmp_output_dir()) / subfolder / "model_output" / f"{model_name.replace(':', '_')}_{variant}_cv.md"
        )
        actual_output = get_model_output(model_name, prompt_content, model_output_file)
    except Exception as e:
        pytest.fail(f"Ollama failed to generate response for {model_name}: {e}")

    # Save the output to outputs/ directory
    cv_output_file.write_text(actual_output, encoding="utf-8")

    # 3. Read Ground Truth reference
    expected_output = gt_filepath.read_text(encoding="utf-8")

    # 4. Use DeepEval framework to compare actual response against ground truth
    score, reason, passed = run_assessment(
        prompt_content=prompt_content,
        actual_output=actual_output,
        expected_output=expected_output,
    )

    # Register the run results
    EVALUATION_RESULTS.append(
        {
            "Model": model_name,
            "Variant": variant,
            "Score": round(score, 2),
            "Passed": passed,
            "Reason": reason,
            "Output Path": str(cv_output_file),
        }
    )

    # If the check failed, make the test fail
    if not passed:
        pytest.fail(f"Model: {model_name}, Variant: {variant} failed to meet threshold. Reason: {reason}")
