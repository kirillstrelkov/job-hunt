import os

from google import genai
from google.genai import types
from loguru import logger

DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"

GEMINI_OPTIONS = types.GenerateContentConfig(
    temperature=0.0,
    max_output_tokens=2048,
)


def call_gemini(system: str, user_message: str, model: str = DEFAULT_GEMINI_MODEL) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    logger.debug(f"System:\n{system}")
    logger.debug(f"User message:\n{user_message}")
    logger.info(f"Calling Gemini model '{model}'")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=GEMINI_OPTIONS.temperature,
            max_output_tokens=GEMINI_OPTIONS.max_output_tokens,
        ),
        contents=user_message,
    )

    result = response.text
    logger.debug(f"Response:\n{result}")
    return result
