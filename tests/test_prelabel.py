from unittest.mock import MagicMock

import pandas as pd

from gapstudy.prelabel import classify, parse, system_prompt, user_prompt

VALID = {"test", "build_run", "architecture"}


def test_parse_keeps_valid_unique_keys_in_order():
    assert parse('{"categories": ["test", "build_run", "test", "made_up"]}', VALID) == ["test", "build_run"]


def test_parse_tolerates_prose_and_code_fences_around_json():
    assert parse('Sure!\n```json\n{"categories": ["architecture"]}\n```', VALID) == ["architecture"]


def test_parse_returns_empty_on_garbage():
    assert parse("no idea", VALID) == []
    assert parse('{"categories": ', VALID) == []
    assert parse('{"categories": "test"}', VALID) == []


def test_prompts_include_definitions_and_heading():
    cb = {"categories": {"_source": "x", "test": {"name": "Testing", "definition": "Running tests."}}}
    assert "- test: Running tests." in system_prompt(cb) and "_source" not in system_prompt(cb)
    unit = pd.Series({"heading_path": "Dev > Tests", "text": "make test"})
    assert user_prompt(unit).startswith("Section heading: Dev > Tests")
    assert "(no heading)" in user_prompt(pd.Series({"heading_path": float("nan"), "text": "x"}))


def test_classify_calls_openai_compatible_endpoint():
    session = MagicMock()
    session.post.return_value.json.return_value = {"choices": [{"message": {"content": "{}"}}]}
    assert classify(session, "http://h:8000/v1/", "m", "sys", "usr", api_key="k") == "{}"
    url, kw = session.post.call_args.args[0], session.post.call_args.kwargs
    assert url == "http://h:8000/v1/chat/completions"
    assert kw["json"]["temperature"] == 0 and kw["json"]["model"] == "m"
    assert kw["headers"] == {"Authorization": "Bearer k"}
