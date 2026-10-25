import json

import pandas as pd

from gapstudy.labels import LabelStore
from gapstudy.labeltool.app import create_app
from gapstudy.pilot_report import build, problems
from tests.test_labeltool import dirs  # noqa: F401  (fixture)


def label(**kw):
    base = {"evidence": [], "categories": ["test"], "need": None, "coverage": "shared", "flags": [], "notes": ""}
    return pd.Series({**base, **kw})


def test_problems_flags_inconsistent_records():
    assert problems(label(coverage="shared")) == ["partial/shared without evidence"]
    assert problems(label(coverage="agent_only", evidence=["x"], need="task_process")) == ["agent-only but evidence ticked"]
    assert problems(label(coverage="partial", evidence=["x"])) == ["no newcomer need (D1)"]
    assert problems(label(coverage="agent_directed", categories=[])) == []
    assert problems(label(coverage="shared", evidence=["x"], categories=[])) == ["no category"]


def test_report_empty_then_with_labels(dirs):  # noqa: F811
    coding, processed = dirs
    assert "0 / 1 units coded" in build(coding, processed, "pilot")

    store = LabelStore(coding)
    version = json.loads((coding / "codebook.json").read_text())["version"]
    store.save(1, {"unit_id": "o/r::agent::0", "codebook_version": version, "coverage": "agent_only",
                   "categories": ["build_run"], "evidence": [], "need": "dev_environment_tools",
                   "barriers": [], "flags": ["unclear"], "notes": "build cmd only in Makefile", "seconds": 40})
    report = build(coding, processed, "pilot")
    assert "1 / 1 units" in report and "1 / 1 repos complete" in report
    assert "build cmd only in Makefile" in report and "[unclear]" in report
    assert "Consistency problems to fix\n\nNone." in report


def test_recheck_mode_lists_pilot_units_with_old_codebook_version(dirs):  # noqa: F811
    coding, processed = dirs
    store = LabelStore(coding)
    store.save(1, {"unit_id": "o/r::agent::0", "codebook_version": "0.0-old", "coverage": "shared"})
    c = create_app(coding, processed, token="t").test_client()
    s = c.get("/api/state?recheck=1", headers={"X-Token": "t"}).get_json()
    assert s["queue"] == ["o/r::agent::0"] and s["next"] == "o/r::agent::0"
    assert c.get("/api/state", headers={"X-Token": "t"}).get_json()["done"] == 1  # normal mode: counts as done
