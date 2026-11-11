# Worked Debugging Examples

## Example: last element ignored when finding a maximum
Symptom: `find_max([1, 2, 9])` returns 2.
Cause: the loop is `for i in range(1, len(values) - 1)`, so the last index is never visited.
Fix: use `range(1, len(values))`, or better `for v in values[1:]`. Also handle an empty list before reading `values[0]`.

## Example: list keeps growing between calls
Symptom: `add_item("a")` returns `["a"]`, then `add_item("b")` returns `["a", "b"]`.
Cause: the default argument `items=[]` is created once and shared between calls.
Fix: `def add_item(item, items=None): items = [] if items is None else items`.

## Example: ZeroDivisionError on empty data
Symptom: `average([])` crashes with `ZeroDivisionError: division by zero`.
Cause: `total / len(numbers)` with `len(numbers) == 0`.
Fix: `if not numbers: raise ValueError("numbers must not be empty")` (or return `0.0` if the specification allows). Decide the behaviour, document it, and test it.

## Example: function returns None unexpectedly
Symptom: `result = process(data)` then `result[0]` raises `TypeError: 'NoneType' object is not subscriptable`.
Cause: the function builds a list but forgets `return`, or the `return` is only inside an `if` branch.
Fix: make sure every code path returns a value; add a final `return` at function level.

## Example: items skipped while removing from a list
Symptom: `for x in items: if x < 0: items.remove(x)` leaves some negatives in the list.
Cause: removing shifts the remaining elements left, so the iterator skips the next one.
Fix: `items = [x for x in items if x >= 0]`.

## Example: string concatenation instead of addition
Symptom: `age = input("Age: "); next_year = age + 1` raises `TypeError`.
Cause: `input` returns `str`.
Fix: `age = int(input("Age: "))`, wrapped in `try/except ValueError` to handle invalid input.

## Example: wrong result from floating-point accumulation
Symptom: summing `0.1` ten times gives `0.9999999999999999`, and `== 1.0` is False.
Fix: use `math.isclose(total, 1.0)` or `math.fsum`, or `Decimal` for exact decimal arithmetic.

## Example: dictionary KeyError
Symptom: `counts[word] += 1` raises `KeyError` the first time a word appears.
Fix: `counts[word] = counts.get(word, 0) + 1`, or use `collections.defaultdict(int)` / `collections.Counter`.

## Debugging method
Reproduce the failure with the smallest input. Read the traceback bottom-up to find the failing line. Print or log intermediate values, or use `pdb`/an IDE debugger. Form a hypothesis, change one thing, re-run. After fixing, add a regression test that fails on the old code.
