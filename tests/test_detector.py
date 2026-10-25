import json

import numpy as np
import pandas as pd

from gapstudy.detector.evaluate import evaluate_matcher, predict3, retrieval, tune_binary, variants
from gapstudy.detector.items import split_items
from gapstudy.detector.matchers import TfidfMatcher, similarity
from gapstudy.detector.score import score_repo


def test_split_items_lists_sentences_and_code():
    text = ("Intro sentence here. Second sentence follows.\n\n- [ ] Build passes: `make all`\n"
            "- Lint passes with `make lint`\n  continued detail line\n\n```bash\nmake test\n```\n| a | b |\n|---|---|\n")
    items = split_items(text)
    assert items[:2] == ["Intro sentence here.", "Second sentence follows."]
    assert "Build passes: `make all`" in items
    assert "Lint passes with `make lint` continued detail line" in items
    assert any(i.startswith("```bash") for i in items)


def test_split_items_falls_back_to_whole_text_for_short_units():
    assert split_items("Be concise.") == ["Be concise."]


def test_tfidf_similarity_is_cosine_and_sparse_safe():
    m = TfidfMatcher(["run make test before commit", "run make test", "deploy to prod", "deploy now please"])
    a, b = m.encode(["run make test"]), m.encode(["run make test", "deploy to prod"])
    s = similarity(a, b)
    assert s.shape == (1, 2) and np.isclose(s[0, 0], 1.0) and s[0, 1] < 0.2


def test_score_repo_ranks_matching_section_first():
    m = TfidfMatcher(["use pytest for unit tests", "open a pull request", "use pytest", "pull request review",
                      "pytest unit tests", "open pull request"])
    agent = pd.DataFrame({"unit_id": ["a::agent::0"]})
    human = pd.DataFrame({"unit_id": ["a::README::0", "a::CONTRIBUTING::0"]})
    a_items = ["use pytest for unit tests"]
    h_items = ["open a pull request", "use pytest for unit tests"]
    rows = score_repo(agent, human, m.encode(a_items), m.encode(h_items),
                      {"vec": m.encode(a_items), "owner": np.array(["a::agent::0"])},
                      {"vec": m.encode(h_items), "owner": np.array(["a::README::0", "a::CONTRIBUTING::0"])})
    top = json.loads(rows[0]["top"])
    assert top[0][0] == "a::CONTRIBUTING::0" and rows[0]["item_mean"] > 0.99


def test_tune_binary_and_predict3():
    score = np.array([0.1, 0.2, 0.8, 0.9])
    y = np.array([True, True, False, False])
    t = tune_binary(score, y)
    assert ((score < t) == y).all()
    assert list(predict3(np.array([0.1, 0.5, 0.9]), 0.3, 0.7)) == ["agent_only", "partial", "shared"]


def synthetic(n_repos=30, seed=0):
    """Labels plus a score that separates them with some noise."""
    rng = np.random.default_rng(seed)
    rows, scores = [], []
    for r in range(n_repos):
        for k in range(6):
            cov = ["agent_only", "partial", "shared"][k % 3]
            uid = f"r{r}::agent::{k}"
            rows.append({"unit_id": uid, "repo": f"r{r}", "set": "pilot" if r < 6 else "main",
                         "coverage": cov, "evidence": [f"r{r}::README::0"] if cov != "agent_only" else []})
            base = {"agent_only": 0.15, "partial": 0.5, "shared": 0.85}[cov]
            s = float(np.clip(base + rng.normal(0, 0.08), 0, 1))
            scores.append({"unit_id": uid, "matcher": "fake", "unit_max": s, "item_mean": s,
                           "item_max": json.dumps([s, s]), "top": json.dumps([[f"r{r}::README::0", s]])})
    return pd.DataFrame(rows), pd.DataFrame(scores)


def test_evaluate_matcher_on_separable_scores():
    labels, scores = synthetic()
    res, df = evaluate_matcher(scores, labels, n_boot=50)
    assert res["n_dev"] == 36 and res["n_test"] == 144
    assert res["f1"] > 0.95 and res["auc"] > 0.95 and res["macro_f1"] > 0.8
    assert res["retrieval_hit@1"] == 1.0 and res["f1_ci"][0] <= res["f1"] <= res["f1_ci"][1] + 1e-9


def test_evaluate_excludes_agent_directed_and_needs_dev_and_test():
    labels, scores = synthetic()
    labels.loc[0, "coverage"] = "agent_directed"
    _, df = evaluate_matcher(scores, labels, n_boot=0)
    assert "agent_directed" not in set(df.coverage)
    res, _ = evaluate_matcher(scores, labels[labels.set == "main"], n_boot=0)
    assert res == {}


def test_llm_judge_prompt_and_parse():
    from gapstudy.detector.llm_judge import parse, prompt
    unit = pd.Series({"heading_path": "Testing", "text": "Run `make test` before committing."})
    cand = pd.Series({"heading_path": float("nan"), "text": "word " * 500, "doc": "CONTRIBUTING"})
    p = prompt(unit, [cand])
    assert "AGENT SECTION (Testing)" in p and "[1] CONTRIBUTING · (no heading)" in p and p.endswith("…\n")
    assert parse('```json\n{"coverage": "partial", "covered_by": [1, "2", "x"]}\n```') == ("partial", [1, 2])
    assert parse('{"coverage": "maybe"}') == (None, [])
    assert parse("no json") == (None, [])


def test_evaluate_llm_perfect_judge_never_hurts_and_band_is_partial():
    from gapstudy.detector.evaluate import evaluate_llm
    labels, scores = synthetic(seed=1)
    res, df = evaluate_matcher(scores, labels, n_boot=0)
    perfect = labels[["unit_id", "coverage"]].rename(columns={"coverage": "llm_coverage"})
    alone, border = evaluate_llm(df, res, perfect, n_boot=0)
    assert alone["f1"] == 1.0 and alone["macro_f1"] == 1.0 and alone["llm_share"] == 1.0
    assert border["f1"] >= res["f1"] and border["llm_share"] < 1.0


def test_gapcheck_on_local_repo(tmp_path):
    from gapstudy.detector.gapcheck import check
    (tmp_path / ".github").mkdir()
    (tmp_path / "claude.md").write_text("# CLAUDE.md\n\n## Testing\nRun the unit tests with pytest before every commit.\n\n"
                                        "## Secrets\nNever commit the vault token stored in ops credentials.\n")
    (tmp_path / "README.md").write_text("# Tool\n\n## Testing\nRun the unit tests with pytest before every commit.\n")
    (tmp_path / ".github" / "CONTRIBUTING.md").write_text("# Contributing\n\n## PRs\nOpen a pull request against main.\n")
    cfg = {"matcher": "tfidf", "variant": "item_mean", "threshold": 0.5, "t1": 0.5, "t2": 0.9}
    out = check(tmp_path, cfg).set_index("heading_path")
    assert out.loc["Testing", "label"] == "shared" and out.loc["Testing", "best_match"] == "README.md::0"
    assert out.loc["Secrets", "label"] == "agent_only"


def test_variants_and_retrieval():
    s = pd.DataFrame({"unit_max": [0.2], "item_mean": [0.5], "item_max": [json.dumps([0.2, 0.8])]})
    v = variants(s)
    assert v["item_cov@0.5"][0] == 0.5 and v["item_cov@0.9"][0] == 0.0
    df = pd.DataFrame({"coverage": ["shared", "agent_only"], "evidence": [["h2"], []],
                       "top": [json.dumps([["h1", 0.9], ["h2", 0.8]]), json.dumps([])]})
    assert retrieval(df) == {"n": 1, "hit@1": 0.0, "hit@5": 1.0}
