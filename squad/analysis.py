"""Static code-analysis tool (pure ``ast``, no dependencies).

Its findings are handed to the Bug-Finder and Style agents as *tool evidence*, so the LLM
reasons about facts the parser actually found instead of guessing.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Optional

_SNAKE = re.compile(r"^_*[a-z][a-z0-9_]*$")
_CAPS = re.compile(r"^_*[A-Z][A-Za-z0-9]*$")
_BUILTINS_SHADOWED = {"max", "min", "sum", "list", "dict", "set", "str", "int", "float", "id", "input", "type", "len", "map", "filter", "file"}
MAX_LINE = 100
MAX_FUNC_LINES = 50


@dataclass
class Finding:
    line: Optional[int]
    kind: str
    message: str
    category: str  # "bug" or "style"


def analyze(code: str) -> list:
    """Return a list of Finding objects for ``code``."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [Finding(exc.lineno, "syntax-error", f"Code does not parse: {exc.msg}", "bug")]

    findings: list = []
    imported: dict = {}
    used: set = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _check_function(node, findings)
        elif isinstance(node, ast.ClassDef):
            if not _CAPS.match(node.name):
                findings.append(Finding(node.lineno, "class-naming", f"Class '{node.name}' should use CapWords.", "style"))
            if ast.get_docstring(node) is None:
                findings.append(Finding(node.lineno, "missing-docstring", f"Class '{node.name}' has no docstring.", "style"))
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append(Finding(node.lineno, "bare-except", "Bare 'except:' also catches KeyboardInterrupt/SystemExit.", "bug"))
        elif isinstance(node, ast.Compare):
            for op, right in zip(node.ops, node.comparators):
                if isinstance(op, (ast.Eq, ast.NotEq)) and isinstance(right, ast.Constant) and right.value is None:
                    findings.append(Finding(node.lineno, "none-comparison", "Use 'is None' / 'is not None' instead of ==/!= None.", "style"))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            findings.append(Finding(node.lineno, "eval-exec", f"Call to {node.func.id}() can execute arbitrary code.", "bug"))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported[(alias.asname or alias.name).split(".")[0]] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    imported[alias.asname or alias.name] = node.lineno
                else:
                    findings.append(Finding(node.lineno, "star-import", "Avoid 'from module import *'.", "style"))
        elif isinstance(node, ast.Name):
            used.add(node.id)
            if isinstance(node.ctx, ast.Store) and node.id in _BUILTINS_SHADOWED:
                findings.append(Finding(node.lineno, "shadowed-builtin", f"Variable '{node.id}' shadows a built-in.", "style"))

    for name, lineno in imported.items():
        if name not in used:
            findings.append(Finding(lineno, "unused-import", f"Import '{name}' is never used.", "style"))

    for number, line in enumerate(code.splitlines(), start=1):
        if len(line) > MAX_LINE:
            findings.append(Finding(number, "line-too-long", f"Line is {len(line)} characters (limit {MAX_LINE}).", "style"))

    findings.sort(key=lambda f: (f.line or 0, f.kind))
    return findings


def _check_function(node, findings: list) -> None:
    for default in list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]:
        is_literal = isinstance(default, (ast.List, ast.Dict, ast.Set))
        is_ctor = isinstance(default, ast.Call) and isinstance(default.func, ast.Name) and default.func.id in ("list", "dict", "set")
        if is_literal or is_ctor:
            findings.append(Finding(node.lineno, "mutable-default", f"Function '{node.name}' uses a mutable default argument (shared between calls).", "bug"))
    if not node.name.startswith("__") and not _SNAKE.match(node.name):
        findings.append(Finding(node.lineno, "function-naming", f"Function '{node.name}' should use snake_case.", "style"))
    if ast.get_docstring(node) is None:
        findings.append(Finding(node.lineno, "missing-docstring", f"Function '{node.name}' has no docstring.", "style"))
    end = getattr(node, "end_lineno", node.lineno)
    if end - node.lineno + 1 > MAX_FUNC_LINES:
        findings.append(Finding(node.lineno, "long-function", f"Function '{node.name}' is {end - node.lineno + 1} lines long.", "style"))


def format_findings(findings: list) -> str:
    """Render findings as text for inclusion in a prompt."""
    if not findings:
        return "(none)"
    return "\n".join(f"- [{f.category}] line {f.line}: {f.kind}: {f.message}" for f in findings)
