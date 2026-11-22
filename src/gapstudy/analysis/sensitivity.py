"""Sensitivity of the RQ1 headline to sample and scope choices.

  - drop repos whose agent file is unedited /init output (12 CLAUDE.md files)
  - drop repos whose CONTRIBUTING is a stub (< 50 words, usually a link to a website)
  - drop units the coder flagged links_out (the human docs point elsewhere for the topic)
  - docs/ as human documentation: for the 30-repo docs/ subsample, re-score the
    agent-only units against README + CONTRIBUTING + docs/*.md with the tuned
    detector; units that would then match are counted as covered. This is an
    automatic estimate, since manual coding used README and CONTRIBUTING only.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from gapstudy.analysis.rq1 import bootstrap, estimate, repo_table
from gapstudy.github_client import PROJECT_ROOT

PROCESSED = PROJECT_ROOT / "data" / "processed"
CONFIG = PROJECT_ROOT / "detector" / "config.json"


def variants(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "all coded repos (primary)": df,
        "without unedited /init files": df[~df.init_unedited.fillna(False).astype(bool)],
        "without stub CONTRIBUTING": df[~df.stub_contributing.fillna(False).astype(bool)],
        "without links_out units": df[~df["flags"].map(lambda f: "links_out" in (f or []))],
        # How the labels were produced: AI draft reviewed by the annotator vs coded blind (reliability set).
        "only AI-drafted repos (pilot + main)": df[df["set"] != "reliability"] if "set" in df else df.iloc[0:0],
        "only blind-coded repos (reliability set)": df[df["set"] == "reliability"] if "set" in df else df.iloc[0:0],
    }


def table(df: pd.DataFrame, shares: dict[str, float], n_boot: int = 1000) -> pd.DataFrame:
    rows = []
    for name, d in variants(df).items():
        repos = repo_table(d)
        if repos.empty:
            continue
        est = estimate(repos, shares, "agent_only")
        boot = bootstrap(repos, shares, "agent_only", n_boot) if n_boot else None
        lo, hi = ((boot.overall.quantile(.025), boot.overall.quantile(.975)) if boot is not None
                  else (np.nan, np.nan))
        rows.append({"variant": name, "repos": len(repos), "agent_only": est["overall"], "lo": lo, "hi": hi,
                     **{f"agent_only:{t}": v for t, v in est.items() if t != "overall"}})
    return pd.DataFrame(rows)


def coding_mode(df: pd.DataFrame, shares: dict[str, float], n_boot: int = 1000, seed: int = 507) -> dict | None:
    """Agent-only share of AI-drafted minus blind-coded repositories, with a repository-bootstrap CI."""
    if "set" not in df or not (df["set"] == "reliability").any():
        return None
    drafted, blind = repo_table(df[df["set"] != "reliability"]), repo_table(df[df["set"] == "reliability"])
    diff = estimate(drafted, shares, "agent_only")["overall"] - estimate(blind, shares, "agent_only")["overall"]
    a = bootstrap(drafted, shares, "agent_only", n_boot, seed).overall
    b = bootstrap(blind, shares, "agent_only", n_boot, seed + 1).overall
    d = a.to_numpy() - b.to_numpy()
    return {"drafted_repos": len(drafted), "blind_repos": len(blind), "difference": diff,
            "lo": float(np.quantile(d, .025)), "hi": float(np.quantile(d, .975))}


def docs_check(df: pd.DataFrame) -> dict | None:
    """Share of agent-only units in the docs/ subsample that docs/ would cover (detector estimate)."""
    if not CONFIG.exists():
        return None
    from gapstudy.detector.gapcheck import units_of
    from gapstudy.detector.items import split_items
    from gapstudy.detector.matchers import make
    from gapstudy.detector.score import score_repo

    config = json.loads(CONFIG.read_text())
    inv = pd.read_csv(PROCESSED / "docs_inventory.csv")
    sub = set(inv[inv.in_docs_subsample & (inv.docs_fetched > 0)].repo)
    units = pd.read_csv(PROCESSED / "units.csv").set_index("unit_id")
    target = df[df.repo.isin(sub) & (df.coverage == "agent_only")]
    if target.empty:
        return {"repos": 0, "agent_only_units": 0, "covered_by_docs": 0, "share": float("nan")}

    rows = []
    for repo, g in target.groupby("repo"):
        folder = PROCESSED / "corpus" / repo.replace("/", "__")
        human = units[(units.repo == repo) & (units.doc != "agent") & ~units.toc].reset_index()
        human["items"] = human.text.map(split_items)
        docs = [u for p in sorted((folder / "docs").rglob("*")) if p.is_file()
                for u in units_of(p, p.relative_to(folder).as_posix())]
        human = pd.concat([human[["unit_id", "text", "items"]], pd.DataFrame(docs)[["unit_id", "text", "items"]]
                           if docs else None], ignore_index=True)
        agent = units.loc[g.unit_id].reset_index()
        agent["items"] = agent.text.map(split_items)
        a_items = agent[["unit_id", "items"]].explode("items").dropna()
        h_items = human[["unit_id", "items"]].explode("items").dropna()
        corpus = list(agent.text) + list(human.text)
        m = make(config["matcher"], corpus=corpus)
        scored = score_repo(agent, human, m.encode(list(agent.text), "query"), m.encode(list(human.text), "doc"),
                            {"vec": m.encode(list(a_items["items"]), "query"), "owner": a_items.unit_id.to_numpy()},
                            {"vec": m.encode(list(h_items["items"]), "doc"), "owner": h_items.unit_id.to_numpy()})
        for s in scored:
            v = config["variant"]
            score = (np.mean([x >= float(v.split("@")[1]) for x in json.loads(s["item_max"])])
                     if v.startswith("item_cov@") else s[v])
            best = json.loads(s["top"])[0][0] if json.loads(s["top"]) else ""
            rows.append({"repo": repo, "unit_id": s["unit_id"], "covered": score >= config["threshold"],
                         "via_docs": best.startswith("docs/")})
    r = pd.DataFrame(rows)
    flips = r.covered & r.via_docs
    return {"repos": r.repo.nunique(), "agent_only_units": len(r), "covered_by_docs": int(flips.sum()),
            "share": float(flips.mean()), "provisional_detector": bool(config.get("provisional"))}
