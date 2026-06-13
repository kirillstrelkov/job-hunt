import sys
from pathlib import Path

from datasets import Dataset
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama as LangchainOllama
from loguru import logger
from ragas import evaluate
from ragas.metrics import answer_relevancy, faithfulness

sys.path.append(str(Path(__file__).resolve().parents[3]))
sys.path.append(str(Path(__file__).resolve().parents[4]))
from config import LLM_PROMPT_OUTPUT_FILE, TMP_OUTPUT_DIR
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

    # Set up Ollama LLM and Embeddings for Ragas
    evaluator_llm = LangchainOllama(model=eval_model)
    evaluator_embeddings = OllamaEmbeddings(model=eval_model)

    logger.info(f"--- Ragas Evaluation (Variant: {variant}) ---")

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
        out_file = Path(f"{TMP_OUTPUT_DIR}/{subfolder}/ragas/{model.replace(':', '_')}_{variant}_cv.md")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(actual, encoding="utf-8")

        # Ragas requires a dataset format
        data = {
            "question": [prompt_content],
            "answer": [actual],
            "contexts": [[expected]],
            "ground_truth": [expected],
        }
        dataset = Dataset.from_dict(data)

        # Run evaluation
        try:
            result = evaluate(
                dataset=dataset,
                metrics=[faithfulness, answer_relevancy],
                llm=evaluator_llm,
                embeddings=evaluator_embeddings,
            )
            logger.info(f"Model: {model}")
            logger.info(f"  Faithfulness (Factuality): {result.get('faithfulness', 0.0)}")
            logger.info(f"  Answer Relevance: {result.get('answer_relevancy', 0.0)}")
        except Exception as e:
            logger.error(f"Ragas evaluation failed for {model}: {e}")


if __name__ == "__main__":
    run_eval()
