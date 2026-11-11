from squad.sandbox import run_unit_tests

SOLUTION = "def add(a, b):\n    return a + b\n"

PASSING = """import unittest
from solution import add

class T(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

if __name__ == "__main__":
    unittest.main()
"""

FAILING = PASSING.replace("5)", "6)")


def test_passing_tests():
    r = run_unit_tests(SOLUTION, PASSING, timeout=10)
    assert r["ok"] and r["tests_run"] == 1 and r["failures"] == 0


def test_failing_tests_are_reported():
    r = run_unit_tests(SOLUTION, FAILING, timeout=10)
    assert not r["ok"] and r["failures"] == 1


def test_infinite_loop_times_out():
    r = run_unit_tests("def add(a, b):\n    while True:\n        pass\n", PASSING, timeout=2)
    assert r["timed_out"] and not r["ok"]


def test_input_does_not_hang():
    r = run_unit_tests("x = input('?')\ndef add(a, b):\n    return a + b\n", PASSING, timeout=5)
    assert not r["ok"] and not r["timed_out"]


def test_environment_is_stripped(monkeypatch):
    monkeypatch.setenv("SECRET_API_KEY", "hunter2")
    code = "import os\ndef add(a, b):\n    return a + b\nLEAK = os.environ.get('SECRET_API_KEY')\n"
    tests = PASSING.replace("self.assertEqual(add(2, 3), 5)", "import solution\n        self.assertIsNone(solution.LEAK)")
    assert run_unit_tests(code, tests, timeout=5)["ok"]
