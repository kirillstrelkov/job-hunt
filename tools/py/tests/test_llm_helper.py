from unittest.mock import MagicMock, patch

import pytest

from helpers.llm_helper import (
    __get_supported_models,
    dict_to_model_settings,
    generate_response,
    run_model,
)


def test_get_supported_models():
    models = __get_supported_models()
    assert isinstance(models, list)
    assert "gemini-2.0-flash" in models


def test_dict_to_model_settings():
    options = {
        "temperature": 0.5,
        "num_predict": 100,
        "seed": 42,
    }
    settings = dict_to_model_settings(options)
    assert settings.temperature == 0.5
    assert settings.max_tokens == 100
    assert settings.seed == 42


@patch("helpers.llm_helper.GeminiModel")
@patch("helpers.llm_helper.Agent")
def test_generate_response(mock_agent_class, mock_gemini_model_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    mock_agent = MagicMock()
    mock_run_result = MagicMock()
    mock_run_result.data = "Test response text"
    mock_agent.run_sync.return_value = mock_run_result
    mock_agent_class.return_value = mock_agent

    response = generate_response("gemini-2.0-flash", "What is the meaning of life?")

    assert response == "Test response text"
    mock_gemini_model_class.assert_called_once_with("gemini-2.0-flash", api_key="fake-key")
    mock_agent.run_sync.assert_called_once()


@patch("helpers.llm_helper.GeminiModel")
@patch("helpers.llm_helper.Agent")
def test_run_model(mock_agent_class, mock_gemini_model_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    mock_agent = MagicMock()
    mock_run_result = MagicMock()
    mock_run_result.data = "Detailed test response"

    # Mocking usage
    mock_usage = MagicMock()
    mock_usage.request_tokens = 15
    mock_usage.response_tokens = 25
    mock_run_result.usage.return_value = mock_usage

    mock_agent.run_sync.return_value = mock_run_result
    mock_agent_class.return_value = mock_agent

    res_dict = run_model("gemini-2.0-flash", "Hello")

    assert res_dict["model"] == "gemini-2.0-flash"
    assert res_dict["response"] == "Detailed test response"
    assert res_dict["prompt_tokens"] == 15
    assert res_dict["gen_tokens"] == 25
    assert res_dict["total_time"] >= 0.0
    assert res_dict["char_count"] == len("Detailed test response")
    assert res_dict["word_count"] == 3


def test_generate_response_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        generate_response("gemini-2.0-flash", "Hello")
