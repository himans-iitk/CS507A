from unittest.mock import MagicMock

import requests

from gapstudy.github_client import GitHubClient


def make_response(status, text="", headers=None):
    r = MagicMock(spec=requests.Response)
    r.status_code = status
    r.text = text
    r.headers = requests.structures.CaseInsensitiveDict(
        {"X-RateLimit-Remaining": "4000", **(headers or {})}
    )
    return r


def client(tmp_path, responses):
    session = MagicMock()
    session.get.side_effect = responses
    return GitHubClient(token="t", cache_dir=tmp_path, session=session), session


def test_second_call_served_from_cache(tmp_path):
    gh, session = client(tmp_path, [make_response(200, "# Hello")])
    assert gh.get_file("o/r", "README.md", "abc") == "# Hello"
    assert gh.get_file("o/r", "README.md", "abc") == "# Hello"
    assert session.get.call_count == 1


def test_404_is_cached_as_absent(tmp_path):
    gh, session = client(tmp_path, [make_response(404, '{"message":"Not Found"}')])
    assert gh.get_file("o/r", "CONTRIBUTING.md", "abc") is None
    assert gh.get_file("o/r", "CONTRIBUTING.md", "abc") is None
    assert session.get.call_count == 1


def test_cache_survives_new_client(tmp_path):
    gh, _ = client(tmp_path, [make_response(200, "x")])
    gh.get_file("o/r", "a.md", "abc")
    gh2, session2 = client(tmp_path, [])
    assert gh2.get_file("o/r", "a.md", "abc") == "x"
    session2.get.assert_not_called()


def test_retries_after_primary_rate_limit(tmp_path, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    limited = make_response(403, "", {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "0"})
    gh, session = client(tmp_path, [limited, make_response(200, "ok")])
    assert gh.get_file("o/r", "a.md", "abc") == "ok"
    assert session.get.call_count == 2


def test_refresh_uses_etag_and_keeps_cache_on_304(tmp_path):
    gh, session = client(tmp_path, [
        make_response(200, '{"sha": "1"}', {"ETag": '"e1"'}),
        make_response(304),
    ])
    gh.get_json("repos/o/r")
    assert gh.get_json("repos/o/r", refresh=True) == {"sha": "1"}
    assert session.get.call_args.kwargs["headers"]["If-None-Match"] == '"e1"'


def test_corrupt_cache_entry_is_refetched(tmp_path):
    gh, session = client(tmp_path, [make_response(200, "x"), make_response(200, "y")])
    gh.get_file("o/r", "a.md", "abc")
    next(tmp_path.rglob("*.json")).write_text("{truncated")
    assert gh.get_file("o/r", "a.md", "abc") == "y"
    assert session.get.call_count == 2


def test_directory_listing_is_not_a_file(tmp_path):
    gh, _ = client(tmp_path, [make_response(200, '[{"name": "a.md"}]')])
    assert gh.get_file("o/r", "docs", "abc") is None
