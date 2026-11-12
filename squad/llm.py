
"""LLM factory: connects all agents to local Ollama models."""

from typing import Optional

from . import config


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2
):
    """Return a local Ollama chat model."""

    provider = (provider or config.LLM_PROVIDER).lower()

    if provider != "ollama":
        raise ValueError(
            "Only the local Ollama provider is supported."
        )

    model = model or config.LLM_MODEL

    if model not in config.AVAILABLE_MODELS:
        raise ValueError(
            f"Model '{model}' is not supported. "
            f"Choose from {config.AVAILABLE_MODELS}."
        )

    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model,
        temperature=temperature,
    )
