"""Tests for the LLM wrapper — Ollama calls are always mocked."""

from cvagent.llm import generate


def test_generate_returns_stripped_string(mocker):
    mock_response = {"response": "  This is the cover letter.  "}
    mocker.patch("cvagent.llm.ollama.generate", return_value=mock_response)
    result = generate("some prompt", model="mistral")
    assert result == "This is the cover letter."


def test_generate_passes_model_to_ollama(mocker):
    mock_fn = mocker.patch("cvagent.llm.ollama.generate", return_value={"response": "ok"})
    generate("prompt", model="llama3")
    mock_fn.assert_called_once_with(model="llama3", prompt="prompt")


def test_generate_uses_default_model(mocker):
    mock_fn = mocker.patch("cvagent.llm.ollama.generate", return_value={"response": "ok"})
    generate("prompt")
    call_kwargs = mock_fn.call_args
    assert call_kwargs.kwargs["model"] == "mistral"
