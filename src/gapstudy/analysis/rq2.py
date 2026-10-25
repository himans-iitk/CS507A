"""RQ2: which newcomer needs and barriers does agent-only knowledge address?

Uses the units coded agent-only or partially covered: D1 (Dagenais et al.'s
landscape feature) and D2 (Steinmacher et al.'s barriers, multi-label). Shares are
weighted for the per-repo cap; examples are drawn with a fixed seed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GAP = ["agent_only", "partial"]


def needs(df: pd.DataFrame, codebook: dict) -> pd.DataFrame:
    g = df[df.coverage.isin(GAP) & df.need.notna()]
    w = g.weight.fillna(1)
    rows = []
    for key, spec in codebook["needs"].items():
        if key.startswith("_"):
            continue
        hit = g.need == key
        if hit.any():
            rows.append({"group": spec["group"], "need": spec["name"], "units": int(hit.sum()),
                         "repos": g[hit].repo.nunique(), "share": float(w[hit].sum() / w.sum()),
                         "agent_only_units": int((hit & (g.coverage == "agent_only")).sum())})
    return pd.DataFrame(rows).sort_values("share", ascending=False)


def need_groups(table: pd.DataFrame) -> pd.DataFrame:
    return table.groupby("group")[["units", "share"]].sum().sort_values("share", ascending=False)


def barriers(df: pd.DataFrame, codebook: dict) -> pd.DataFrame:
    g = df[df.coverage.isin(GAP)]
    w = g.weight.fillna(1)
    rows = []
    for key, spec in codebook["barriers"].items():
        if key.startswith("_"):
            continue
        hit = g.barriers.map(lambda b: key in (b or []))
        if hit.any():
            rows.append({"group": spec["group"], "barrier": spec["name"], "units": int(hit.sum()),
                         "repos": g[hit].repo.nunique(), "share_of_gap_units": float(w[hit].sum() / w.sum())})
    none = g.barriers.map(lambda b: not b)
    rows.append({"group": "—", "barrier": "(no barrier coded)", "units": int(none.sum()),
                 "repos": g[none].repo.nunique(), "share_of_gap_units": float(w[none].sum() / w.sum()) if len(g) else np.nan})
    return pd.DataFrame(rows).sort_values("share_of_gap_units", ascending=False)


def needs_by_agent(df: pd.DataFrame, codebook: dict) -> pd.DataFrame:
    g = df[df.coverage.isin(GAP) & df.need.notna()]
    names = {k: v["name"] for k, v in codebook["needs"].items() if not k.startswith("_")}
    return pd.crosstab(g.need.map(names), g.tool, normalize="columns").round(3)


def examples(df: pd.DataFrame, units: pd.DataFrame, codebook: dict, top: int = 5, per: int = 2,
             max_words: int = 60, seed: int = 507) -> list[dict]:
    """Short agent-only excerpts for the most frequent needs (seeded, for the paper)."""
    g = df[(df.coverage == "agent_only") & df.need.notna()].merge(units[["unit_id", "heading_path", "text"]], on="unit_id")
    g = g[g.text.str.split().str.len() <= max_words]
    out = []
    for need in g.need.value_counts().index[:top]:
        sample = g[g.need == need].sample(min(per, (g.need == need).sum()), random_state=seed)
        for r in sample.itertuples():
            out.append({"need": codebook["needs"][need]["name"], "repo": r.repo, "tool": r.tool,
                        "heading": r.heading_path if isinstance(r.heading_path, str) else "", "text": r.text})
    return out
