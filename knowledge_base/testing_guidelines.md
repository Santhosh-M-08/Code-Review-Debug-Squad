# Unit Testing Guidelines

## Structure of a good test
Use Arrange-Act-Assert. Arrange the inputs, act by calling the function once, assert on the result. Name tests after the behaviour, e.g. `test_average_of_empty_list_raises_value_error`. Keep each test focused on one behaviour.

## Which cases to cover
Cover the normal case, boundary values (empty list, single element, zero, negative numbers, very large values), invalid input (wrong type, `None`) and error cases. For every bug you fix, write a regression test that fails on the old code.

## Boundary and edge cases for common inputs
For lists: empty, one item, two items, duplicates, already sorted, reverse sorted. For numbers: zero, negative, float, very large. For strings: empty, one character, whitespace only, unicode, mixed case. For dictionaries: missing key, empty dict.

## Testing exceptions
With `unittest`, use `with self.assertRaises(ValueError):` around the call. Optionally check the message with `assertRaisesRegex`. Test that the right exception type is raised, not just any exception.

## Comparing floats
Use `self.assertAlmostEqual(actual, expected, places=7)` instead of `assertEqual` for floating-point results.

## Many inputs, one test
Use `with self.subTest(value=value):` inside a loop over a table of `(input, expected)` pairs so each failing case is reported separately.

## Mutable defaults and shared state
To detect shared mutable state, call the function twice and assert that the second result is independent of the first. Create fresh objects in `setUp` so tests cannot influence each other.

## Determinism and speed
Tests must give the same result every run. Do not depend on the current time, random numbers (seed them), network, environment variables or files that may not exist. Do not call `input()`. A unit test should run in milliseconds.

## Layout with unittest
Import the code under test, define `class TestSomething(unittest.TestCase)`, name methods `test_*`, and end the file with `if __name__ == "__main__": unittest.main()`. Run with `python -m unittest -v`.

## Assertions to prefer
Use `assertEqual`, `assertTrue`/`assertFalse`, `assertIsNone`, `assertIn`, `assertListEqual` and `assertRaises`. Avoid bare `assert` statements because they give poor failure messages and are removed under `python -O`.

## Diagnosing a failing test
First decide whether the test or the code is wrong. If the expectation contradicts the function's documented behaviour, fix the test. If the test matches the specification and the code differs, the code has a bug; report it rather than weakening the test.
