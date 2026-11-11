from squad.analysis import analyze, format_findings

BUGGY = '''import os

def add_item(item, items=[]):
    items.append(item)
    return items

def find_max(values):
    max = values[0]
    try:
        pass
    except:
        pass
    if max == None:
        return eval("1")
    return max
'''


def kinds(code):
    return {f.kind for f in analyze(code)}


def test_syntax_error_is_reported_alone():
    findings = analyze("def broken(:\n    pass\n")
    assert [f.kind for f in findings] == ["syntax-error"]


def test_detects_expected_problems():
    found = kinds(BUGGY)
    assert {"mutable-default", "bare-except", "none-comparison", "eval-exec", "shadowed-builtin", "unused-import", "missing-docstring"} <= found


def test_clean_code_has_no_findings():
    clean = 'def add(a, b):\n    """Add two numbers."""\n    return a + b\n'
    assert analyze(clean) == []
    assert format_findings([]) == "(none)"


def test_naming_checks():
    found = kinds('def BadName():\n    """x"""\n\nclass bad_class:\n    """x"""\n')
    assert {"function-naming", "class-naming"} <= found


def test_format_findings_text():
    text = format_findings(analyze("def f(x=[]):\n    pass\n"))
    assert "mutable-default" in text and "[bug]" in text
