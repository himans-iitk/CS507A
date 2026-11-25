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


def test_latex_text_escapes_markdown_excerpts():
    from gapstudy.paper_tables import clip, latex_text
    out = latex_text("- Run `make test_unit` with **care** & a $VAR {x} \\ y")
    assert r"\textbullet" in out and r"\texttt{make test\_unit}" in out
    assert "**" not in out and r"\&" in out and r"\$VAR" in out and r"\{x\}" in out and r"\textbackslash{}" in out
    assert clip("one two three four", 2).endswith(r"\dots") and not clip("one two", 5).endswith(r"\dots")


def test_new_paper_tables_render():
    from gapstudy.paper_tables import corpus, examples, flow, reliability, sensitivity
    from gapstudy.summary import facts
    f = facts()
    assert r"\label{tab:flow}" in flow(f) and r"\textbf{Sampled}" in flow(f)
    assert r"\label{tab:corpus}" in corpus(f)
    if f["reliability"].get("confusion"):
        rel = reliability(f)
        n = f["reliability"]["units"]
        assert r"\label{tab:rel}" in rel and f"& {n} \\\\" in rel  # grand total = units re-coded
    sens = sensitivity(f)
    assert sens.count(r"\midrule") == 2 or "Only" not in sens  # primary rows, then the coding-mode split
    ex = examples(f)
    assert ex == "" or (r"\label{tab:examples}" in ex and "```" not in ex)


def test_repo_histogram_counts_every_repo():
    import re
    from gapstudy.paper_figures import repo_histogram
    from gapstudy.summary import facts
    f = facts()
    tikz = repo_histogram(f)
    counts = [int(c) for c in re.findall(r"anchor=south,inner sep=1pt\] at \([^)]*\) \{(\d+)\}", tikz)]
    assert sum(counts) == len(f["repo_shares"])


def test_coding_mode_difference_is_drafted_minus_blind():
    from gapstudy.analysis.sensitivity import coding_mode
    rows = []
    for i in range(6):  # three drafted repos all agent-only, three blind repos all shared
        s = "main" if i < 3 else "reliability"
        for tool in ("claude", "agents", "copilot-instructions"):
            rows.append({"repo": f"r{i}{tool}", "tool": tool, "set": s,
                         "coverage": "agent_only" if s == "main" else "shared"})
    cm = coding_mode(pd.DataFrame(rows), {"claude": 1 / 3, "agents": 1 / 3, "copilot-instructions": 1 / 3}, n_boot=50)
    assert cm["difference"] == pytest.approx(1.0) and cm["drafted_repos"] == 9 and cm["blind_repos"] == 9


def test_architecture_figure_traces_a_real_section():
    from gapstudy.paper_figures import architecture, example_facts
    e = example_facts()
    if e is None:
        pytest.skip("pipeline outputs not available")
    tikz = architecture(e)
    assert r"\label{fig:overview}" in tikz and tikz.count(r"\node[ex]") == 6
    assert e["n_items"] == len(e["item_best"]) and f"{e['score']:.3f}" in tikz
    assert e["set"] != "pilot"  # the traced section must come from the RQ3 test data
