from unittest.mock import MagicMock

from tailor_cv.llm import OLLAMA_OPTIONS, call_ollama


def test_call_ollama_returns_response(mocker):
    mock_response = MagicMock()
    mock_response.message.content = "Tailored CV text"
    mocker.patch("tailor_cv.llm.ollama.chat", return_value=mock_response)

    result = call_ollama(system="sys", user_message="usr", model="test-model")

    assert result == "Tailored CV text"


def test_call_ollama_passes_system_and_user(mocker):
    mock_response = MagicMock()
    mock_response.message.content = "output"
    mock_chat = mocker.patch("tailor_cv.llm.ollama.chat", return_value=mock_response)

    call_ollama(system="sys prompt", user_message="user data", model="my-model")

    mock_chat.assert_called_once_with(
        model="my-model",
        messages=[
            {"role": "system", "content": "sys prompt"},
            {"role": "user", "content": "user data"},
        ],
        options=OLLAMA_OPTIONS,
    )


def test_ollama_options_are_factual():
    assert OLLAMA_OPTIONS["temperature"] == 0.0
    assert OLLAMA_OPTIONS["num_ctx"] == 8192
    assert OLLAMA_OPTIONS["num_predict"] == 2048
