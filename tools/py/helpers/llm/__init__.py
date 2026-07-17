"""LLM Agent integration package."""

from collections.abc import Sequence
from typing import Any

from opentelemetry.trace import StatusCode
from phoenix.otel import SpanAttributes
from pydantic_ai import Agent, AgentRunResult

from config.config import DEFAULT_CONFIG
from helpers.telemetry import get_tracer

from .gemini import _get_agent as get_gemini_agent
from .ollama import _get_agent as get_ollama_agent

_TRACER = get_tracer("helpers.llm")


def get_agent(
    model_name: str,
    output_type: Any,
    system_prompt: str | Sequence[str] = (),
) -> Agent[Any, Any]:
    """Get a configured Pydantic AI agent.

    Args:
        model_name: The model name to use.
        output_type: The expected output class (e.g. BaseModel subclass or str).
        system_prompt: Static system prompts to use for this agent.

    Returns:
        A configured Agent instance.

    """
    gemini_models = DEFAULT_CONFIG.get_config_value(".gemini_models") or []
    if model_name in gemini_models:
        return get_gemini_agent(
            model_name=model_name,
            output_type=output_type,
            system_prompt=system_prompt,
        )

    return get_ollama_agent(
        model_name=model_name,
        output_type=output_type,
        system_prompt=system_prompt,
    )


def run_model(
    model_name: str,
    output_type: Any,
    user_prompt: str | Sequence[Any],
    message_history: Sequence[Any] | None = None,
    system_prompt: str | Sequence[str] = (),
    tracer_name: str | None = None,
) -> AgentRunResult[Any]:
    """Run a model synchronously using a Pydantic AI agent and return the result.

    Args:
        model_name: The model name to use.
        output_type: The expected output class (e.g. BaseModel subclass or str).
        user_prompt: User input to start/continue the conversation.
        message_history: History of the conversation so far.
        system_prompt: Static system prompts to use for this agent.
        tracer_name: Optional custom tracer name.

    Returns:
        The RunResult object returned by the agent.

    """
    agent = get_agent(
        model_name=model_name,
        output_type=output_type,
        system_prompt=system_prompt,
    )

    return run_agent(
        agent=agent,
        user_prompt=user_prompt,
        message_history=message_history,
        tracer_name=tracer_name,
    )


def run_agent(
    agent: Agent[Any, Any],
    user_prompt: str | Sequence[Any],
    message_history: Sequence[Any] | None = None,
    tracer_name: str | None = None,
) -> AgentRunResult[Any]:
    """Run a pre-configured Pydantic AI agent synchronously and return the result.

    Args:
        agent: The pre-configured Agent instance.
        user_prompt: User input to start/continue the conversation.
        message_history: History of the conversation so far.
        tracer_name: Optional custom tracer name.

    Returns:
        The RunResult object returned by the agent.

    """
    tracer = _TRACER

    if tracer_name:
        tracer = get_tracer(tracer_name)

    model_name = agent.model.model_name

    with tracer.start_as_current_span("run_agent") as span:
        span.set_attributes(
            {
                SpanAttributes.LLM_MODEL_NAME: model_name,
                SpanAttributes.INPUT_VALUE: str(user_prompt),
            }
        )

        output = agent.run_sync(
            user_prompt=user_prompt,
            message_history=message_history,
        )

        span.set_attribute(SpanAttributes.OUTPUT_VALUE, str(output.output))
        span.set_status(StatusCode.OK)

    return output
