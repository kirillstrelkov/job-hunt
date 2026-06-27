"""Ollama agent helper using Pydantic AI."""

from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from helpers.models import TailoredCVBody
from helpers.constants import SYS_PROMPT_WITH_TAILORED_CV


def get_agent(model_name: str) -> Agent:
    """Return a configured Ollama Pydantic AI agent targeting TailoredCVBody."""
    model = OllamaModel(model_name)

    return Agent(
        model,
        output_type=TailoredCVBody,
        instructions=SYS_PROMPT_WITH_TAILORED_CV,
    )
