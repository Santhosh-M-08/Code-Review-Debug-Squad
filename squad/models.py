"""Plain data containers shared by the orchestrator, report and UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReviewResult:
    original_code: str
    request: str = ""
    intent: str = ""
    intent_source: str = ""  # "llm", "heuristic" or "override"
    retrieval: dict = field(default_factory=dict)  # the agent's retrieve/skip decision
    retrieved: list = field(default_factory=list)  # chunks pulled from ChromaDB
    static_findings: list = field(default_factory=list)  # output of the AST analysis tool
    bugs: Optional[dict] = None
    style: Optional[dict] = None
    fixed_code: Optional[str] = None
    fix_verdict: Optional[str] = None  # OK / REVISED / NO_CHANGES from the reflection step
    explanation: Optional[str] = None
    tests_code: Optional[str] = None
    test_run: Optional[dict] = None
    test_log: list = field(default_factory=list)  # ReAct-style attempts
    notes: list = field(default_factory=list)
    trace: list = field(default_factory=list)
