"""Phase 7: compute RQ1, RQ2, sensitivity and corpus results into one report.

    python -m gapstudy.analysis.report [--boot 1000]

Writes analysis/phase7/results.md (and CSVs of every table next to it). Uses the
frozen coding/labels_v1.csv; before the freeze it runs on the current pass-1
labels and marks every number provisional.
"""

from __future__ import annotations

import argparse
import json

import pandas as pd

from gapstudy.analysis import corpus, rq1, rq2, sensitivity
from gapstudy.analysis.data import PROCESSED, TOOL_NAMES, frame_shares, load
from gapstudy.github_client import PROJECT_ROOT
from gapstudy.labels import CODING

OUT = PROJECT_ROOT / "analysis" / "phase7"


def pct(x: float) -> str:
    return "—" if pd.isna(x) else f"{100 * x:.1f}%"


def ci(row) -> str:
    return pct(row.estimate) + ("" if pd.isna(row.lo) else f" [{pct(row.lo)}, {pct(row.hi)}]")


def headline_md(h: pd.DataFrame) -> list[str]:
    scopes = ["overall", "claude", "agents", "copilot-instructions"]
    names = {"overall": "All (post-stratified)", **TOOL_NAMES}
    labels = {"agent_only": "Agent-only", "partial": "Partially covered", "shared": "Shared",
              "any_gap": "Agent-only or partial", "agent_directed_share": "Agent-directed (share of all units)"}
    present = [s for s in scopes if s in set(h.scope)]
    lines = ["| Outcome (mean share per repo) | " + " | ".join(names[s] for s in present) + " |",
             "|---|" + "---|" * len(present)]
    for outcome, g in h.groupby("outcome", sort=False):
        g = g.set_index("scope")
        lines.append(f"| {labels[outcome]} | " + " | ".join(ci(g.loc[s]) for s in present) + " |")
    repos = h[h.outcome == "agent_only"].set_index("scope").repos
    lines.append("| Repos | " + " | ".join(str(repos[s]) for s in present) + " |")
    return lines


def build(df: pd.DataFrame, provisional: bool, shares: dict, codebook: dict, units: pd.DataFrame,
          n_boot: int, docs: pd.DataFrame | None = None) -> tuple[str, dict[str, pd.DataFrame]]:
    cats = {k: v["name"] for k, v in codebook["categories"].items() if not k.startswith("_")}
    tables: dict[str, pd.DataFrame] = {}
    L = ["# Phase 7 results", ""]
    if provisional:
        L += ["> **Provisional:** computed from unfrozen pass-1 labels; do not report.", ""]

    if df is not None and not df.empty:
        k = df[df.coverage.isin(rq1.KNOWLEDGE)]
        L += [f"Coded units: {len(df)} in {df.repo.nunique()} repos; knowledge units (excluding "
              f"agent-directed): {len(k)}. Overall figures are post-stratified to the eligible frame "
              f"({', '.join(f'{TOOL_NAMES[t]} {s:.1%}' for t, s in shares.items())}). "
              f"95% CIs: {n_boot} bootstrap draws resampling repos within each agent.", ""]

        h = rq1.headline(df, shares, n_boot)
        tables["rq1_headline"] = h
        L += ["## RQ1 — How much agent-file knowledge is absent from README and CONTRIBUTING?", ""]
        L += headline_md(h) + [""]
        u = rq1.unit_level(df)
        L += [f"Pooled over units (cap-weighted): agent-only {pct(u['agent_only'])}, partial "
              f"{pct(u['partial'])}, shared {pct(u['shared'])}.", ""]

        bc = rq1.by_category(df, cats)
        tables["rq1_by_category"] = bc
        L += ["### By instruction category", "", "| Category | Units | Repos | Agent-only | Agent-only or partial |",
              "|---|---|---|---|---|"]
        L += [f"| {r.category} | {r.units} | {r.repos} | {pct(r.agent_only)} | {pct(r.any_gap)} |" for r in bc.itertuples()]
        L.append("")

        try:
            g = rq1.gee(df, list(cats))
            tables["rq1_gee"] = g
            names = {f"cat:{k}": v for k, v in cats.items()} | {f"agent:{t}": f"{TOOL_NAMES[t]} (vs CLAUDE.md)" for t in TOOL_NAMES}
            L += ["### Logistic GEE: agent-only ~ categories + agent (clustered by repo)", "",
                  f"n = {g.attrs['n_units']} units in {g.attrs['n_repos']} repos; exchangeable working "
                  f"correlation; robust SEs. Dropped (too rare or no variation): "
                  f"{', '.join(cats[d] for d in g.attrs['dropped']) or 'none'}.", "",
                  "| Term | Odds ratio [95% CI] | p |", "|---|---|---|"]
            L += [f"| {names.get(i, i)} | {r.odds_ratio:.2f} [{r.lo:.2f}, {r.hi:.2f}] | {r.p:.3g} |" for i, r in g.iterrows()]
            L.append("")
        except Exception as exc:  # small or degenerate samples
            L += [f"GEE not estimable on the current labels: {exc}", ""]

        chi = rq1.chi_square_descriptive(df)
        L += [f"Descriptive χ² (agent × coverage, units; ignores clustering): χ²({chi['dof']}) = "
              f"{chi['chi2']:.1f}, p = {chi['p']:.3g}.", ""]

        L += ["## RQ2 — Which newcomer needs and barriers does this knowledge address?", "",
              "Units coded agent-only or partially covered.", ""]
        n = rq2.needs(df, codebook)
        tables["rq2_needs"] = n
        if not n.empty:
            L += ["### Newcomer need (Dagenais et al. landscape features)", "",
                  "| Group | Need | Units | Repos | Share |", "|---|---|---|---|---|"]
            L += [f"| {r.group} | {r.need} | {r.units} | {r.repos} | {pct(r.share)} |" for r in n.itertuples()]
            L += ["", "By group: " + "; ".join(f"{g} {pct(r.share)}" for g, r in rq2.need_groups(n).iterrows()), ""]
        b = rq2.barriers(df, codebook)
        tables["rq2_barriers"] = b
        L += ["### Barriers mitigated (Steinmacher et al.; multi-label)", "",
              "| Group | Barrier | Units | Repos | Share of gap units |", "|---|---|---|---|---|"]
        L += [f"| {r.group} | {r.barrier} | {r.units} | {r.repos} | {pct(r.share_of_gap_units)} |" for r in b.itertuples()]
        L.append("")
        ex = rq2.examples(df, units, codebook)
        if ex:
            L += ["### Example agent-only knowledge (seeded sample, ≤ 60 words)", ""]
            for e in ex:
                L += [f"- **{e['need']}** — {e['repo']} ({TOOL_NAMES[e['tool']]}), *{e['heading'] or 'no heading'}*:",
                      "  > " + e["text"].replace("\n", " ")[:400]]
            L.append("")

        flags = df["flags"].explode().value_counts()
        L += ["## Sensitivity", "", "| Variant | Repos | Agent-only (post-stratified) |", "|---|---|---|"]
        s = sensitivity.table(df, shares)
        tables["sensitivity"] = s
        L += [f"| {r.variant} | {r.repos} | {pct(r.agent_only)} |" for r in s.itertuples()]
        d = sensitivity.docs_check(df)
        L += [""]
        if d:
            L += [f"docs/ check (detector estimate, {d['repos']} repos): {d['covered_by_docs']} of "
                  f"{d['agent_only_units']} agent-only units ({pct(d['share'])}) match a docs/ section."
                  + (" Detector thresholds are provisional." if d.get("provisional_detector") else ""), ""]
        else:
            L += ["docs/ check: needs the tuned detector (detector/config.json from gapstudy.detector.evaluate).", ""]
        L += [f"Flags: conflict (human docs contradict the agent file) on {int(flags.get('conflict', 0))} units; "
              f"links_out on {int(flags.get('links_out', 0))}.", ""]
    else:
        L += ["No labels yet: RQ1, RQ2 and the sensitivity checks run once coding has started.", ""]

    if docs is not None:
        tables["corpus_documents"] = docs
        L += ["## Corpus: length and readability (all 201 repos, no labels needed)", "",
              "Flesch Reading Ease (textstat) on prose with code removed; higher = easier. "
              "Documents with < 30 prose words are skipped.", "",
              corpus.summary(docs).rename(columns={"words": "median words", "flesch": "median Flesch"}).to_markdown(), "",
              "Within-repo comparisons (Wilcoxon signed-rank):", "",
              corpus.paired_tests(docs).round(3).assign(p=lambda t: t.p.map(
                  lambda p: "< 0.0001" if p < 1e-4 else f"{p:.3g}")).to_markdown(index=False), "",
              "Agent-file Flesch median by agent: " + ", ".join(
                  f"{TOOL_NAMES[t]} {v:.1f}" for t, v in docs[docs.doc == "agent"].groupby("tool").flesch.median().items()), ""]
    return "\n".join(L), tables


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=1000)
    args = ap.parse_args()
    df, provisional = load()
    codebook = json.loads((CODING / "codebook.json").read_text())
    units = pd.read_csv(PROCESSED / "units.csv")
    text, tables = build(df, provisional, frame_shares(), codebook, units, args.boot, corpus.documents())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.md").write_text(text + "\n")
    for name, t in tables.items():
        t.to_csv(OUT / f"{name}.csv", index=name in ("rq1_gee",))
    print(text)


if __name__ == "__main__":
    main()
