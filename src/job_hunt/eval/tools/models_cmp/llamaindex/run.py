from pathlib import Path

from job_hunt.core.config import DEFAULT_CONFIG
from llama_index.core.evaluation import CorrectnessEvaluator
from llama_index.llms.ollama import Ollama
from loguru import logger

from job_hunt.core.ollama_helper import get_eval_model, get_model_names
from job_hunt.core.tmp_helper import get_tmp_output_dir


def run_eval() -> None:
    eval_model = get_eval_model()
    models = get_model_names()
    subfolder = "job1"
    variant = "jd"
    gt_file = Path(f"inputs/{subfolder}/gt.md")
    job = DEFAULT_CONFIG.get_jobs()[0]
    prompt_file = job.llm_prompt_path

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
        logger.info(f"Generating Resume with {model}...")
        try:
            from job_hunt.core.ollama_helper import get_model_output

            output_name = f"{model.replace(':', '_')}_{variant}_resume.md"
            model_output_file = Path(get_tmp_output_dir()) / subfolder / "model_output" / output_name
            actual = get_model_output(model, prompt_content, model_output_file)
        except Exception as e:
            logger.error(f"Ollama generation failed for {model}: {e}")
            continue

        # Save output
        out_file = Path(get_tmp_output_dir()) / subfolder / "llamaindex" / output_name
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
