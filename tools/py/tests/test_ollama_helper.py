from helpers.ollama_helper import get_model_options


def test_get_model_options_no_defaults():
    model = "gemma-4-26b-a4b-it"
    options = get_model_options(model)
    assert "num_ctx" not in options


def test_get_model_options_with_defaults():
    model = "gemini-3.1-flash-lite"
    options = get_model_options(model)
    assert "num_ctx" in options
    assert "temperature" in options
