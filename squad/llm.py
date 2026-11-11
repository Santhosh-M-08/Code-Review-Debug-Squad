
"""LLM factory: one place that decides which model the agents talk to."""

import os
from typing import Optional

from . import config


_KEY_VARS = {
    "google": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2
):
    """Return a LangChain chat model for the chosen provider.

    Providers:
        google    - Google Gemini
        anthropic - Anthropic Claude
        openai    - OpenAI
        ollama    - Local Ollama model
    """

    provider = (provider or config.LLM_PROVIDER).lower()

    if provider not in config.DEFAULT_MODELS:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Choose from {list(config.DEFAULT_MODELS)}."
        )

    model = model or config.LLM_MODEL or config.DEFAULT_MODELS[provider]

    # Check API key for cloud providers
    key_var = _KEY_VARS.get(provider)

    if provider == "google":
        api_key = (
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )
    else:
        api_key = os.getenv(key_var) if key_var else None

    if key_var and not api_key:
        raise RuntimeError(
            f"{key_var} is not set. "
            "Add it in the sidebar or export it before starting the app."
        )

    # Google Gemini
    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = (
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )

        if not api_key:
            raise RuntimeError("Google API key is missing.")

        return ChatGoogleGenerativeAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
            timeout=30,
            max_retries=0,
        )

    # Anthropic Claude
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=4096
        )

    # OpenAI
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            temperature=temperature
        )

    # Ollama
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model,
            temperature=temperature,
        )
