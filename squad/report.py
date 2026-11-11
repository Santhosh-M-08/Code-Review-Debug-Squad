
"""Human-friendly consolidated code review report."""

from __future__ import annotations

from .models import ReviewResult


SEVERITY_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
}

SEVERITY_LABELS = {
    "high": "🔴 High Priority",
    "medium": "🟠 Medium Priority",
    "low": "🟡 Low Priority",
}

INTENT_LABELS = {
    "debug": "Bug Detection",
    "style": "Code Quality Review",
    "explain": "Code Explanation",
    "test": "Test Generation",
    "full_review": "Complete Code Review",
}


def render_report(r: ReviewResult) -> str:

    lines = [
        "# 🔍 Code Review Report",
        "",
        "Here is a summary of the analysis performed by your Code Review Squad.",
        "",
        "---",
        "",
        "## 📋 Review Overview",
        "",
        f"- **Review Type:** {INTENT_LABELS.get(r.intent, r.intent)}",
        f"- **Static Analysis Findings:** {len(r.static_findings)}",
    ]

    # Collect bug information
    issues = []

    if r.bugs is not None:
        issues = sorted(
            r.bugs.get("issues", []) or [],
            key=lambda i: SEVERITY_ORDER.get(
                str(i.get("severity", "")).lower(), 3
            )
        )

    high = sum(
        1 for i in issues
        if str(i.get("severity", "")).lower() == "high"
    )

    medium = sum(
        1 for i in issues
        if str(i.get("severity", "")).lower() == "medium"
    )

    low = sum(
        1 for i in issues
        if str(i.get("severity", "")).lower() == "low"
    )

    lines += [
        "",
        "### Issues Summary",
        "",
        f"- 🔴 **High Priority:** {high}",
        f"- 🟠 **Medium Priority:** {medium}",
        f"- 🟡 **Low Priority:** {low}",
        f"- **Total Bugs Identified:** {len(issues)}",
    ]

    # Bug-Finder results
    if r.bugs is not None:

        lines += [
            "",
            "---",
            "",
            "## 🐛 1. Bugs and Problems Found",
            "",
        ]

        if not issues:
            lines.append(
                "✅ No bugs were identified by the Bug-Finder agent."
            )

        for number, issue in enumerate(issues, start=1):

            severity = str(
                issue.get("severity", "low")
            ).lower()

            label = SEVERITY_LABELS.get(
                severity, "⚪ Other"
            )

            line_number = issue.get("line")

            lines += [
                f"### {number}. {issue.get('title', 'Unnamed issue')}",
                "",
                f"**Priority:** {label}",
                "",
            ]

            if line_number is not None:
                lines.append(f"**Location:** Line {line_number}")
                lines.append("")

            lines += [
                "**What is the problem?**",
                str(issue.get("explanation", "No explanation provided.")),
                "",
                "**How can it be fixed?**",
                str(issue.get("suggestion", "No suggestion provided.")),
                "",
            ]

    # Style/Lint results
    if r.style is not None:

        findings = r.style.get("findings", []) or []
        score = r.style.get("score", "?")

        lines += [
            "---",
            "",
            "## ✨ 2. Code Quality and Style",
            "",
            f"**Code Quality Score:** {score}/10",
            "",
        ]

        if not findings:
            lines.append(
                "✅ No major style or readability issues were identified."
            )

        for number, finding in enumerate(findings, start=1):

            lines += [
                f"### {number}. {finding.get('title', 'Code improvement')}",
                "",
            ]

            category = finding.get("category")

            if category:
                lines.append(f"**Category:** {category}")
                lines.append("")

            line_number = finding.get("line")

            if line_number is not None:
                lines.append(f"**Location:** Line {line_number}")
                lines.append("")

            lines += [
                "**Suggested improvement:**",
                str(finding.get("suggestion", "No suggestion provided.")),
                "",
            ]

    # Fixed code information
    if r.fixed_code is not None:

        lines += [
            "---",
            "",
            "## 🛠️ 3. Suggested Code Fix",
            "",
            "The Fixer agent has generated an improved version of your code.",
            "",
            f"**Self-review result:** {r.fix_verdict or 'Not available'}",
            "",
            "👉 Open the **Fixed Code** tab to view the corrected code.",
        ]

    # Explanation
    if r.explanation:

        lines += [
            "",
            "---",
            "",
            "## 📖 4. Code Explanation",
            "",
            r.explanation,
        ]

    # Test results
    if r.test_run is not None:

        t = r.test_run

        passed = (
            t["tests_run"]
            - t["failures"]
            - t["errors"]
        )

        status = (
            "✅ PASSED"
            if t["ok"]
            else "❌ FAILED"
        )

        lines += [
            "",
            "---",
            "",
            "## 🧪 5. Test Results",
            "",
            f"**Overall Status:** {status}",
            "",
            "| Test Metric | Result |",
            "|---|---:|",
            f"| Total Tests | {t['tests_run']} |",
            f"| Passed | {passed} |",
            f"| Failed | {t['failures']} |",
            f"| Errors | {t['errors']} |",
            f"| Execution Time | {t['duration']} seconds |",
            "",
            f"**Testing Attempts:** {len(r.test_log)}",
            "",
        ]

        if t["ok"]:
            lines.append(
                "All generated tests passed successfully."
            )
        else:
            lines.append(
                "Some tests did not pass. Review the failed tests "
                "and update the code before considering it complete."
            )

    # Additional notes
    if r.notes:

        lines += [
            "",
            "---",
            "",
            "## 📝 6. Additional Notes",
            "",
        ]

        for note in r.notes:
            lines.append(f"- {note}")

    # Final recommendation
    lines += [
        "",
        "---",
        "",
        "## 🎯 Final Recommendation",
        "",
    ]

    if r.test_run is not None and not r.test_run["ok"]:
        lines.append(
            "Review the remaining test failures and correct the "
            "identified issues before using the code."
        )
    elif issues:
        lines.append(
            "Review the identified problems and apply the suggested "
            "corrections. Run the tests again to verify the changes."
        )
    else:
        lines.append(
            "No bugs were identified by the Bug-Finder agent. "
            "Review the suggested improvements and test results "
            "before using the code."
        )

    return "\n".join(lines)
