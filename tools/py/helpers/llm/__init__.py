from helpers.config import DEFAULT_CONFIG
from helpers.constants import SYS_PROMPT_WITH_TAILORED_CV
from .gemini import get_agent as get_gemini_agent
from .ollama import get_agent as get_ollama_agent
from pydantic_ai import Agent


def get_agent(
    model_name: str,
    output_type: any,
    instructions: str = SYS_PROMPT_WITH_TAILORED_CV,
) -> Agent:
    """Return the correct Pydantic AI agent dynamically depending on whether model_name is a Gemini or Ollama model."""
    gemini_models = DEFAULT_CONFIG.get_config_value(".gemini_models") or []
    if model_name in gemini_models:
        return get_gemini_agent(model_name, output_type, instructions)

    return get_ollama_agent(model_name, output_type, instructions)
