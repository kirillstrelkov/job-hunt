import sys
from pathlib import Path

from llama_index.core.evaluation import CorrectnessEvaluator
from llama_index.llms.ollama import Ollama
from loguru import logger

sys.path.append(str(Path(__file__).resolve().parents[3]))
sys.path.append(str(Path(__file__).resolve().parents[4]))
from helpers.config import LLM_PROMPT_OUTPUT_FILE, TMP_OUTPUT_DIR
from helpers.ollama_helper import get_eval_model, get_model_names


def run_eval():
    eval_model = get_eval_model()
    models = get_model_names()
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

    # Initialize evaluator
    evaluator_llm = Ollama(model=eval_model, request_timeout=120.0)
    evaluator = CorrectnessEvaluator(llm=evaluator_llm)

    logger.info(f"--- LlamaIndex Correctness Evaluation (Variant: {variant}) ---")

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
        out_file = Path(f"{TMP_OUTPUT_DIR}/{subfolder}/llamaindex/{model.replace(':', '_')}_{variant}_cv.md")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(actual, encoding="utf-8")

        # Evaluate correctness
        try:
            result = evaluator.evaluate(query=prompt_content, response=actual, reference=expected)
            logger.info(f"Model: {model}")
            logger.info(f"  Score: {result.score} / 5.0")
            logger.info(f"  Passing: {result.score >= 3.5}")
            logger.info(f"  Reasoning: {result.feedback}")
        except Exception as e:
            logger.error(f"Evaluation failed for {model}: {e}")


if __name__ == "__main__":
    run_eval()
