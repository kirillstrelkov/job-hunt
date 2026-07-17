from collections.abc import Sequence

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel

from config.config import DEFAULT_CONFIG
from helpers.llm_helper import dict_to_model_settings, get_model_options

load_dotenv(DEFAULT_CONFIG.get_env_file())


def _get_agent(
    model_name: str,
    output_type: BaseModel,
    system_prompt: str | Sequence[str] = (),
) -> Agent:
    """Return a configured Gemini Pydantic AI agent."""
    options = get_model_options(model_name)
    settings = dict_to_model_settings(options)
    model = GoogleModel(model_name)

    agent = Agent(
        model,
        output_type=output_type,
        system_prompt=system_prompt,
        model_settings=settings,
    )
    return agent
