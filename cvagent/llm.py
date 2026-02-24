"""Thin wrapper around the Ollama Python SDK."""

from __future__ import annotations

import ollama

DEFAULT_MODEL = "mistral"


def generate(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Send a prompt to Ollama and return the response text.

    Communicates with the local Ollama daemon (localhost:11434 by default).
    Uses blocking (non-streaming) mode — sufficient for short cover letters.

    Raises ollama.ResponseError if the model is unavailable or the daemon
    is not running.
    """
    response = ollama.generate(model=model, prompt=prompt)
    return response["response"].strip()
