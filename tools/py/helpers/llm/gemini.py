"""Gemini agent helper using Pydantic AI."""

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel

from config.config import DEFAULT_CONFIG
from helpers.constants import SYS_PROMPT_WITH_TAILORED_CV
from helpers.llm_helper import dict_to_model_settings, get_model_options

load_dotenv(DEFAULT_CONFIG.get_env_file())


def get_agent(
    model_name: str,
    output_type: BaseModel,
    instructions: str = SYS_PROMPT_WITH_TAILORED_CV,
) -> Agent:
    """Return a configured Gemini Pydantic AI agent."""
    options = get_model_options(model_name)
    settings = dict_to_model_settings(options)
    model = GeminiModel(model_name)

    return Agent(
        model,
        output_type=output_type,
        instructions=instructions,
        model_settings=settings,
    )
