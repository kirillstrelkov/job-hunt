import pytest
from unittest.mock import MagicMock

from tailor_cv.llm_gemini import call_gemini


def test_call_gemini_returns_response(mocker, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text="Tailored CV text")
    mocker.patch("tailor_cv.llm_gemini.genai.Client", return_value=mock_client)

    result = call_gemini(system="sys", user_message="usr", model="gemini-2.0-flash")

    assert result == "Tailored CV text"


def test_call_gemini_passes_system_instruction(mocker, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text="output")
    mocker.patch("tailor_cv.llm_gemini.genai.Client", return_value=mock_client)

    call_gemini(system="be concise", user_message="user data", model="gemini-2.0-flash")

    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs["config"].system_instruction == "be concise"
    assert call_kwargs["contents"] == "user data"


def test_call_gemini_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        call_gemini(system="sys", user_message="usr")
