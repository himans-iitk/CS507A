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


def test_problems_treat_nan_as_missing():
    from gapstudy.pilot_report import problems
    row = pd.Series({"coverage": "agent_only", "need": float("nan"), "evidence": [], "categories": ["test"]})
    assert problems(row) == ["no newcomer need (D1)"]
    row = pd.Series({"coverage": "partial", "need": "task_process", "evidence": float("nan"), "categories": ["test"]})
    assert problems(row) == ["partial/shared without evidence"]


def test_combine_takes_need_from_second_pass_only_for_shared_gaps():
    from gapstudy.freeze import combine
    labels = pd.DataFrame([
        {"unit_id": "a", "coverage": "agent_only", "need": None, "barriers": []},
        {"unit_id": "b", "coverage": "partial", "need": None, "barriers": []},
        {"unit_id": "c", "coverage": "partial", "need": "task_process", "barriers": ["finding_task"]},
        {"unit_id": "d", "coverage": "shared", "need": None, "barriers": []},
    ])
    second = {"a": {"coverage": "partial", "need": "development_process", "barriers": ["process_practices"], "coder": "B"},
              "b": {"coverage": "shared", "need": None, "coder": "B"},
              "c": {"coverage": "agent_only", "need": "software_architecture", "coder": "B"}}
    out = combine(labels, second).set_index("unit_id")
    assert out.loc["a", "need"] == "development_process" and out.loc["a", "need_source"] == "pass2:B"
    assert out.loc["a", "coverage"] == "agent_only"          # coverage stays the first annotator's
    assert pd.isna(out.loc["b", "need"])                      # second coder saw no gap: nothing borrowed
    assert out.loc["c", "need"] == "task_process" and out.loc["c", "need_source"] == "pass1"
    assert pd.isna(out.loc["d", "need_source"])


def test_agreement_kind(tmp_path):
    from gapstudy.reliability import agreement_kind
    (tmp_path / "annotators.json").write_text(json.dumps({"A": {"type": "human"}, "B": {"type": "human"},
                                                          "L": {"type": "llm"}}))
    assert agreement_kind({"A"}, {"A"}, tmp_path) == "intra-rater"
    assert agreement_kind({"A"}, {"B"}, tmp_path) == "inter-rater"
    assert agreement_kind({"A"}, {"L"}, tmp_path) == "human-llm"


@pytest.mark.skipif(not FROZEN.exists(), reason="needs frozen labels and pipeline outputs")
def test_rq1_figure_has_both_panels():
    from gapstudy.paper_figures import figure
    from gapstudy.summary import facts
    f = facts()
    tikz = figure(f)
    assert r"\label{fig:rq1}" in tikz and "(a) By agent" in tikz and "(b) By instruction category" in tikz
    assert tikz.count("\\fill[covA]") >= len(f["categories"]) + 4  # one agent-only segment per bar (+ legend)
