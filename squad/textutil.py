"""Small helpers for parsing LLM replies. No third-party imports."""
import re

_FENCE = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    """Return the longest fenced code block in ``text`` (or the whole text if none)."""
    blocks = _FENCE.findall(text)
    if blocks:
        return max(blocks, key=len).strip() + "\n"
    return text.strip() + "\n"


def parse_verdict(text: str) -> str:
    """Read ``VERDICT: OK|REVISED`` from the reflection step (default REVISED)."""
    m = re.search(r"VERDICT:\s*(OK|REVISED)", text, re.IGNORECASE)
    return m.group(1).upper() if m else "REVISED"


def parse_diagnosis(text: str) -> str:
    """Read ``DIAGNOSIS: TEST_BUG|CODE_BUG``; unknown replies count as CODE_BUG (stop looping)."""
    m = re.search(r"DIAGNOSIS:\s*(TEST_BUG|CODE_BUG)", text, re.IGNORECASE)
    return m.group(1).upper() if m else "CODE_BUG"


def parse_thought(text: str) -> str:
    m = re.search(r"THOUGHT:\s*(.+)", text)
    return m.group(1).strip() if m else ""
