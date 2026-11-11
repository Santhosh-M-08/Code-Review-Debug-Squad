from squad.intent import heuristic_intent, parse_intent_label
from squad.knowledge import chunk_markdown
from squad.textutil import extract_code, parse_diagnosis, parse_thought, parse_verdict


def test_extract_code_prefers_longest_fenced_block():
    text = "Here:\n```python\nx = 1\n```\nand\n```python\ny = 2\nz = 3\n```"
    assert extract_code(text) == "y = 2\nz = 3\n"


def test_extract_code_without_fence():
    assert extract_code("  print(1)  ") == "print(1)\n"


def test_parsers():
    assert parse_verdict("VERDICT: ok\n```python\n```") == "OK"
    assert parse_verdict("nothing") == "REVISED"
    assert parse_diagnosis("DIAGNOSIS: TEST_BUG\nTHOUGHT: wrong import") == "TEST_BUG"
    assert parse_diagnosis("garbled") == "CODE_BUG"
    assert parse_thought("DIAGNOSIS: CODE_BUG\nTHOUGHT: real bug here") == "real bug here"


def test_parse_intent_label():
    assert parse_intent_label("Debug.") == "debug"
    assert parse_intent_label("full review") == "full_review"
    assert parse_intent_label("full-review") == "full_review"
    assert parse_intent_label("I do not know") is None


def test_heuristic_intent():
    assert heuristic_intent("why does it crash on empty input?") == "debug"
    assert heuristic_intent("explain this function") == "explain"
    assert heuristic_intent("check my naming and pep8") == "style"
    assert heuristic_intent("write unit tests") == "test"
    assert heuristic_intent("fix the bugs and write tests") == "full_review"
    assert heuristic_intent("") == "full_review"


def test_chunk_markdown_splits_on_h2():
    md = "# Title\nintro ignored\n\n## First\nalpha\n\n## Second\nbeta\n\n## Empty\n"
    chunks = chunk_markdown(md, "style_x.md", "style")
    assert [c["metadata"]["section"] for c in chunks] == ["First", "Second"]
    assert chunks[0]["text"].startswith("First\nalpha")
    assert chunks[1]["metadata"]["category"] == "style"
    assert len({c["id"] for c in chunks}) == 2


def test_real_knowledge_base_files_chunk_cleanly():
    from squad import config

    for path in config.KB_DIR.glob("*.md"):
        category = path.stem.split("_", 1)[0]
        assert category in {"style", "bugs", "testing"}
        assert len(chunk_markdown(path.read_text(encoding="utf-8"), path.name, category)) >= 5
