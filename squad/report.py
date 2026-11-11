"""Consolidated markdown review built from a ReviewResult (no LLM call needed)."""
from __future__ import annotations

from .models import ReviewResult

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def render_report(r: ReviewResult) -> str:
    lines = ["# Code Review Report", ""]
    lines.append(f"**Intent:** `{r.intent}` &nbsp;|&nbsp; **Static findings:** {len(r.static_findings)}")

    if r.bugs is not None:
        issues = sorted(r.bugs.get("issues", []) or [], key=lambda i: _SEVERITY_ORDER.get(str(i.get("severity")).lower(), 3))
        lines += ["", f"## Bugs ({len(issues)})"]
        if not issues:
            lines.append("No bugs found.")
        for i in issues:
            lines.append(f"- **[{str(i.get('severity', '?')).upper()}] {i.get('title', '')}** (line {i.get('line')})")
            lines.append(f"  - Why: {i.get('explanation', '')}")
            lines.append(f"  - Fix: {i.get('suggestion', '')}")

    if r.style is not None:
        findings = r.style.get("findings", []) or []
        lines += ["", f"## Style (score {r.style.get('score', '?')}/10, {len(findings)} finding(s))"]
        for f in findings:
            lines.append(f"- **{f.get('title', '')}** [{f.get('category', '')}] (line {f.get('line')}): {f.get('suggestion', '')}")

    if r.fixed_code is not None:
        lines += ["", "## Fix", f"Reflection verdict: `{r.fix_verdict}`. See the **Fixed code** tab for the full diff."]

    if r.explanation:
        lines += ["", "## Explanation", r.explanation]

    if r.test_run is not None:
        t = r.test_run
        status = "PASS" if t["ok"] else "FAIL"
        lines += [
            "",
            "## Tests",
            f"**{status}**: {t['tests_run']} tests run, {t['failures']} failures, {t['errors']} errors "
            f"({len(r.test_log)} sandbox attempt(s), {t['duration']}s).",
        ]

    if r.notes:
        lines += ["", "## Notes"] + [f"- {n}" for n in r.notes]
    return "\n".join(lines)
