from unittest.mock import MagicMock, patch

import pytest

from helpers.llm_helper import (
    dict_to_model_settings,
    generate_response,
    get_model_names,
    run_model,
)


def test_get_model_names():
    models = get_model_names()
    assert isinstance(models, list)
    assert "gemini-3.5-flash" in models


def test_dict_to_model_settings():
    options = {
        "temperature": 0.5,
        "num_predict": 100,
        "seed": 42,
    }
    settings = dict_to_model_settings(options)
    assert settings["temperature"] == 0.5
    assert settings["max_tokens"] == 100
    assert settings["seed"] == 42


@patch("helpers.llm_helper.GoogleModel")
@patch("helpers.llm_helper.Agent")
def test_generate_response(mock_agent_class, mock_gemini_model_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    mock_agent = MagicMock()
    mock_run_result = MagicMock()
    mock_run_result.output = "Test response text"
    mock_agent.run_sync.return_value = mock_run_result
    mock_agent_class.return_value = mock_agent

    response = generate_response("gemini-2.0-flash", "What is the meaning of life?")

    assert response == "Test response text"
    mock_gemini_model_class.assert_called_once_with("gemini-2.0-flash")
    mock_agent.run_sync.assert_called_once()


@patch("helpers.llm_helper.GoogleModel")
@patch("helpers.llm_helper.Agent")
def test_run_model(mock_agent_class, mock_gemini_model_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    mock_agent = MagicMock()
    mock_run_result = MagicMock()
    mock_run_result.output = "Detailed test response"

    # Mocking usage
    mock_usage = MagicMock()
    mock_usage.input_tokens = 15
    mock_usage.output_tokens = 25
    mock_run_result.usage = mock_usage

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
    mock_gemini_model_class.assert_called_once_with("gemini-2.0-flash")


def test_generate_response_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        generate_response("gemini-2.0-flash", "Hello")
