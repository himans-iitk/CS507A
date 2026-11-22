"""Key findings, read from the pipeline outputs, for the final-results file and the paper.

`facts()` is the single place that turns result tables into headline findings, so
analysis/FINAL_RESULTS.md and the sentences in the paper always agree.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from gapstudy.github_client import PROJECT_ROOT

ANALYSIS = PROJECT_ROOT / "analysis"
P7, P6, P5 = ANALYSIS / "phase7", ANALYSIS / "phase6", ANALYSIS / "phase5"
TOOLS = {"claude": "CLAUDE.md", "agents": "AGENTS.md", "copilot-instructions": "copilot-instructions.md"}
MIN_UNITS = 20  # categories rarer than this are listed but not named as extremes


def _codebook() -> dict:
    return json.loads((PROJECT_ROOT / "coding" / "codebook.json").read_text())


def facts() -> dict:
    f: dict = {}
    h = pd.read_csv(P7 / "rq1_headline.csv")
    f["headline"] = {(r.outcome, r.scope): (r.estimate, r.lo, r.hi, r.repos) for r in h.itertuples()}

    cat = pd.read_csv(P7 / "rq1_by_category.csv").sort_values("agent_only", ascending=False)
    common = cat[cat.units >= MIN_UNITS]
    f["categories"] = cat
    f["cat_highest"] = common.head(3).to_dict("records")
    f["cat_lowest"] = common.tail(1).to_dict("records")[0]

    names = {f"cat:{k}": v["name"] for k, v in _codebook()["categories"].items() if not k.startswith("_")}
    names |= {f"agent:{t}": f"{n} (vs CLAUDE.md)" for t, n in TOOLS.items()}
    g = pd.read_csv(P7 / "rq1_gee.csv", index_col=0)
    g["term"] = g.index.map(lambda i: names.get(i, i))
    f["gee"] = g
    f["gee_sig_cats"] = g[(g.p < 0.05) & g.index.str.startswith("cat:")].sort_values("odds_ratio")
    f["gee_agent_min_p"] = float(g[g.index.str.startswith("agent:")].p.min())

    needs = pd.read_csv(P7 / "rq2_needs.csv")
    f["needs"] = needs
    f["need_groups"] = needs.groupby("group").share.sum().sort_values(ascending=False)
    f["needs_top"] = needs.sort_values("share", ascending=False).head(3).to_dict("records")
    bars = pd.read_csv(P7 / "rq2_barriers.csv")
    f["barriers"] = bars
    f["barriers_top"] = bars[bars.group != "—"].head(3).to_dict("records")
    none = bars[bars.group == "—"]
    f["no_barrier_share"] = float(none.share_of_gap_units.iloc[0]) if len(none) else 0.0

    if (P7 / "rq1_repo_shares.csv").exists():
        per = pd.read_csv(P7 / "rq1_repo_shares.csv", index_col=0)
        f["repo_shares"] = per
        f["repo_spread"] = pd.read_csv(P7 / "rq1_repo_spread.csv", index_col=0)
        f["repo_facts"] = {"repos": len(per), "any_agent_only": int((per.agent_only > 0).sum()),
                           "all_agent_only": int((per.agent_only == 1).sum()), "no_shared": int((per.shared == 0).sum()),
                           "median_by_tool": per.groupby("tool").agent_only.median().to_dict()}
    if (P7 / "provenance_need_source.csv").exists():
        f["need_source"] = pd.read_csv(P7 / "provenance_need_source.csv", index_col=0).units.to_dict()
    if (P5 / "reliability_by_repo.csv").exists():
        f["rel_by_repo"] = pd.read_csv(P5 / "reliability_by_repo.csv", index_col=0)

    s = pd.read_csv(P7 / "sensitivity.csv")
    f["sensitivity"] = s
    scope = s[~s.variant.str.startswith("only ")]  # scope variants; the "only ..." rows split by coding mode
    f["sens_range"] = (float(scope.agent_only.min()), float(scope.agent_only.max()))
    mode = s[s.variant.str.startswith("only ")].set_index("variant")
    f["sens_mode"] = {("blind" if "blind" in v else "drafted"): r.to_dict() for v, r in mode.iterrows()}
    cm = P7 / "sensitivity_coding_mode.csv"
    f["coding_mode"] = pd.read_csv(cm).iloc[0].to_dict() if cm.exists() else None

    det = pd.read_csv(P6 / "detector_results.csv")
    matchers = det[det.variant.notna()] if "variant" in det else det
    f["detector"] = matchers.sort_values("dev_f1", ascending=False)
    f["detector_best"] = f["detector"].iloc[0].to_dict()
    f["detector_llm"] = det[det.variant.isna()] if "variant" in det else det.iloc[0:0]

    errors = (P6 / "errors.md").read_text() if (P6 / "errors.md").exists() else ""
    grab = lambda pat: int(m.group(1)) if (m := re.search(pat, errors)) else None  # noqa: E731
    f["errors_false_agent_only"] = grab(r"False agent-only[^:]*: (\d+)")
    f["errors_missed_agent_only"] = grab(r"Missed agent-only[^:]*: (\d+)")
    dc = P7 / "docs_check.csv"
    f["docs_check"] = pd.read_csv(dc).iloc[0].to_dict() if dc.exists() else None

    rel = P5 / "reliability.json"
    f["reliability"] = json.loads(rel.read_text()) if rel.exists() else {"status": "pending"}

    ex = P7 / "rq2_examples.csv"
    f["examples"] = pd.read_csv(ex) if ex.exists() else pd.DataFrame()
    docs = pd.read_csv(P7 / "corpus_documents.csv")
    f["docs"] = docs
    f["flesch"] = docs.groupby("doc").flesch.median().to_dict()

    if (P7 / "provenance_by_set.csv").exists():
        f["provenance"] = pd.read_csv(P7 / "provenance_by_set.csv", index_col=0)
        f["provenance_by_draft"] = pd.read_csv(P7 / "provenance_by_draft.csv", index_col=0)
    labels = pd.read_csv(PROJECT_ROOT / "coding" / "labels_v1.csv")
    f["n_units"], f["n_repos"] = len(labels), labels.repo.nunique()
    f["flags"] = labels["flags"].map(json.loads).explode().value_counts().to_dict()
    return f


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def ci(t) -> str:
    return f"{pct(t[0])} [{pct(t[1])}, {pct(t[2])}]"


def gee_sentence(f: dict) -> str:
    sig = ", ".join(f"{r.term} (OR {r.odds_ratio:.2f})" for r in f["gee_sig_cats"].itertuples()) or "no category"
    agents = (f"the agents do not differ (smallest p = {f['gee_agent_min_p']:.2f})" if f["gee_agent_min_p"] >= 0.05
              else "at least one agent differs from CLAUDE.md (p < 0.05)")
    return f"- Clustered logistic model (GEE, vs. other categories): {sig} differ significantly (p < 0.05); {agents}."


def repo_sentence(f: dict) -> str:
    if "repo_facts" not in f:
        return ""
    rf, sp = f["repo_facts"], f["repo_spread"]
    return (f"- Per repository (unweighted): median agent-only share {pct(sp.loc['agent_only', 'median'])} "
            f"(middle half {pct(sp.loc['agent_only', 'q1'])}–{pct(sp.loc['agent_only', 'q3'])}); "
            f"{rf['any_agent_only']} of {rf['repos']} repositories have at least one agent-only unit, "
            f"{rf['all_agent_only']} only agent-only units, and {rf['no_shared']} share no unit fully with their "
            "human docs (`analysis/phase7/rq1_repo_shares.csv`).")


def coding_mode_sentence(f: dict) -> str:
    cm, sm = f.get("coding_mode"), f.get("sens_mode", {})
    if not cm or "blind" not in sm:
        return "- Coding mode: no blind-coded set to compare with."
    b = sm["blind"]
    sig = "not significant" if cm["lo"] <= 0 <= cm["hi"] else "significant"
    return (f"- Coding mode: blind-coded repositories (reliability set, {int(cm['blind_repos'])}) have agent-only "
            f"{pct(b['agent_only'])} [{pct(b['lo'])}, {pct(b['hi'])}]; AI-drafted repositories are "
            f"{100 * cm['difference']:+.1f} pp higher [{100 * cm['lo']:+.1f}, {100 * cm['hi']:+.1f}] ({sig} at 95%).")


def render(mode: str, f: dict | None = None) -> str:
    f = f or facts()
    hl = f["headline"]
    rel = f["reliability"]
    best = f["detector_best"]
    L = ["# Final results", "",
         f"Generated by `python -m gapstudy.pipeline` on {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC. "
         f"Annotation mode: **{mode}**. Every number below is read from the pipeline outputs; "
         "the detailed tables are linked at the end.", ""]
    if rel["status"] == "pending":
        L += ["> **Single-annotator results.** No second-coder labels exist yet, so the reliability of the "
              "coverage labels is not measured. Rerun the pipeline once the second round is in; agreement "
              "is then computed and the paper switches to its two-annotator text.", ""]

    L += ["## Dataset", "",
          f"- {f['n_units']:,} coded agent-file units in {f['n_repos']} repositories "
          "(pilot, reliability and main sets; frozen in `coding/labels_v1.csv`)."]
    if "provenance" in f:
        p = f["provenance"].sum()
        reviewed = int(p.drop("blind", errors="ignore").sum())
        L += [f"- {reviewed:,} labels started from an AI draft that the annotator reviewed "
              f"({int(p.get('draft_corrected', 0))} coverage corrections); {int(p.get('blind', 0))} were coded blind, "
              "without any draft."]
    if "need_source" in f:
        L += ["- Newcomer need (D1/D2) of gap units: " + "; ".join(f"{k} {v}" for k, v in f["need_source"].items()) + "."]
    if rel["status"] == "pending":
        L += ["- Reliability: pending (second coder)."]
    else:
        who = {"human-llm": f"first annotator vs. an independent LLM annotator ({', '.join(rel.get('second_coder_models', []))})",
               "inter-rater": "two human annotators", "intra-rater": "one annotator re-coding"}[rel["kind"]]
        lo, hi = rel.get("coverage_kappa_ci", [float("nan")] * 2)
        L += [f"- Agreement on the blind reliability set ({who}; {rel['units']} units, {rel['repos']} repos): "
              f"Cohen's κ = **{rel['coverage_kappa']:.2f}** [{lo:.2f}, {hi:.2f}], weighted κ = "
              f"{rel['coverage_weighted_kappa']:.2f}, same label on {pct(rel['coverage_agreement'])} of units; "
              f"per repository median {pct(rel['repo_agreement_median'])}, {rel['repos_full_agreement']} repos in full agreement."]
        if rel["kind"] == "human-llm":
            L += ["- Note: the second annotator is an LLM, so this is human–LLM agreement, not agreement between "
                  "two human coders."]

    L += ["", "## RQ1 — How much agent-file knowledge is absent from README and CONTRIBUTING?", "",
          "Mean share per repository, post-stratified to the eligible population; 95% repository-bootstrap CIs.", "",
          "| | All | CLAUDE.md | AGENTS.md | copilot-instructions.md |", "|---|---|---|---|---|"]
    for outcome, label in (("agent_only", "Agent-only"), ("partial", "Partially covered"), ("shared", "Shared"),
                           ("any_gap", "Agent-only or partial")):
        L.append(f"| {label} | " + " | ".join(ci(hl[(outcome, s)]) for s in ("overall", *TOOLS)) + " |")
    L += ["",
          f"- Most often agent-only (≥ {MIN_UNITS} units): " + ", ".join(
              f"{c['category']} ({pct(c['agent_only'])})" for c in f["cat_highest"])
          + f"; least: {f['cat_lowest']['category']} ({pct(f['cat_lowest']['agent_only'])}).",
          gee_sentence(f),
          repo_sentence(f),
          f"- Sensitivity: agent-only stays between {pct(f['sens_range'][0])} and {pct(f['sens_range'][1])} "
          "across the robustness variants.",
          coding_mode_sentence(f),
          f"- {f['flags'].get('conflict', 0)} units contradict the human docs; {f['flags'].get('links_out', 0)} "
          "are covered only by a link elsewhere.", ""]

    L += ["## RQ2 — Which newcomer needs and barriers does this knowledge address?", "",
          "Units coded agent-only or partially covered.", "",
          "- Need groups (Dagenais et al.): " + "; ".join(f"{g} {pct(v)}" for g, v in f["need_groups"].items()) + ".",
          "- Top needs: " + "; ".join(f"{n['need']} {pct(n['share'])}" for n in f["needs_top"]) + ".",
          "- Top barriers mitigated (Steinmacher et al.): " + "; ".join(
              f"{b['barrier']} {pct(b['share_of_gap_units'])}" for b in f["barriers_top"])
          + f"; no barrier coded for {pct(f['no_barrier_share'])} of gap units.", ""]

    L += ["## RQ3 — Can agent-only knowledge be detected automatically?", "",
          "Thresholds tuned on the pilot repositories; scores on held-out repositories.", "",
          "| Matcher | Precision | Recall | F1 agent-only | ROC-AUC | Macro-F1 | Evidence in top 5 |",
          "|---|---|---|---|---|---|---|"]
    for r in f["detector"].to_dict("records"):
        L.append(f"| {r['matcher']} ({r['variant']}) | {r['precision']:.2f} | {r['recall']:.2f} | {r['f1']:.2f} | "
                 f"{r['auc']:.2f} | {r['macro_f1']:.2f} | {r['retrieval_hit@5']:.2f} |")
    L += ["", f"- Chosen on the pilot repositories: **{best['matcher']}** — F1 {best['f1']:.2f}, ROC-AUC {best['auc']:.2f}.",
          "- LLM judge: " + ("included (see `analysis/phase6/detector_results.md`)." if len(f["detector_llm"])
                             else "not run yet (needs the model; see `scripts/llm/`)."), ""]

    if f.get("docs_check"):
        d = f["docs_check"]
        L.insert(L.index("## RQ2 — Which newcomer needs and barriers does this knowledge address?"),
                 f"- docs/ check: in {int(d['repos'])} repositories with Markdown under docs/, the detector matches "
                 f"{int(d['covered_by_docs'])} of {int(d['agent_only_units'])} agent-only units ({pct(d['share'])}) "
                 "to a docs/ section.\n")
    fl = f["flesch"]
    L += ["## Readability", "",
          f"Median Flesch Reading Ease: agent files {fl['agent']:.1f}, README {fl['README']:.1f}, "
          f"CONTRIBUTING {fl['CONTRIBUTING']:.1f} (higher = easier).", "",
          "## Details", "",
          "- RQ1/RQ2/sensitivity/provenance: `analysis/phase7/results.md` (+ CSVs)",
          "- RQ3 and error analysis: `analysis/phase6/detector_results.md`, `analysis/phase6/errors.md`",
          "- Reliability: `analysis/phase5/reliability.md`",
          "- Paper: `paper/main.pdf`; run record: `analysis/pipeline_manifest.json`", ""]
    return "\n".join(L)


def write_final_results(mode: str) -> Path:
    path = ANALYSIS / "FINAL_RESULTS.md"
    path.write_text(render(mode))
    return path
