import json
import shutil
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from gapstudy.github_client import PROJECT_ROOT
from gapstudy.labels import LabelStore
from gapstudy.labeltool.app import create_app

NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)


@pytest.fixture
def dirs(tmp_path):
    coding, processed = tmp_path / "coding", tmp_path / "processed"
    coding.mkdir(), processed.mkdir()
    shutil.copy(PROJECT_ROOT / "coding" / "codebook.json", coding)
    pd.DataFrame({
        "unit_id": ["o/r::agent::0", "o/r::agent::1", "o/s::agent::0"],
        "repo": ["o/r", "o/r", "o/s"], "n": [0, 1, 0], "tool": "claude",
        "set": ["pilot", "reliability", "reliability"], "repo_order": [0, 1, 2], "weight": 1.0,
        "queue_pos": [0, 1, 2],
    }).to_csv(coding / "queue.csv", index=False)
    pd.DataFrame({
        "unit_id": ["o/r::agent::0", "o/r::agent::1", "o/s::agent::0", "o/r::README::0", "o/r::CONTRIBUTING::0"],
        "repo": ["o/r", "o/r", "o/s", "o/r", "o/r"], "tool": "claude",
        "doc": ["agent", "agent", "agent", "README", "CONTRIBUTING"], "n": [0, 1, 0, 0, 0],
        "kind": "section", "heading_path": ["Build", "Test", "X", "Intro", "PRs"],
        "text": ["Run `make`.", "Run `make test`.", "x", "A tool.", "Open a PR."], "words": 3, "toc": False,
    }).to_csv(processed / "units.csv", index=False)
    return coding, processed


def test_store_latest_wins_and_history_kept(tmp_path):
    s = LabelStore(tmp_path)
    s.save(1, {"unit_id": "u", "coverage": "shared"})
    s.save(1, {"unit_id": "u", "coverage": "partial"})
    assert s.latest(1)["u"]["coverage"] == "partial"
    assert len(s.records(1)) == 2


def test_recode_queue_only_old_reliability_units_and_shuffled_deterministically(tmp_path):
    s = LabelStore(tmp_path)
    q = pd.DataFrame({"unit_id": [f"u{i}" for i in range(10)] + ["p"], "set": ["reliability"] * 10 + ["pilot"]})
    for i in range(10):
        s.save(1, {"unit_id": f"u{i}"}, now=NOW - timedelta(days=20 if i < 8 else 3))
    s.save(1, {"unit_id": "p"}, now=NOW - timedelta(days=30))
    ids = s.queue(2, q, now=NOW)
    assert sorted(ids) == [f"u{i}" for i in range(8)]
    assert ids == s.queue(2, q, now=NOW) and ids != sorted(ids)
    assert s.recode_pending(q, now=NOW) == (2, (NOW + timedelta(days=11)).date().isoformat())


def test_app_requires_token(dirs):
    app = create_app(*dirs, token="t")
    c = app.test_client()
    assert c.get("/api/state").status_code == 403
    assert c.get("/api/state?token=t").status_code == 200


def test_app_unit_save_and_blind_second_pass(dirs):
    coding, processed = dirs
    app = create_app(coding, processed, token="t")
    c = app.test_client()
    h = {"X-Token": "t"}
    state = c.get("/api/state?pass=1", headers=h).get_json()
    assert state["next"] == "o/r::agent::0" and state["total"] == 3

    unit = c.get("/api/unit/o/r::agent::1?pass=1", headers=h).get_json()
    assert [x["doc"] for x in unit["human"]] == ["README", "CONTRIBUTING"]

    r = c.post("/api/label?pass=1", headers=h, json={"unit_id": "o/r::agent::1", "coverage": "agent_only",
                                                    "categories": ["test"], "need": "dev_environment_tools"})
    assert r.status_code == 200 and r.get_json()["codebook_version"] == json.loads(
        (coding / "codebook.json").read_text())["version"]
    assert c.post("/api/label?pass=1", headers=h, json={"unit_id": "o/r::agent::1"}).status_code == 400

    # pass 2 never exposes the pass-1 label, and the unit is not yet eligible (< 14 days)
    assert c.get("/api/unit/o/r::agent::1?pass=2", headers=h).get_json()["label"] is None
    s2 = c.get("/api/state?pass=2", headers=h).get_json()
    assert s2["total"] == 0 and s2["recode_waiting"] == 1


def test_prelabels_are_served(dirs):
    coding, processed = dirs
    pd.DataFrame({"unit_id": ["o/r::agent::0"], "categories": [json.dumps(["build_run"])]}).to_csv(
        coding / "prelabels.csv", index=False)
    c = create_app(coding, processed, token="t").test_client()
    assert c.get("/api/unit/o/r::agent::0", headers={"X-Token": "t"}).get_json()["prelabel"] == ["build_run"]
