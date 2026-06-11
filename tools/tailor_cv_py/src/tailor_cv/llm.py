import ollama
from loguru import logger

DEFAULT_MODEL = "gemma4:e2b"

OLLAMA_OPTIONS = {
    "temperature": 0.0,  # Strictly factual — no creative drift
    "top_k": 10,
    "top_p": 0.5,
    "num_predict": 2048,  # Enough tokens for a 2-page resume
    "num_ctx": 8192,  # Expands context to read a full 10-page master CV
}


def call_ollama(system: str, user_message: str, model: str = DEFAULT_MODEL) -> str:
    logger.debug(f"System:\n{system}")
    logger.debug(f"User message:\n{user_message}")
    logger.info(f"Calling Ollama model '{model}'")
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        options=OLLAMA_OPTIONS,
    )
    tailored_cv = response.message.content
    logger.debug(f"Response:\n{tailored_cv}")
    return tailored_cv
