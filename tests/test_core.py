import json

import pytest

from src.main import analyze_case
from src.prompt_loader import load_config, load_prompts, render
from src.storage import Store
from src.validator import ValidationError, parse_json, validate

CATS = load_config()["categories"]
GOOD = {
    "constraints": ["n up to 1e5"],
    "bug_category": "wrong_initialization",
    "confidence": 0.9,
    "hints": ["think", "look at init", "start with first element"],
}


class FakeLLM:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def complete(self, system, user):
        self.calls += 1
        return self.replies.pop(0)


def test_parse_json_handles_fences():
    assert parse_json("```json\n" + json.dumps(GOOD) + "\n```")["confidence"] == 0.9


def test_validate_accepts_good():
    assert validate(dict(GOOD), CATS)


@pytest.mark.parametrize(
    "patch",
    [
        {"bug_category": "banana"},
        {"confidence": 5},
        {"hints": ["only one"]},
        {"hints": ["```cpp\nx\n```", "b", "c"]},
    ],
)
def test_validate_rejects_bad(patch):
    with pytest.raises(ValidationError):
        validate({**GOOD, **patch}, CATS)


def test_render_keeps_json_braces():
    assert render('{"a": $x}', x="1") == '{"a": 1}'


def test_prompts_have_required_sections():
    assert {"system", "analyze", "repair"} <= set(load_prompts())


def test_cache_avoids_second_call(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    llm = FakeLLM([json.dumps(GOOD)])
    cfg, prompts = load_config(), load_prompts()
    analyze_case(llm, prompts, cfg, store, "Title\nbody", "code")
    _, cached = analyze_case(llm, prompts, cfg, store, "Title\nbody", "code")
    assert cached and llm.calls == 1


def test_repair_path(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    llm = FakeLLM(["not json at all", json.dumps(GOOD)])
    data, _ = analyze_case(llm, load_prompts(), load_config(), store, "T\nb", "c")
    assert data["bug_category"] == "wrong_initialization" and llm.calls == 2
