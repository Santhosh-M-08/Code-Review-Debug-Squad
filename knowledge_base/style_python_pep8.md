# Python Style Guidelines

## Naming conventions
Functions, methods and variables use `snake_case`. Classes use `CapWords`. Constants use `UPPER_SNAKE_CASE`.
Names should describe purpose: `total_price` is better than `tp` or `x`. Avoid single-letter names except for short loop indices (`i`, `j`) or well-known math symbols.
Never use `l`, `O` or `I` as names because they look like digits.

## Do not shadow built-ins
Names such as `max`, `min`, `sum`, `list`, `dict`, `str`, `id`, `input`, `type` and `file` are built-ins. Re-binding them (for example `max = values[0]`) hides the built-in for the rest of the scope and causes confusing bugs later. Use `largest`, `max_value`, `items`, `name`, and so on.

## Line length and whitespace
Keep lines under 79 characters (100 is acceptable in teams that agree on it). Use 4 spaces per indentation level, never tabs mixed with spaces.
Put two blank lines between top-level functions and classes, and one blank line between methods. Put spaces around operators (`a + b`) and after commas, but not inside brackets (`f(a, b)`, not `f( a, b )`).

## Imports
Put imports at the top of the file, one per line, grouped as standard library, third-party, then local. Do not use `from module import *` because it hides where names come from. Remove imports that are never used.

## Docstrings and comments
Every public module, class and function should have a docstring that states what it does, its parameters, return value and the exceptions it raises. Comments should explain why, not restate what the code does. Delete commented-out code.

## Idiomatic constructs
Compare to `None` with `is None` / `is not None`, never `== None`. Test truthiness directly (`if items:`) instead of `if len(items) > 0:`. Use `enumerate` instead of `range(len(x))` when you need the index, and `zip` to iterate several sequences together.
Prefer f-strings (`f"{name}: {score:.2f}"`) to `%` formatting or string concatenation. Prefer list/dict comprehensions for simple transformations, but fall back to a loop when the comprehension needs more than one condition or nested level.

## Function design
A function should do one thing and fit on a screen (about 40 lines). Keep the parameter count under about five; group related values into a dataclass or dict. Avoid deep nesting: return early or raise on invalid input ("guard clauses") instead of wrapping the body in several `if` levels.
Add type hints for parameters and return values (`def average(values: list[float]) -> float:`).

## Exceptions
Never use a bare `except:`; it also catches `KeyboardInterrupt` and `SystemExit`. Catch the narrowest exception you can handle (`except ValueError:`) and never silently `pass`. Raise specific exceptions with a helpful message.

## Resource handling
Open files with a `with` statement so they are closed even when an error occurs. Do not leave `print` debugging statements in library code; use the `logging` module.
