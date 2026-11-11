
"""The squad: intent routing, agentic retrieval and the five agents, wired together with LCEL."""

from __future__ import annotations

import ast
import json
from typing import Callable, Optional

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from . import analysis, config, prompts
from .intent import INTENTS, heuristic_intent, parse_intent_label
from .knowledge import KnowledgeBase, format_context
from .models import ReviewResult
from .sandbox import run_unit_tests
from .textutil import extract_code, parse_diagnosis, parse_thought, parse_verdict


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def _is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


class CodeReviewSquad:
    """Coordinates the agents. Each agent is an LCEL chain."""

    def __init__(self, llm, kb: Optional[KnowledgeBase] = None):
        self.llm = llm
        self.kb = kb

        as_json = JsonOutputParser()
        as_text = StrOutputParser()

        self.intent_chain = prompts.INTENT_PROMPT | llm | as_text
        self.retrieval_chain = prompts.RETRIEVAL_PROMPT | llm | JsonOutputParser()
        self.bug_chain = prompts.BUG_PROMPT | llm | as_json
        self.style_chain = prompts.STYLE_PROMPT | llm | JsonOutputParser()
        self.fix_chain = prompts.FIX_PROMPT | llm | as_text
        self.reflect_chain = prompts.REFLECT_PROMPT | llm | StrOutputParser()
        self.test_chain = prompts.TEST_PROMPT | llm | StrOutputParser()
        self.repair_chain = prompts.TEST_REPAIR_PROMPT | llm | StrOutputParser()
        self.explain_chain = prompts.EXPLAIN_PROMPT | llm | StrOutputParser()

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def run(
        self,
        code: str,
        request: str = "",
        intent_override: Optional[str] = None,
        progress: Optional[Callable[[str], None]] = None,
    ) -> ReviewResult:

        result = ReviewResult(
            original_code=code,
            request=request
        )

        def log(message: str) -> None:
            result.trace.append(message)

            if progress:
                progress(message)

        # 1. Intent detection and routing

        log("Router: detecting user intent...")

        result.intent, result.intent_source = self.detect_intent(
            code,
            request,
            intent_override
        )

        log(
            f"Router: intent = **{result.intent}** "
            f"(via {result.intent_source})"
        )

        # 2. Static code analysis

        log("Analysis tool: checking Python code...")

        result.static_findings = analysis.analyze(code)

        log(
            f"Analysis tool: {len(result.static_findings)} "
            "static finding(s)"
        )

        # 3. Agentic RAG

        log("Retrieval planner: starting knowledge retrieval...")

        self._decide_retrieval(result, log)

        tool_text = analysis.format_findings(
            result.static_findings
        )

        intent = result.intent

        # 4. Bug-Finder

        if intent in ("debug", "full_review"):

            log("Bug-Finder: reasoning step by step...")
            log("Bug-Finder: sending request to Gemini...")

            result.bugs = _as_dict(
                self.bug_chain.invoke(
                    {
                        "code": code,
                        "tool_findings": tool_text,
                        "guidelines": self._context(result, "bugs")
                    }
                )
            )
            log("Bug-Finder: Gemini response received.")

            log("Bug-Finder: completed.")

        # 5. Style/Lint agent

        if intent in ("style", "full_review"):

            log("Style/Lint agent: reviewing conventions...")

            result.style = _as_dict(
                self.style_chain.invoke(
                    {
                        "code": code,
                        "tool_findings": tool_text,
                        "guidelines": self._context(result, "style")
                    }
                )
            )

            log("Style/Lint agent: completed.")

        # 6. Fixer

        if intent in ("debug", "full_review"):

            self._fix(result, log)

        # 7. Explainer

        if intent == "explain":

            log("Explainer agent: writing the walkthrough...")

            result.explanation = self.explain_chain.invoke(
                {
                    "code": code,
                    "request": request or "(no specific request)",
                    "guidelines": self._context(result, None)
                }
            )

            log("Explainer: completed.")

        # 8. Test-Writer

        if intent in ("test", "debug", "full_review"):

            target = (
                code
                if intent == "test"
                else (result.fixed_code or code)
            )

            self._test(result, target, log)

        log("Done.")

        return result

    # ---------------------------------------------------------
    # Intent detection
    # ---------------------------------------------------------

    def detect_intent(
        self,
        code: str,
        request: str,
        override: Optional[str] = None
    ):
        """Detect intent without calling Gemini when an override is selected."""

        if override:
            selected = override.strip().lower()

            if selected in INTENTS:
                return selected, "override"

        # Use local heuristic instead of Gemini
        return heuristic_intent(request), "heuristic"

    # ---------------------------------------------------------
    # Agentic RAG
    # ---------------------------------------------------------

    def _decide_retrieval(self, result: ReviewResult, log) -> None:
        result.retrieval = {
            "retrieve": False,
            "query": "",
            "reason": "temporarily disabled for debugging"
        }
        log("Retrieval planner: skipped (debugging)")

    def _context(
        self,
        result: ReviewResult,
        category: Optional[str]
    ) -> str:

        if (
            not result.retrieval.get("retrieve")
            or self.kb is None
        ):
            return "(retrieval skipped)"

        log_message = (
            f"Knowledge base: searching {category or 'general'} guidelines..."
        )

        # Search the local knowledge base
        hits = self.kb.search(
            result.retrieval["query"],
            k=config.RETRIEVAL_TOP_K,
            category=category
        )

        known = {
            h["id"]
            for h in result.retrieved
        }

        result.retrieved.extend(
            h for h in hits
            if h["id"] not in known
        )

        return format_context(hits)

    # ---------------------------------------------------------
    # Fixer with reflection
    # ---------------------------------------------------------

    def _fix(self, result: ReviewResult, log) -> None:

        code = result.original_code

        bug_issues = _as_list(
            _as_dict(result.bugs).get("issues")
        )

        style_findings = _as_list(
            _as_dict(result.style).get("findings")
        )

        if not bug_issues and not style_findings:

            result.fixed_code = code
            result.fix_verdict = "NO_CHANGES"

            log("Fixer: nothing to fix")
            return

        payload = json.dumps(
            {
                "bugs": bug_issues,
                "style": style_findings
            },
            indent=2
        )

        log("Fixer: rewriting the code...")

        candidate = extract_code(
            self.fix_chain.invoke(
                {
                    "code": code,
                    "issues": payload
                }
            )
        )

        log("Fixer: rewrite completed.")

        log("Fixer (reflection): self-reviewing the rewrite...")

        reflected = self.reflect_chain.invoke(
            {
                "code": code,
                "issues": payload,
                "candidate": candidate
            }
        )

        result.fix_verdict = parse_verdict(reflected)

        final = extract_code(reflected)

        if not _is_valid_python(final):

            final = candidate

            result.notes.append(
                "The reflection step returned invalid Python, "
                "so the first rewrite was kept."
            )

        if not _is_valid_python(final):

            final = code
            result.fix_verdict = "FAILED"

            result.notes.append(
                "The Fixer could not produce valid Python; "
                "the original code is shown unchanged."
            )

        result.fixed_code = final

        log(
            f"Fixer: reflection verdict = {result.fix_verdict}"
        )

    # ---------------------------------------------------------
    # Test-Writer with ReAct loop
    # ---------------------------------------------------------

    def _test(
        self,
        result: ReviewResult,
        target_code: str,
        log
    ) -> None:

        log("Test-Writer: generating unittest cases...")

        tests = extract_code(
            self.test_chain.invoke(
                {
                    "code": target_code,
                    "guidelines": self._context(result, "testing")
                }
            )
        )

        log("Test-Writer: test generation completed.")

        run = {}

        for attempt in range(
            1,
            config.MAX_TEST_REPAIRS + 2
        ):

            log(
                "Test-Writer: running tests in the sandbox "
                f"(attempt {attempt})..."
            )

            run = run_unit_tests(
                target_code,
                tests,
                timeout=config.SANDBOX_TIMEOUT
            )

            entry = {
                "attempt": attempt,
                "tests": tests,
                "run": run,
                "thought": "",
                "diagnosis": ""
            }

            result.test_log.append(entry)

            log(
                f"Sandbox: {'PASS' if run['ok'] else 'FAIL'} "
                f"({run['tests_run']} tests, "
                f"{run['failures']} failures, "
                f"{run['errors']} errors)"
            )

            if run["ok"] or attempt > config.MAX_TEST_REPAIRS:
                break

            observation = (
                run["stderr"] + "\n" + run["stdout"]
            ).strip() or "no output"

            log("Test-Writer (ReAct): diagnosing test failures...")

            reply = self.repair_chain.invoke(
                {
                    "code": target_code,
                    "tests": tests,
                    "output": observation
                }
            )

            entry["diagnosis"] = parse_diagnosis(reply)
            entry["thought"] = parse_thought(reply)

            log(
                f"Test-Writer (ReAct): {entry['diagnosis']}. "
                f"{entry['thought']}"
            )

            if entry["diagnosis"] != "TEST_BUG":

                result.notes.append(
                    "Some tests still fail and the Test-Writer "
                    "judged the tests correct, so the failures "
                    "point to genuine bugs remaining in the code."
                )

                break

            tests = extract_code(reply)

        result.tests_code = tests
        result.test_run = run
