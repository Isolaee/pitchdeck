"""LLM backend abstraction — supports Ollama (local) and OpenAI (API)."""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Backend identifiers
# ---------------------------------------------------------------------------
BACKEND_OLLAMA = "ollama"
BACKEND_OPENAI = "openai"

DEFAULT_BACKEND = BACKEND_OLLAMA
DEFAULT_OLLAMA_MODEL = "mistral"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def generate(prompt: str, backend: str = DEFAULT_BACKEND, model: str | None = None) -> str:
    """Send a prompt to the configured LLM backend and return the response text.

    Args:
        prompt:  The full prompt string to send.
        backend: "ollama" (default, local) or "openai".
        model:   Override the default model for the chosen backend.

    Raises:
        ValueError: If an unknown backend is specified or the OpenAI API key is missing.
        ollama.ResponseError: If the Ollama daemon is not running or model unavailable.
        openai.OpenAIError: If the OpenAI API call fails.
    """
    if backend == BACKEND_OLLAMA:
        return _generate_ollama(prompt, model or DEFAULT_OLLAMA_MODEL)
    elif backend == BACKEND_OPENAI:
        return _generate_openai(prompt, model or DEFAULT_OPENAI_MODEL)
    else:
        raise ValueError(f"Unknown backend '{backend}'. Choose '{BACKEND_OLLAMA}' or '{BACKEND_OPENAI}'.")


# ---------------------------------------------------------------------------
# Ollama (local)
# ---------------------------------------------------------------------------

def _generate_ollama(prompt: str, model: str) -> str:
    """Call the local Ollama daemon (localhost:11434)."""
    import ollama  # only required when using this backend

    response = ollama.generate(model=model, prompt=prompt)
    return response["response"].strip()


# ---------------------------------------------------------------------------
# OpenAI (future / production)
# ---------------------------------------------------------------------------

def _generate_openai(prompt: str, model: str) -> str:
    """Call the OpenAI Chat Completions API.

    Requires OPENAI_API_KEY to be set in the environment (or .env file).
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Add it to your .env file or environment variables."
        )

    import openai  # only required when using this backend

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
