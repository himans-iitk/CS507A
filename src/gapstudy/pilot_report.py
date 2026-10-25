"""Phase 4: summarise pilot coding to drive the codebook v1.0 revision.

    python -m gapstudy.pilot_report [--set pilot]

Writes analysis/phase4/pilot_report.md: progress, label distributions, every
note and flagged unit (the hard cases), consistency problems to fix, LLM
pre-label agreement (if pre-labels exist), and projected coding time.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from gapstudy.github_client import PROJECT_ROOT
from gapstudy.labels import CODING, LabelStore

PROCESSED = PROJECT_ROOT / "data" / "processed"
OUT = PROJECT_ROOT / "analysis" / "phase4" / "pilot_report.md"


def problems(row: pd.Series) -> list[str]:
    """Internal inconsistencies of one label record."""
    out = []
    evidence = row.evidence or []
    if row.coverage in ("partial", "shared") and not evidence:
        out.append("partial/shared without evidence")
    if row.coverage == "agent_only" and evidence:
        out.append("agent-only but evidence ticked")
    if row.coverage in ("agent_only", "partial") and not row.need:
        out.append("no newcomer need (D1)")
    if not (row.categories or []) and row.coverage != "agent_directed":
        out.append("no category")
    return out


def table(s: pd.Series | pd.DataFrame) -> str:
    return s.to_markdown() if hasattr(s, "to_markdown") else str(s)


def prelabel_agreement(labels: pd.DataFrame, prelabels: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Per-category precision/recall of LLM suggestions against your final categories."""
    merged = labels.merge(prelabels, on="unit_id", suffixes=("", "_llm"))
    rows = []
    for k in keys:
        human = merged.categories.map(lambda c: k in (c or []))
        llm = merged.categories_llm.map(lambda c: k in json.loads(c))
        tp, fp, fn = (human & llm).sum(), (~human & llm).sum(), (human & ~llm).sum()
        if tp + fp + fn:
            rows.append({"category": k, "support": int(human.sum()),
                         "precision": tp / (tp + fp) if tp + fp else float("nan"),
                         "recall": tp / (tp + fn) if tp + fn else float("nan")})
    return pd.DataFrame(rows).set_index("category").round(2) if rows else pd.DataFrame()


def build(coding_dir: Path, processed_dir: Path, which: str) -> str:
    codebook = json.loads((coding_dir / "codebook.json").read_text())
    queue = pd.read_csv(coding_dir / "queue.csv")
    units = pd.read_csv(processed_dir / "units.csv").set_index("unit_id")
    target = queue[queue.set == which]
    labels = LabelStore(coding_dir).to_frame(1)
    if labels.empty:
        return f"# Pilot report ({which} set)\n\nNo labels yet: 0 / {len(target)} units coded.\n"
    labels = labels[labels.unit_id.isin(target.unit_id)].merge(target[["unit_id", "repo", "tool"]], on="unit_id")
    cov_names = {k: v["name"] for k, v in codebook["coverage"].items()}
    lines = [f"# Pilot report ({which} set, codebook {codebook['version']})", ""]

    done, total = len(labels), len(target)
    repos_done = labels.groupby("repo").size().reindex(target.repo.unique()).fillna(0)
    full = (repos_done == target.groupby("repo").size().reindex(repos_done.index)).sum()
    lines += [f"**Progress:** {done} / {total} units ({100 * done / total:.0f}%), {full} / {len(repos_done)} repos complete.",
              f"Labels by codebook version: {labels.codebook_version.value_counts().to_dict()}", ""]

    secs = labels.seconds.dropna()
    secs = secs[(secs > 0) & (secs < 1800)]  # ignore idle time
    if len(secs):
        remaining = len(queue) - len(LabelStore(coding_dir).latest(1))
        lines += [f"**Pace:** median {secs.median():.0f} s/unit (mean {secs.mean():.0f} s). "
                  f"Remaining {remaining} units ≈ {remaining * secs.mean() / 3600:.1f} h at the mean pace.", ""]

    cov = labels.coverage.map(cov_names)
    lines += ["## Coverage", "", table(pd.crosstab(cov, labels.tool, margins=True, margins_name="total")), ""]
    knowledge = labels[labels.coverage != "agent_directed"]
    if len(knowledge):
        rate = (knowledge.coverage == "agent_only").mean()
        lines += [f"Unweighted agent-only share among knowledge units (excl. agent-directed): **{rate:.0%}** "
                  f"(n = {len(knowledge)}; pilot only, not an estimate).", ""]

    cats = labels.categories.explode().dropna().map(lambda k: codebook["categories"][k]["name"])
    lines += ["## Categories", "", table(cats.value_counts().rename("units")), ""]
    if labels.need.notna().any():
        needs = labels.need.dropna().map(lambda k: codebook["needs"][k]["name"])
        lines += ["## D1 newcomer need (agent-only + partial)", "", table(needs.value_counts().rename("units")), ""]

    flags = labels["flags"].explode().dropna()
    lines += ["## Flags", "", table(flags.value_counts().rename("units")) if len(flags) else "None.", ""]

    labels["problems"] = labels.apply(problems, axis=1)
    bad = labels[labels.problems.str.len() > 0]
    lines += ["## Consistency problems to fix", ""]
    lines += [f"- `{r.unit_id}`: {', '.join(r.problems)}" for r in bad.itertuples()] or ["None."]
    lines.append("")

    lines += ["## Hard cases (notes and flagged units) — input for codebook v1.0", ""]
    hard = labels[(labels.notes.fillna("") != "") | labels["flags"].map(lambda f: bool(f))]
    for cov_key, group in hard.groupby("coverage"):
        lines += [f"### {cov_names[cov_key]}", ""]
        for r in group.itertuples():
            u = units.loc[r.unit_id]
            head = u.heading_path if isinstance(u.heading_path, str) and u.heading_path else "(no heading)"
            flag_txt = f" [{', '.join(r.flags)}]" if r.flags else ""
            lines.append(f"- **{r.repo}** · {head}{flag_txt}: {r.notes or '(no note)'}")
        lines.append("")
    if hard.empty:
        lines += ["No notes or flags yet.", ""]

    pre_path = coding_dir / "prelabels.csv"
    if pre_path.exists():
        keys = [k for k in codebook["categories"] if not k.startswith("_")]
        agree = prelabel_agreement(labels, pd.read_csv(pre_path), keys)
        if not agree.empty:
            lines += ["## LLM pre-label agreement with your categories", "", table(agree), ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="pilot", choices=["pilot", "reliability", "main"])
    args = ap.parse_args()
    report = build(CODING, PROCESSED, args.set)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(report)
    print(report)


if __name__ == "__main__":
    main()
