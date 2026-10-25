"""Phase 8: write every number the paper uses as a LaTeX macro (paper/numbers.tex).

    python -m gapstudy.paper_numbers

Numbers come straight from the pipeline outputs, so the paper never carries a
hand-copied figure. Results that need frozen labels (RQ1-RQ3, reliability) are
written as \\TBD until coding/labels_v1.csv exists and the analyses have run;
provisional results are never written into the paper.
"""

from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from gapstudy.github_client import PROJECT_ROOT

PROCESSED = PROJECT_ROOT / "data" / "processed"
OUT = PROJECT_ROOT / "paper" / "numbers.tex"
TBD = r"\TBD"


def num(x, digits: int = 0) -> str:
    return f"{x:,.{digits}f}".replace(",", "{,}")


def pct(x, digits: int = 1) -> str:
    return TBD if x is None or pd.isna(x) else f"{100 * x:.{digits}f}\\%"


def macro_name(*parts: str) -> str:
    words = re.sub(r"[^A-Za-z ]+", " ", " ".join(parts)).split()
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def sampling() -> dict[str, str]:
    flow = pd.read_csv(PROCESSED / "sampling_flow.csv").set_index("step")
    m = {"nPackageFiles": num(flow.total.iloc[0]), "nEligible": num(flow.total.iloc[-1])}
    for step, row in flow.iterrows():
        m[macro_name("flow", step.replace("minus", ""))] = num(row.total)
    for tool, key in (("claude", "Claude"), ("agents", "Agents"), ("copilot-instructions", "Copilot")):
        m[f"nEligible{key}"] = num(flow[tool].iloc[-1])
    units = pd.read_csv(PROCESSED / "units.csv")
    queue = pd.read_csv(PROJECT_ROOT / "coding" / "queue.csv")
    assign = pd.read_csv(PROJECT_ROOT / "coding" / "assignments.csv")
    inv = pd.read_csv(PROCESSED / "docs_inventory.csv")
    sample = pd.read_csv(PROCESSED / "sample.csv")
    sample = sample[sample.in_sample]
    m |= {
        "nSampleRepos": num(len(sample)), "nPerAgent": num(len(sample) // 3),
        "sampleMedianStars": num(sample.stars.median()),
        "nUnits": num(len(units)), "nAgentUnits": num((units.doc == "agent").sum()),
        "nReadmeUnits": num((units.doc == "README").sum()), "nContribUnits": num((units.doc == "CONTRIBUTING").sum()),
        "agentUnitMedianWords": num((units[units.doc == "agent"].words).median()),
        "nCodable": num(((units.doc == "agent") & ~units.toc).sum()), "nQueued": num(len(queue)),
        "nPilotRepos": num((assign.set == "pilot").sum()), "nReliabilityRepos": num((assign.set == "reliability").sum()),
        "nMainRepos": num((assign.set == "main").sum()),
        "nPilotUnits": num((queue.set == "pilot").sum()), "nReliabilityUnits": num((queue.set == "reliability").sum()),
        "nFullyCodedRepos": num((assign.codable_units <= 10).sum()),
        "nStubContributing": num(assign.stub_contributing.sum()), "nInitUnedited": num(assign.init_unedited.sum()),
        "nDocsRepos": num((inv.docs_files > 0).sum()), "nDocsSubsample": num(inv.in_docs_subsample.sum()),
        "nDocsFiles": num(inv.docs_fetched.sum()),
    }
    return m


def corpus() -> dict[str, str]:
    path = PROJECT_ROOT / "analysis" / "phase7" / "corpus_documents.csv"
    if not path.exists():
        return {}
    d = pd.read_csv(path)
    med = d.groupby("doc")[["words", "flesch"]].median()
    m = {f"{k}Words": num(med.loc[doc, "words"]) for doc, k in (("agent", "agent"), ("README", "readme"), ("CONTRIBUTING", "contrib"))}
    m |= {f"{k}Flesch": num(med.loc[doc, "flesch"], 1) for doc, k in (("agent", "agent"), ("README", "readme"), ("CONTRIBUTING", "contrib"))}
    pair = d.pivot(index="repo", columns="doc", values="flesch")[["agent", "CONTRIBUTING"]].dropna()
    diff = pair.agent - pair.CONTRIBUTING  # same pairs as gapstudy.analysis.corpus.paired_tests
    p = wilcoxon(pair.agent, pair.CONTRIBUTING).pvalue
    m["fleschGapContrib"] = num(-diff.median(), 1)
    m["fleschHarderShare"] = pct((diff < 0).mean(), 0)
    m["fleschPairs"] = num(len(pair))
    m["fleschContribP"] = r"$p < 0.0001$" if p < 1e-4 else f"$p = {p:.3g}$"
    by_tool = d[d.doc == "agent"].groupby("tool").flesch.median()
    m |= {"fleschClaude": num(by_tool["claude"], 1), "fleschAgents": num(by_tool["agents"], 1),
          "fleschCopilot": num(by_tool["copilot-instructions"], 1)}
    return m


def results() -> dict[str, str]:
    """RQ1-RQ3 numbers, only from frozen labels."""
    frozen = (PROJECT_ROOT / "coding" / "labels_v1.csv").exists()
    phase7 = PROJECT_ROOT / "analysis" / "phase7"
    keys = ["agentOnlyOverall", "agentOnlyClaude", "agentOnlyAgents", "agentOnlyCopilot", "anyGapOverall",
            "sharedOverall", "agentDirectedOverall", "kappaCoverage", "kappaWeighted", "detectorBestMatcher",
            "detectorFOne", "detectorAUC", "nCodedUnits", "nKnowledgeUnits"]
    m = {k: TBD for k in keys}
    if not frozen:
        return m
    labels = pd.read_csv(PROJECT_ROOT / "coding" / "labels_v1.csv")
    m["nCodedUnits"] = num(len(labels))
    m["nKnowledgeUnits"] = num(labels.coverage.isin(["agent_only", "partial", "shared"]).sum())
    head = phase7 / "rq1_headline.csv"
    if head.exists():
        h = pd.read_csv(head).set_index(["outcome", "scope"])
        fmt = lambda o, s: f"{pct(h.loc[(o, s), 'estimate'])} [{pct(h.loc[(o, s), 'lo'])}, {pct(h.loc[(o, s), 'hi'])}]"
        m |= {"agentOnlyOverall": fmt("agent_only", "overall"), "agentOnlyClaude": fmt("agent_only", "claude"),
              "agentOnlyAgents": fmt("agent_only", "agents"), "agentOnlyCopilot": fmt("agent_only", "copilot-instructions"),
              "anyGapOverall": fmt("any_gap", "overall"), "sharedOverall": fmt("shared", "overall"),
              "agentDirectedOverall": pct(h.loc[("agent_directed_share", "overall"), "estimate"])}
    det = PROJECT_ROOT / "analysis" / "phase6" / "detector_results.csv"
    if det.exists():
        r = pd.read_csv(det)
        if "variant" in r.columns:  # matcher rows only; LLM rows have no score variant
            r = r[~r.provisional.astype(bool) & r.variant.notna()]
        if "variant" in r.columns and len(r):
            best = r.sort_values("dev_f1", ascending=False).iloc[0]
            m |= {"detectorBestMatcher": best.matcher.replace("_", r"\_"), "detectorFOne": num(best.f1, 2),
                  "detectorAUC": num(best.auc, 2)}
    rel = PROJECT_ROOT / "analysis" / "phase5" / "reliability.md"
    if rel.exists():
        text = rel.read_text()
        for key, label in (("kappaCoverage", "Cohen's κ (4 labels)"), ("kappaWeighted", "linearly weighted κ")):
            hit = re.search(re.escape(label) + r"[^|]*\| ([0-9.]+)", text)
            if hit:
                m[key] = hit.group(1)
    return m


def main() -> None:
    macros = {**sampling(), **corpus(), **results()}
    lines = ["% Generated by `python -m gapstudy.paper_numbers`. Do not edit by hand.",
             r"\providecommand{\TBD}{\textcolor{red}{\textbf{[TBD]}}}"]
    lines += [rf"\newcommand{{\{k}}}{{{v}}}" for k, v in sorted(macros.items())]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    tbd = sum(v == TBD for v in macros.values())
    print(f"wrote {len(macros)} macros to {OUT} ({tbd} still TBD)")


if __name__ == "__main__":
    main()
