import json

import pandas as pd
import pytest

from gapstudy.analysis import provenance
from gapstudy.github_client import PROJECT_ROOT
from gapstudy.paper_tables import tex

FROZEN = PROJECT_ROOT / "coding" / "labels_v1.csv"


def test_provenance_origins():
    rows = pd.DataFrame([
        {"unit_id": "a", "set": "main", "coder": "X", "draft_shown": True, "verdict": "correct"},
        {"unit_id": "b", "set": "main", "coder": "X", "draft_shown": True, "verdict": "wrong", "coverage": "partial"},
        {"unit_id": "c", "set": "pilot", "coder": "X", "draft_shown": True, "verdict": None,
         "accepted_draft": False, "changed_fields": "['evidence']"},
        {"unit_id": "d", "set": "reliability", "coder": "X", "draft_shown": False, "verdict": None},
    ])
    drafts = {"a": {"coverage": "shared"}, "b": {"coverage": "agent_only"}, "c": {"coverage": "shared"}}
    s = provenance.summary(rows, drafts)
    assert s["counts"] == {"draft_accepted": 1, "draft_details_edited": 1, "draft_corrected": 1, "blind": 1}
    assert s["n_reviewed"] == 3 and s["accept_rate"] == pytest.approx(2 / 3)
    assert s["confusion"].loc["agent_only", "partial"] == 1


def test_tex_escaping():
    assert tex("Low-level Design & Runtime_Behavior 5%") == r"Low-level Design \& Runtime\_Behavior 5\%"
    assert tex("Poor “How to Contribute”") == "Poor ``How to Contribute''"


@pytest.mark.skipif(not FROZEN.exists(), reason="needs frozen labels and pipeline outputs")
def test_pipeline_outputs_agree():
    from gapstudy.summary import facts, render
    f = facts()
    assert f["n_units"] == len(pd.read_csv(FROZEN))
    text = render("single annotator", f)
    assert "## RQ1" in text and "## RQ3" in text
    numbers = (PROJECT_ROOT / "paper" / "numbers.tex").read_text()
    status = json.loads((PROJECT_ROOT / "analysis" / "phase5" / "reliability.json").read_text())
    assert ("\\secondcodertrue" in numbers) == (status["status"] != "pending")
