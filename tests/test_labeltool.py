import json
import shutil

import pandas as pd
import pytest

from gapstudy.github_client import PROJECT_ROOT
from gapstudy.labels import LabelStore
from gapstudy.labeltool.app import create_app

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


def test_app_requires_token(dirs):
    app = create_app(*dirs, token="t")
    c = app.test_client()
    assert c.get("/api/state").status_code == 403
    assert c.get("/api/state?token=t").status_code == 200


def test_prelabels_are_served(dirs):
    coding, processed = dirs
    pd.DataFrame({"unit_id": ["o/r::agent::0"], "categories": [json.dumps(["build_run"])]}).to_csv(
        coding / "prelabels.csv", index=False)
    c = create_app(coding, processed, token="t").test_client()
    assert c.get("/api/unit/o/r::agent::0", headers={"X-Token": "t"}).get_json()["prelabel"] == ["build_run"]


def add_draft(coding, unit_id, **kw):
    draft = {"unit_id": unit_id, "coverage": "partial", "categories": ["build_run"],
             "evidence": ["o/r::README::0"], "need": "dev_environment_tools", "barriers": ["environment_setup"],
             "flags": [], "rationale": "make is in README", "drafter": "claude-opus-5.5", **kw}
    with (coding / "drafts.jsonl").open("a") as f:
        f.write(json.dumps(draft) + "\n")
    return draft


def test_saving_requires_a_verifier_name(dirs):
    c = create_app(*dirs, token="t").test_client()
    body = {"unit_id": "o/r::agent::0", "coverage": "shared"}
    assert c.post("/api/label", headers={"X-Token": "t"}, json=body).status_code == 400
    r = c.post("/api/label", headers={"X-Token": "t", "X-Coder": "Ana"}, json=body)
    assert r.status_code == 200 and r.get_json()["coder"] == "Ana"


def test_verify_mode_shows_draft_and_logs_accept_or_change(dirs):
    coding, processed = dirs
    draft = add_draft(coding, "o/r::agent::0")
    c = create_app(coding, processed, token="t").test_client()
    h = {"X-Token": "t", "X-Coder": "Ana"}
    u = c.get("/api/unit/o/r::agent::0", headers=h).get_json()
    assert u["draft"]["coverage"] == "partial" and u["draft"]["rationale"] and not u["blind"]

    same = {k: draft[k] for k in ("coverage", "categories", "evidence", "need", "barriers", "flags")}
    rec = c.post("/api/label", headers=h, json={"unit_id": "o/r::agent::0", **same}).get_json()
    assert rec["draft_shown"] and rec["accepted_draft"] and rec["changed_fields"] == []

    rec = c.post("/api/label", headers=h, json={"unit_id": "o/r::agent::0", **same, "coverage": "agent_only",
                                                "evidence": [], "flags": ["unclear"]}).get_json()
    assert not rec["accepted_draft"] and rec["changed_fields"] == ["coverage", "evidence", "flags"]
    assert len(LabelStore(coding).records(1)) == 2  # both decisions kept


def test_reliability_units_are_blind_and_pass2_needs_a_different_person(dirs):
    coding, processed = dirs
    add_draft(coding, "o/r::agent::1")
    c = create_app(coding, processed, token="t").test_client()
    ana, ben = {"X-Token": "t", "X-Coder": "Ana"}, {"X-Token": "t", "X-Coder": "Ben"}
    u = c.get("/api/unit/o/r::agent::1", headers=ana).get_json()
    assert u["draft"] is None and u["blind"]
    rec = c.post("/api/label", headers=ana, json={"unit_id": "o/r::agent::1", "coverage": "agent_only"}).get_json()
    assert rec["draft_shown"] is False

    s_ana = c.get("/api/state?pass=2", headers=ana).get_json()
    assert s_ana["total"] == 0 and s_ana["second_coder"] == {"no_first_label": 1, "own_first_label": 1}
    s_ben = c.get("/api/state?pass=2", headers=ben).get_json()
    assert s_ben["queue"] == ["o/r::agent::1"]
    u2 = c.get("/api/unit/o/r::agent::1?pass=2", headers=ben).get_json()
    assert u2["label"] is None and u2["draft"] is None and u2["blind"]  # never sees Ana's label or the draft


def test_changed_fields_treats_lists_as_sets_and_empty_as_equal():
    from gapstudy.labeltool.app import changed_fields
    d = {"coverage": "shared", "categories": ["a", "b"], "evidence": ["x"], "need": None, "barriers": [], "flags": []}
    assert changed_fields(d, {**d, "categories": ["b", "a"], "need": ""}) == []
    assert changed_fields(d, {**d, "need": "task_process"}) == ["need"]
