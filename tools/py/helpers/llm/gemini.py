"""Gemini agent helper using Pydantic AI."""

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel, GoogleModelSettings
from helpers.models import TailoredCVBody
from helpers.constants import SYS_PROMPT_WITH_TAILORED_CV


def get_agent(model_name: str) -> Agent:
    """Return a configured Gemini Pydantic AI agent targeting TailoredCVBody."""
    settings = GoogleModelSettings(thinking_budget=0)
    model = GeminiModel(model_name)

    return Agent(
        model,
        output_type=TailoredCVBody,
        instructions=SYS_PROMPT_WITH_TAILORED_CV,
        model_settings=settings,
    )
