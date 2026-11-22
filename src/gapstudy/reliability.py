"""Phase 5: reliability from the blind second coding of the reliability set.

    python -m gapstudy.reliability [--boot 1000]

Compares pass 1 and pass 2 on units coded in both passes and writes
analysis/phase5/reliability.md and reliability.json (status and point estimates, read
by the pipeline and the paper). Agreement is inter-rater when the passes were coded by
different people and intra-rater when one person re-coded; with no pass-2 labels the
status is "pending" and the single-annotator results stand alone. Measures:
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
from gapstudy.labels import CODING, LabelStore, aliases, annotator_type, annotators

OUT = PROJECT_ROOT / "analysis" / "phase5" / "reliability.md"
OUT_JSON = OUT.with_suffix(".json")
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


def coders(store: LabelStore, unit_ids: set[str], coding_dir: Path = CODING) -> tuple[set, set]:
    alias = aliases(coding_dir)
    pick = lambda p: {alias.get(r.get("coder"), r.get("coder")) for u, r in store.latest(p).items() if u in unit_ids}
    return pick(1), pick(2)


def agreement_kind(c1: set, c2: set, coding_dir: Path = CODING) -> str:
    """intra-rater (same person twice), human-llm (an LLM coded one pass) or inter-rater (two people)."""
    if c1 == c2:
        return "intra-rater"
    types = {annotator_type(c, coding_dir) for c in c1 | c2}
    return "human-llm" if "llm" in types else "inter-rater"


def by_repo(p: pd.DataFrame, queue: pd.DataFrame) -> pd.DataFrame:
    tools = queue.drop_duplicates("unit_id").set_index("unit_id").tool
    d = p.assign(agree=p.coverage_1 == p.coverage_2, tool=p.unit_id.map(tools))
    return d.groupby("repo").agg(tool=("tool", "first"), units=("agree", "size"), agreement=("agree", "mean"))


def report(coding_dir: Path, n_boot: int) -> tuple[str, dict]:
    codebook = json.loads((coding_dir / "codebook.json").read_text())
    keys = [k for k in codebook["categories"] if not k.startswith("_")]
    queue = pd.read_csv(coding_dir / "queue.csv")
    store = LabelStore(coding_dir)
    p = paired(store, queue[queue.set == "reliability"])
    total = int((queue.set == "reliability").sum())
    if p.empty:
        status = {"status": "pending", "units": 0, "total": total}
        text = ("# Reliability (pass 1 vs blind pass 2)\n\n"
                f"No second-coder labels yet (0 / {total} units). Results use a single annotator.\n")
        return text, status
    c1, c2 = coders(store, set(p.unit_id), coding_dir)
    kind = agreement_kind(c1, c2, coding_dir)
    title = {"intra-rater": "Intra-rater", "inter-rater": "Inter-rater", "human-llm": "Human–LLM"}[kind]
    lines = [f"# {title} agreement (pass 1 vs blind pass 2)", ""]

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
              ("| D1 newcomer need, κ | n/a (pass 1 coded no needs on this set) |" if pd.isna(point["need_kappa"])
               else f"| D1 newcomer need, κ | {point['need_kappa']:.2f}{ci('need_kappa')} |"), "",
              "## Coverage confusion (rows: pass 1, columns: pass 2)", "",
              pd.crosstab(p.coverage_1, p.coverage_2).to_markdown(), "",
              "## Per-category κ", "", "| Category | κ | units (pass 1) |", "|---|---|---|"]
    for k in keys:
        support = p.categories_1.map(lambda c: k in (c or [])).sum()
        lines.append(f"| {codebook['categories'][k]['name']} | {point['cat:' + k]:.2f} | {support} |")
    tools = queue.drop_duplicates("unit_id").set_index("unit_id").tool
    agent_rows = []
    for t, g in p.assign(tool=p.unit_id.map(tools)).groupby("tool"):
        agent_rows.append(f"| {t} | {len(g)} | {(g.coverage_1 == g.coverage_2).mean():.1%} | "
                          f"{kappa(g.coverage_1, g.coverage_2):.2f} |")
    repo = by_repo(p, queue)
    lines += ["", "## By agent", "", "| Agent | Units | Agreement | κ |", "|---|---|---|---|", *agent_rows,
              "", "## By repository", "",
              f"Agreement per repository: median {repo.agreement.median():.0%}, mean {repo.agreement.mean():.0%}; "
              f"{(repo.agreement == 1).sum()} of {len(repo)} repositories agree on every unit, "
              f"{(repo.agreement >= .8).sum()} on at least 80%, {(repo.agreement < .6).sum()} below 60%.", "",
              "Lowest agreement:", "", repo.sort_values("agreement").head(5).round(2).to_markdown()]
    lines += ["", "Interpretation (Landis & Koch): 0.61–0.80 substantial, > 0.80 almost perfect. "
              f"Pass 1 coder(s): {', '.join(sorted(map(str, c1)))}; pass 2 coder(s): "
              f"{', '.join(sorted(map(str, c2)))}, so this is {kind} agreement."]
    by_repo(p, queue).to_csv(OUT.parent / "reliability_by_repo.csv")
    info = annotators(coding_dir)
    second = sorted(map(str, c2))
    status = {"status": "complete" if len(p) == total else "partial", "kind": kind, "units": int(len(p)),
              "second_coders": second,
              "second_coder_types": sorted({annotator_type(c, coding_dir) for c in second}),
              "second_coder_models": sorted({info.get(c, {}).get("model") for c in second} - {None}),
              "repo_agreement_median": round(float(repo.agreement.median()), 4),
              "repos_full_agreement": int((repo.agreement == 1).sum()),
              "total": total, "repos": int(p.repo.nunique()),
              **{k: (None if pd.isna(point[k]) else round(float(point[k]), 4))
                 for k in ("coverage_agreement", "coverage_kappa", "coverage_weighted_kappa", "category_jaccard",
                           "need_kappa")}}
    if n_boot:
        for k in ("coverage_kappa", "coverage_weighted_kappa"):
            status[f"{k}_ci"] = [round(float(boot[k].quantile(.025)), 4), round(float(boot[k].quantile(.975)), 4)]
    return "\n".join(lines) + "\n", status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=1000)
    args = ap.parse_args()
    text, status = report(CODING, args.boot)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    OUT_JSON.write_text(json.dumps(status, indent=2) + "\n")
    print(text)


if __name__ == "__main__":
    main()
