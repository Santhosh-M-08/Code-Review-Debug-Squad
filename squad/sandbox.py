"""Isolated code-execution sandbox used by the Test-Writer agent.

The code under test and the generated unittest file are written to a throw-away directory
and run in a separate Python process with:
  * a wall-clock timeout (subprocess) and CPU / memory / file-size limits (POSIX rlimits),
  * a stripped environment (no API keys or other secrets are passed on),
  * stdin closed (``input()`` raises EOFError instead of hanging),
  * the temporary directory as the working directory, deleted afterwards.

This is a practical safeguard for a student project, not a hard security boundary.
For production use, run the same command inside a container (e.g. Docker with --network none).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MAX_OUTPUT = 8000

_BOOT = '''\
import sys
try:
    import resource
    for _res, _val in (
        (resource.RLIMIT_CPU, {cpu}),
        (resource.RLIMIT_AS, 512 * 1024 * 1024),
        (resource.RLIMIT_FSIZE, 10 * 1024 * 1024),
    ):
        try:
            resource.setrlimit(_res, (_val, _val))
        except (ValueError, OSError):
            pass
except ImportError:  # e.g. Windows
    pass
import unittest
unittest.main(module=None, argv=["unittest", "-v", "test_solution"])
'''


def _decode(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _clip(text: str) -> str:
    return text if len(text) <= MAX_OUTPUT else text[:MAX_OUTPUT] + "\n... [output truncated]"


def run_unit_tests(solution_code: str, test_code: str, timeout: int = 10) -> dict:
    """Run ``test_code`` (a unittest module importing ``solution``) against ``solution_code``.

    Returns a dict with: ok, returncode, stdout, stderr, timed_out, duration, tests_run,
    failures, errors.
    """
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8", "PYTHONHASHSEED": "0"}
    if os.name == "nt":
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")

    with tempfile.TemporaryDirectory(prefix="squad_sandbox_") as tmp:
        root = Path(tmp)
        (root / "solution.py").write_text(solution_code, encoding="utf-8")
        (root / "test_solution.py").write_text(test_code, encoding="utf-8")
        (root / "_boot.py").write_text(_BOOT.format(cpu=timeout + 2), encoding="utf-8")

        start = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(
                [sys.executable, "-E", "-s", "-B", "_boot.py"],
                cwd=tmp,
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=timeout,
            )
            returncode, stdout, stderr = proc.returncode, _decode(proc.stdout), _decode(proc.stderr)
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            returncode = -1
            stdout, stderr = _decode(exc.stdout), _decode(exc.stderr)
            stderr += f"\nTimed out after {timeout}s (possible infinite loop)."
        duration = time.monotonic() - start

    combined = stderr + "\n" + stdout
    ran = re.search(r"Ran (\d+) tests?", combined)
    failures = re.search(r"failures=(\d+)", combined)
    errors = re.search(r"errors=(\d+)", combined)
    return {
        "ok": returncode == 0 and not timed_out,
        "returncode": returncode,
        "stdout": _clip(stdout),
        "stderr": _clip(stderr),
        "timed_out": timed_out,
        "duration": round(duration, 2),
        "tests_run": int(ran.group(1)) if ran else 0,
        "failures": int(failures.group(1)) if failures else 0,
        "errors": int(errors.group(1)) if errors else 0,
    }
