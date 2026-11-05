import json
import shutil

import pytest

from gapstudy.labels import CODING
from gapstudy.labeltool.app import PROCESSED
from gapstudy.verify.app import create_app, verdict_record

DRAFT = {"coverage": "partial", "categories": ["build_run"], "evidence": ["o/r::README::1"],
         "need": "dev_environment_tools", "barriers": ["environment_setup"], "flags": [], "drafter": "x"}


def test_correct_keeps_draft():
    r = verdict_record(DRAFT, "o/r::agent::0", "correct", None, "A", "", 5, "v")
    assert r["coverage"] == "partial" and r["accepted_draft"] and r["changed_fields"] == []


def test_wrong_to_shared_clears_need():
    r = verdict_record(DRAFT, "o/r::agent::0", "wrong", "shared", "A", "", 5, "v")
    assert r["coverage"] == "shared" and r["need"] is None and r["barriers"] == []
    assert "coverage" in r["changed_fields"] and not r["accepted_draft"]


def test_wrong_to_partial_without_need_is_marked():
    d = dict(DRAFT, coverage="shared", need=None, barriers=[])
    r = verdict_record(d, "o/r::agent::0", "wrong", "partial", "A", "", 5, "v")
    assert r["needs_detail"]


def test_wrong_requires_different_answer():
    with pytest.raises(ValueError):
        verdict_record(DRAFT, "o/r::agent::0", "wrong", "partial", "A", "", 5, "v")


@pytest.mark.skipif(not (CODING / "drafts.jsonl").exists(), reason="needs real coding data")
def test_app_roundtrip(tmp_path):
    coding = tmp_path / "coding"
    shutil.copytree(CODING, coding, ignore=shutil.ignore_patterns("labels"))
    (coding / "labels").mkdir()
    c = create_app(coding, PROCESSED, token="t").test_client()
    assert c.get("/api/list?set=pilot").status_code == 403
    lst = c.get("/api/list?set=pilot&token=t").get_json()
    assert lst["ids"] and not lst["done"]
    uid = lst["ids"][0]
    u = c.get(f"/api/unit/{uid}?token=t").get_json()
    assert u["draft"]["coverage"] and u["human"]
    other = next(k for k in ("agent_only", "shared") if k != u["draft"]["coverage"])
    r = c.post("/api/verify?token=t", json={"unit_id": uid, "name": "T", "verdict": "wrong", "coverage": other})
    assert r.status_code == 200
    saved = [json.loads(line) for line in (coding / "labels" / "pass1.jsonl").read_text().splitlines()]
    assert saved[-1]["coverage"] == other and saved[-1]["verdict"] == "wrong"
    assert c.get("/api/list?set=pilot&token=t").get_json()["done"] == [uid]
    rel = c.get("/api/list?set=reliability&token=t")
    assert rel.status_code == 400  # the blind set is never served here
