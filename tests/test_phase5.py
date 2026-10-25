import hashlib
import json
import shutil
from datetime import date

import pandas as pd
import pytest

from gapstudy.freeze import check, freeze
from gapstudy.github_client import PROJECT_ROOT
from gapstudy.labels import LabelStore
from gapstudy.progress import summary
from gapstudy.reliability import metrics, paired, report

COVS = ["agent_only", "partial", "shared", "agent_only", "partial", "shared", "agent_directed", "shared"]


@pytest.fixture
def coding(tmp_path):
    shutil.copy(PROJECT_ROOT / "coding" / "codebook.json", tmp_path)
    ids = [f"r{i % 4}::agent::{i}" for i in range(len(COVS))]
    pd.DataFrame({"unit_id": ids, "repo": [u.split("::")[0] for u in ids], "tool": "claude",
                  "set": "reliability", "weight": 1.0}).to_csv(tmp_path / "queue.csv", index=False)
    return tmp_path


def version(coding):
    return json.loads((coding / "codebook.json").read_text())["version"]


def save_all(coding, coding_pass, coverages, cats=None):
    store, ids = LabelStore(coding), pd.read_csv(coding / "queue.csv").unit_id
    for i, (u, c) in enumerate(zip(ids, coverages)):
        store.save(coding_pass, {
            "unit_id": u, "codebook_version": version(coding), "coverage": c,
            "categories": (cats or [["test"]] * len(ids))[i], "need": "task_process" if c in ("agent_only", "partial") else None,
            "evidence": ["h"] if c in ("partial", "shared") else [], "barriers": [], "flags": [], "notes": ""})


def test_identical_passes_give_perfect_agreement(coding):
    save_all(coding, 1, COVS)
    save_all(coding, 2, COVS)
    m = metrics(paired(LabelStore(coding), pd.read_csv(coding / "queue.csv")), ["test", "build_run"])
    assert m["coverage_kappa"] == 1 and m["coverage_weighted_kappa"] == 1
    assert m["category_jaccard"] == 1 and m["cat:test"] == 1 and m["need_kappa"] == 1


def test_weighted_kappa_penalises_adjacent_disagreement_less(coding):
    save_all(coding, 1, COVS)
    near = COVS.copy(); near[1] = "shared"       # partial -> shared (adjacent)
    save_all(coding, 2, near)
    m = metrics(paired(LabelStore(coding), pd.read_csv(coding / "queue.csv")), ["test"])
    assert m["coverage_agreement"] == 7 / 8
    assert m["coverage_weighted_kappa"] > m["coverage_kappa"]


def test_report_with_bootstrap(coding):
    assert "No units re-coded yet (0 / 8)" in report(coding, 0)
    save_all(coding, 1, COVS)
    save_all(coding, 2, COVS)
    text = report(coding, 50)
    assert "**8 / 8** in 4 repos" in text and "[1.00, 1.00]" in text


def test_freeze_refuses_incomplete_then_writes_with_checksum(coding):
    with pytest.raises(SystemExit):
        freeze(coding, "v1")
    LabelStore(coding).save(1, {"unit_id": "r0::agent::0", "codebook_version": "0.0", "coverage": "shared"})
    _, issues = check(coding)
    assert any("not labelled" in i for i in issues) and any("older codebook" in i for i in issues)

    save_all(coding, 1, COVS)
    path = freeze(coding, "v1")
    df = pd.read_csv(path)
    assert len(df) == 8 and json.loads(df.categories[0]) == ["test"] and set(df.set) == {"reliability"}
    digest = (coding / "labels_v1.sha256").read_text().split()[0]
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()


def test_progress_statuses(coding):
    s = summary(coding, date(2026, 11, 3))
    assert s.loc["reliability", "status"] == "4 units/day to finish by Nov 04"  # Nov 3 and Nov 4 left
    assert s.loc["re-code", "status"] == "starts Nov 16"
    save_all(coding, 1, COVS)
    assert summary(coding, date(2026, 11, 3)).loc["reliability", "status"] == "done"
