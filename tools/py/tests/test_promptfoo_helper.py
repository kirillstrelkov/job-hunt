from helpers.promptfoo_helper import get_provider_id


def test_get_provider_id_gemini():
    # Verify Gemini provider ID format
    provider = get_provider_id("gemini-3.5-flash")
    assert provider == "google:gemini-3.5-flash"


def test_get_provider_id_ollama():
    # Verify Ollama provider ID format
    provider = get_provider_id("gemma4:e4b-it-qat")
    assert provider == "ollama:chat:gemma4:e4b-it-qat"
