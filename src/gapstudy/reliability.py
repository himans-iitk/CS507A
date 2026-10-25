"""Phase 5: intra-rater reliability from the blind re-code of the reliability set.

    python -m gapstudy.reliability [--boot 1000]

Compares pass 1 and pass 2 on units coded in both passes and writes
analysis/phase5/reliability.md:
  - coverage: Cohen's kappa over all four labels, and linearly weighted kappa on the
    ordinal agent-only < partial < shared scale (units neither pass called agent-directed);
  - categories: per-category kappa (present/absent) and mean Jaccard per unit;
  - D1 newcomer need: kappa where both passes gave one.
95% CIs come from a bootstrap that resamples repos, since units are nested in repos.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from gapstudy.github_client import PROJECT_ROOT
from gapstudy.labels import CODING, LabelStore

OUT = PROJECT_ROOT / "analysis" / "phase5" / "reliability.md"
ORDINAL = {"agent_only": 0, "partial": 1, "shared": 2}


def paired(store: LabelStore, queue: pd.DataFrame) -> pd.DataFrame:
    a, b = store.to_frame(1), store.to_frame(2)
    if a.empty or b.empty:
        return pd.DataFrame()
    cols = ["unit_id", "coverage", "categories", "need"]
    pairs = a[cols].merge(b[cols], on="unit_id", suffixes=("_1", "_2"))
    return pairs.merge(queue[["unit_id", "repo"]], on="unit_id")


def kappa(x: pd.Series, y: pd.Series, weights: str | None = None) -> float:
    if len(x) == 0:
        return float("nan")
    if x.nunique() == 1 and y.nunique() == 1:
        return 1.0 if (x.values == y.values).all() else 0.0
    return cohen_kappa_score(x, y, weights=weights)


def metrics(p: pd.DataFrame, category_keys: list[str]) -> dict[str, float]:
    out = {"coverage_agreement": (p.coverage_1 == p.coverage_2).mean(),
           "coverage_kappa": kappa(p.coverage_1, p.coverage_2)}
    ordinal = p[p.coverage_1.isin(ORDINAL) & p.coverage_2.isin(ORDINAL)]
    out["coverage_weighted_kappa"] = kappa(ordinal.coverage_1.map(ORDINAL), ordinal.coverage_2.map(ORDINAL), "linear")
    sets1, sets2 = p.categories_1.map(lambda c: set(c or [])), p.categories_2.map(lambda c: set(c or []))
    out["category_jaccard"] = np.mean([len(s & t) / len(s | t) if s | t else 1.0 for s, t in zip(sets1, sets2)])
    for k in category_keys:
        out[f"cat:{k}"] = kappa(sets1.map(lambda s: k in s), sets2.map(lambda s: k in s))
    needs = p.dropna(subset=["need_1", "need_2"])
    out["need_kappa"] = kappa(needs.need_1, needs.need_2)
    return out


def bootstrap(p: pd.DataFrame, category_keys: list[str], n: int, seed: int = 507) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    repos = p.repo.unique()
    groups = {r: g for r, g in p.groupby("repo")}
    draws = []
    for _ in range(n):
        sample = pd.concat([groups[r] for r in rng.choice(repos, len(repos))], ignore_index=True)
        draws.append(metrics(sample, category_keys))
    return pd.DataFrame(draws)


def report(coding_dir: Path, n_boot: int) -> str:
    codebook = json.loads((coding_dir / "codebook.json").read_text())
    keys = [k for k in codebook["categories"] if not k.startswith("_")]
    queue = pd.read_csv(coding_dir / "queue.csv")
    p = paired(LabelStore(coding_dir), queue[queue.set == "reliability"])
    total = (queue.set == "reliability").sum()
    lines = ["# Intra-rater reliability (pass 1 vs blind pass 2)", ""]
    if p.empty:
        return "\n".join(lines + [f"No units re-coded yet (0 / {total})."]) + "\n"

    point = metrics(p, keys)
    boot = bootstrap(p, keys, n_boot) if n_boot else pd.DataFrame(columns=point)
    ci = lambda k: (f" [{boot[k].quantile(.025):.2f}, {boot[k].quantile(.975):.2f}]"
                    if n_boot and boot[k].notna().any() else "")
    lines += [f"Units re-coded: **{len(p)} / {total}** in {p.repo.nunique()} repos. "
              f"95% CIs: repo bootstrap, {n_boot} draws.", "",
              "| Measure | Value |", "|---|---|",
              f"| Coverage, % agreement | {point['coverage_agreement']:.1%} |",
              f"| Coverage, Cohen's κ (4 labels) | {point['coverage_kappa']:.2f}{ci('coverage_kappa')} |",
              f"| Coverage, linearly weighted κ (agent-only < partial < shared) | {point['coverage_weighted_kappa']:.2f}{ci('coverage_weighted_kappa')} |",
              f"| Categories, mean Jaccard per unit | {point['category_jaccard']:.2f}{ci('category_jaccard')} |",
              f"| D1 newcomer need, κ | {point['need_kappa']:.2f}{ci('need_kappa')} |", "",
              "## Coverage confusion (rows: pass 1, columns: pass 2)", "",
              pd.crosstab(p.coverage_1, p.coverage_2).to_markdown(), "",
              "## Per-category κ", "", "| Category | κ | units (pass 1) |", "|---|---|---|"]
    for k in keys:
        support = p.categories_1.map(lambda c: k in (c or [])).sum()
        lines.append(f"| {codebook['categories'][k]['name']} | {point['cat:' + k]:.2f} | {support} |")
    lines += ["", "Interpretation (Landis & Koch): 0.61–0.80 substantial, > 0.80 almost perfect. "
              "This is intra-rater agreement; report it as such."]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=1000)
    args = ap.parse_args()
    text = report(CODING, args.boot)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
