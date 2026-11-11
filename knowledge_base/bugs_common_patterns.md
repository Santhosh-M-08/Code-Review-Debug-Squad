# Common Bug Patterns in Python

## Off-by-one errors in loops and slices
`range(1, len(values) - 1)` stops before the last element, so the final item is never examined. `range(n)` yields `0..n-1`; `range(1, n + 1)` yields `1..n`. Slices exclude the end index: `values[0:3]` has three items. When a loop must visit every element, iterate directly (`for v in values`) instead of managing indices.

## Empty input and index errors
`values[0]`, `max(values)`, `min(values)` and `sum(values) / len(values)` all fail on an empty sequence (`IndexError`, `ValueError`, `ZeroDivisionError`). Check for empty input first and either return a sensible default or raise a clear `ValueError`.

## Division by zero and integer division
Dividing by a value that can be zero raises `ZeroDivisionError`. Guard the denominator. In Python 3 `/` is true division and `//` is floor division; `7 // 2 == 3` and `-7 // 2 == -4`, which surprises people expecting truncation towards zero.

## Mutable default arguments
`def add(item, items=[])` creates the list once, when the function is defined, so every call that omits `items` shares and mutates the same list. Use `items=None` and create the list inside: `if items is None: items = []`. The same applies to `{}` and `set()` defaults.

## None handling
Functions such as `dict.get`, `re.match`, `str.find` (returns -1, not None) and many user functions may return `None` or a sentinel. Using the result without checking causes `AttributeError: 'NoneType' object has no attribute ...`. Check before use.

## Modifying a collection while iterating
Removing or inserting items in a list while looping over it skips elements. Iterate over a copy (`for x in list(items)`), build a new list with a comprehension, or collect removals and apply them afterwards. Changing a dict's size during iteration raises `RuntimeError`.

## Identity versus equality
`is` compares object identity, `==` compares value. `x is 5` or `name is "abc"` may work by accident because of interning and then break. Use `==` for values and `is` only for `None`, `True`, `False`.

## Floating-point comparison
`0.1 + 0.2 == 0.3` is `False`. Compare floats with `math.isclose(a, b)` or a tolerance. Never use floats for money; use `decimal.Decimal` or integer cents.

## Late binding in closures
`[lambda: i for i in range(3)]` creates three lambdas that all return 2, because `i` is looked up when the lambda runs. Bind the current value with a default argument: `lambda i=i: i`.

## Unreachable or wrong return placement
A `return` inside a loop body returns on the first iteration; a missing `return` yields `None`. Check indentation: code intended to run after the loop must be dedented out of it.

## Unsafe use of eval and exec
`eval(user_input)` and `exec(...)` run arbitrary code. Use `ast.literal_eval` for literals or a proper parser. Never build SQL with string formatting; use parameterised queries.

## Integer parsing and type mix-ups
`input()` returns a string, so `input() + 1` raises `TypeError` and `"5" + "5"` is `"55"`. Convert explicitly with `int()` or `float()` and handle `ValueError` for bad input.

## Recursion without a base case
A recursive function must reach a base case on every path, otherwise it raises `RecursionError`. Check that each call moves towards the base case, e.g. `n - 1`.
