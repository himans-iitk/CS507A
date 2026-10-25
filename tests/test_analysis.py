import json

import numpy as np
import pandas as pd
import pytest

from gapstudy.analysis import rq1, rq2, sensitivity
from gapstudy.analysis.report import build
from gapstudy.github_client import PROJECT_ROOT

CODEBOOK = json.loads((PROJECT_ROOT / "coding" / "codebook.json").read_text())
TRUE_RATE = {"claude": 0.5, "agents": 0.3, "copilot-instructions": 0.2}
SHARES = {"claude": 0.334, "agents": 0.283, "copilot-instructions": 0.383}


@pytest.fixture(scope="module")
def synthetic():
    """60 repos per agent, 10 units each; units with 'security' are agent-only far more often."""
    rng = np.random.default_rng(1)
    rows = []
    for tool, rate in TRUE_RATE.items():
        for r in range(60):
            repo = f"{tool}/r{r}"
            for k in range(10):
                cat = ["security"] if k < 2 else (["test"] if k < 8 else [])  # some units have no category
                p = min(0.95, rate * (2.5 if cat == ["security"] else 0.8))
                cov = "agent_only" if rng.random() < p else rng.choice(["partial", "shared"])
                if k == 9 and r % 10 == 0:
                    cov = "agent_directed"
                rows.append({"unit_id": f"{repo}::agent::{k}", "repo": repo, "tool": tool, "weight": 1.0,
                             "coverage": cov, "categories": cat,
                             "need": "dev_environment_tools" if k % 2 else "software_architecture",
                             "barriers": ["environment_setup"] if k % 2 else [],
                             "flags": ["links_out"] if k == 0 else [], "evidence": [],
                             "init_unedited": tool == "claude" and r < 6, "stub_contributing": r % 15 == 0})
    return pd.DataFrame(rows)


def test_repo_table_excludes_agent_directed(synthetic):
    t = rq1.repo_table(synthetic).set_index("repo")
    assert t.loc["claude/r0", "units"] == 9 and t.loc["claude/r1", "units"] == 10
    assert np.isclose(t.loc["claude/r0", "agent_directed_share"], 0.1)
    assert np.allclose(t[["agent_only", "partial", "shared"]].sum(axis=1), 1)


def test_headline_recovers_rates_and_post_stratifies(synthetic):
    h = rq1.headline(synthetic, SHARES, n_boot=200).set_index(["outcome", "scope"])
    expected = {t: r * (0.2 * 2.5 + 0.8 * 0.8) for t, r in TRUE_RATE.items()}  # mix of security/test units
    for t, e in expected.items():
        row = h.loc[("agent_only", t)]
        assert abs(row.estimate - e) < 0.07 and row.lo <= row.estimate <= row.hi
    per = {t: h.loc[("agent_only", t)].estimate for t in TRUE_RATE}
    assert np.isclose(h.loc[("agent_only", "overall")].estimate, sum(per[t] * SHARES[t] for t in per) / sum(SHARES.values()))


def test_gee_finds_category_and_agent_effects(synthetic):
    g = rq1.gee(synthetic, ["security", "test", "ui_ux"])
    assert "ui_ux" in g.attrs["dropped"]
    assert g.loc["cat:security", "odds_ratio"] > 2 and g.loc["cat:security", "p"] < 0.001
    assert g.loc["agent:copilot-instructions", "odds_ratio"] < 1  # lower agent-only rate than CLAUDE.md


def test_by_category_and_unit_level(synthetic):
    bc = rq1.by_category(synthetic, {"security": "Security", "test": "Testing"}).set_index("category")
    assert bc.loc["Security", "agent_only"] > bc.loc["Testing", "agent_only"]
    u = rq1.unit_level(synthetic)
    assert np.isclose(u["agent_only"] + u["partial"] + u["shared"], 1)


def test_rq2_tables(synthetic):
    n = rq2.needs(synthetic, CODEBOOK)
    assert np.isclose(n.share.sum(), 1) and set(n.need) == {"Development Environment and Tools", "Software Architecture"}
    b = rq2.barriers(synthetic, CODEBOOK).set_index("barrier")
    assert np.isclose(b.loc["Local environment setup hurdles", "share_of_gap_units"]
                      + b.loc["(no barrier coded)", "share_of_gap_units"], 1)
    units = synthetic[["unit_id"]].assign(heading_path="H", text="Run make dev to start the local stack.")
    ex = rq2.examples(synthetic, units, CODEBOOK)
    assert ex and ex == rq2.examples(synthetic, units, CODEBOOK)  # deterministic


def test_sensitivity_variants_drop_the_right_rows(synthetic):
    s = sensitivity.table(synthetic, SHARES).set_index("variant")
    assert s.loc["all coded repos (primary)", "repos"] == 180
    assert s.loc["without unedited /init files", "repos"] == 174
    assert s.loc["without stub CONTRIBUTING", "repos"] == 180 - 12


def test_report_builds_with_and_without_labels(synthetic):
    units = synthetic[["unit_id"]].assign(heading_path="H", text="Run make dev to start the local stack.")
    text, tables = build(synthetic, True, SHARES, CODEBOOK, units, n_boot=50)
    assert "Provisional" in text and "## RQ1" in text and "## RQ2" in text and "Logistic GEE" in text
    assert {"rq1_headline", "rq1_by_category", "rq2_needs", "rq2_barriers", "sensitivity"} <= set(tables)
    empty, _ = build(pd.DataFrame(), True, SHARES, CODEBOOK, units, n_boot=0)
    assert "No labels yet" in empty
