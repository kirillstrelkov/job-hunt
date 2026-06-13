import re
import sys
from pathlib import Path

from loguru import logger
from trulens.apps.virtual import TruVirtual, VirtualApp, VirtualRecord
from trulens.core import Feedback, TruSession

sys.path.append(str(Path(__file__).resolve().parents[3]))
sys.path.append(str(Path(__file__).resolve().parents[4]))
from helpers.config import LLM_PROMPT_OUTPUT_FILE, TMP_OUTPUT_DIR, TRULENS_DB_URL
from helpers.ollama_helper import get_eval_model, get_models

# Set TruLens database path to be inside the tmp directory
Path(TRULENS_DB_URL.replace("sqlite:///", "")).parent.mkdir(parents=True, exist_ok=True)
TruSession(database_url=TRULENS_DB_URL)


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

    def correctness_score(input_text: str, output_text: str) -> float:
        prompt = (
            f"Ground Truth:\n{expected}\n\n"
            f"Generated Output:\n{output_text}\n\n"
            f"Instruction: Score the factual correctness and structural alignment of the Generated Output "
            f"against the Ground Truth from 0.0 (worst) to 1.0 (best). Output ONLY the numeric float value."
        )
        try:
            from helpers.ollama_helper import generate_response

            text = generate_response(eval_model, prompt).strip()
            m = re.search(r"[-+]?\d*\.\d+|\d+", text)
            if m:
                return float(m.group())
            return 0.0
        except Exception:
            return 0.0

    # Define TruLens Feedback
    feedback = Feedback(correctness_score, name="Correctness").on_input_output()

    # Define Virtual App and Recorder
    virtual_app = VirtualApp()
    tru_recorder = TruVirtual(app_id=f"cv-tailoring-{variant}", app=virtual_app, feedbacks=[feedback])

    logger.info(f"--- TruLens Evaluation (Variant: {variant}) ---")

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
        out_file = Path(f"{TMP_OUTPUT_DIR}/{subfolder}/trulens/{model.replace(':', '_')}_{variant}_cv.md")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(actual, encoding="utf-8")

        # Log to TruLens DB using VirtualRecord
        try:
            record = VirtualRecord(main_input=prompt_content, main_output=actual)
            tru_recorder.add_record(record)
        except Exception as e:
            logger.error(f"Could not log record to TruLens database: {e}")

        # Run custom feedback to show in console
        score = correctness_score(prompt_content, actual)
        logger.info(f"Model: {model}")
        logger.info(f"  Score: {score} / 1.0")


if __name__ == "__main__":
    run_eval()
