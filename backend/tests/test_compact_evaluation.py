import pytest
from app.services.compact_evaluation import prepare, expand
from app.services.ai_service import run


def test_source_references_expand_to_exact_cv_fragments():
    payload = {"sources": [{"location": "page:1", "text": "Python para APIs.\nSQL para consultas."}],
               "criteria": {"requirements": [{"id": 1, "name": "Python", "category": "technology"}]}}
    compact, fragments = prepare(payload)
    assert len(compact["sources"]) == 2
    expanded = expand({"evidence": [{"requirement_id": 1, "state": "evidenced",
        "explanation": "APIs em Python", "source_ids": [1]}]}, fragments)
    assert expanded["evidence"][0]["citations"] == [{"location": "page:1", "quote": "Python para APIs."}]
    class Fixture:
        name = "fixture"
        def complete(self, *args): return expanded
    result, _ = run("evaluate", payload, Fixture())
    assert result.evidence[0].state == "evidenced"


def test_unknown_source_is_rejected():
    with pytest.raises(ValueError, match="desconhecida"):
        expand({"evidence": [{"requirement_id": 1, "state": "evidenced", "explanation": "Example", "source_ids": [99]}]}, [])


def test_long_fragments_remain_literal_substrings():
    text = "x" * 1300
    _, fragments = prepare({"sources": [{"location": "p1", "text": text}], "criteria": {}})
    assert [len(item["text"]) for item in fragments] == [600, 600, 100]
    assert all(item["text"] in text for item in fragments)
