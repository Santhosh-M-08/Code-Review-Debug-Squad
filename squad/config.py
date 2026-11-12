
"""Central configuration. Everything can be overridden with environment variables."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

KB_DIR = BASE_DIR / "knowledge_base"
CHROMA_DIR = BASE_DIR / ".chroma"

COLLECTION_NAME = "coding_guidelines"


# Local LLM Configuration (Ollama)

LLM_PROVIDER = "ollama"

LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder:3b")

DEFAULT_MODELS = {
    "qwen2.5-coder:3b": "qwen2.5-coder:3b",
    "llama3.2:3b": "llama3.2:3b",
    "gemma3:1b": "gemma3:1b",
}

AVAILABLE_MODELS = list(DEFAULT_MODELS.keys())


# Sandbox Configuration

SANDBOX_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "10"))

MAX_TEST_REPAIRS = int(os.getenv("MAX_TEST_REPAIRS", "2"))


# Retrieval Configuration

RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "3"))
