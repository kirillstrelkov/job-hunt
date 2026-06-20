"""Gemini agent helper using Pydantic AI."""

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel, GoogleModelSettings
from helpers.models import TailoredCVBody


def get_agent(model_name: str) -> Agent:
    """Return a configured Gemini Pydantic AI agent targeting TailoredCVBody."""
    settings = GoogleModelSettings(thinking_budget=0)
    model = GeminiModel(model_name)

    return Agent(
        model,
        output_type=TailoredCVBody,
        instructions="""
        You are a professional technical reverse recruiter.
        Analyze the candidate's CV against the Job Description (JD).
        Produce a tailored CV matching the TailoredCVBody schema.
        Ensure every field is populated strictly based on the provided documents.
        """,
        model_settings=settings,
    )
