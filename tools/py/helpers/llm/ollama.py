"""Ollama agent integration helper."""

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.profiles import ModelProfile
from pydantic_ai.providers.ollama import OllamaProvider

from helpers.constants import SYS_PROMPT_WITH_TAILORED_CV
from helpers.llm_helper import dict_to_model_settings, get_model_options


def get_agent(
    model_name: str,
    output_type: BaseModel,
    instructions: str = SYS_PROMPT_WITH_TAILORED_CV,
) -> Agent:
    """Return a configured Ollama Pydantic AI agent."""
    options = get_model_options(model_name)
    settings = dict_to_model_settings(options)

    extra_body = {"think": False, "keep_alive": int(options.get("keep_alive", 0))}

    ollama_options = {}
    if "num_ctx" in options:
        ollama_options["num_ctx"] = int(options["num_ctx"])
    if "repeat_penalty" in options:
        ollama_options["repeat_penalty"] = float(options["repeat_penalty"])

    if ollama_options:
        extra_body["options"] = ollama_options

    settings["extra_body"] = extra_body

    settings["thinking"] = False

    model = OllamaModel(
        model_name,
        provider=OllamaProvider(base_url="http://localhost:11434/v1"),
        profile=ModelProfile(
            supports_tools=False,
            supports_json_schema_output=False,
            supports_json_object_output=True,
            default_structured_output_mode="prompted",
        ),
    )

    return Agent(
        model,
        output_type=output_type,
        instructions=instructions,
        model_settings=settings,
    )
