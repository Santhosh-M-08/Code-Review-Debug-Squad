"""Intent detection helpers.

The LLM router (see prompts.INTENT_PROMPT) is the primary classifier. These helpers
validate its answer and provide a deterministic keyword fallback.
"""
from typing import Optional

INTENTS = ("full_review", "debug", "style", "explain", "test")

_KEYWORDS = {
    "test": ["unit test", "write test", "test case", "tests for", "testing", "write tests"],
    "explain": ["explain", "what does", "how does", "walk me through", "understand", "describe"],
    "style": ["style", "lint", "pep8", "pep 8", "naming", "readab", "format", "clean up", "convention"],
    "debug": ["bug", "debug", "error", "fix", "wrong", "crash", "fails", "not working", "exception", "broken"],
}


def parse_intent_label(text: str) -> Optional[str]:
    """Map a free-text model reply to one of INTENTS, or None if it is not recognisable."""
    t = text.strip().lower().replace("-", "_").replace(" ", "_")
    for label in INTENTS:
        if label in t:
            return label
    return None


def heuristic_intent(request: str) -> str:
    """Keyword-based fallback: one matching intent wins; none or several means a full review."""
    r = (request or "").lower()
    matched = [intent for intent, words in _KEYWORDS.items() if any(w in r for w in words)]
    if len(matched) == 1:
        return matched[0]
    return "full_review"
