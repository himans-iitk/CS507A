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
        "nMainUnits": num((queue.set == "main").sum()),
        "nFullyCodedRepos": num((assign.codable_units <= 10).sum()),
        "nStubContributing": num(assign.stub_contributing.sum()), "nInitUnedited": num(assign.init_unedited.sum()),
        "nDocsRepos": num((inv.docs_files > 0).sum()), "nDocsSubsample": num(inv.in_docs_subsample.sum()),
        "nDocsFiles": num(inv.docs_fetched.sum()),
    }
    # Dataset and corpus descriptives for the methods section.
    dates = pd.to_datetime(sample.snapshot_date)
    src = sample.snapshot_source.value_counts()
    m |= {"snapshotFirst": dates.min().strftime("%B %Y"), "snapshotLast": dates.max().strftime("%B %Y"),
          "nSnapshotPackage": num(src.get("package_history", 0)), "nSnapshotAPI": num(src.get("api_history", 0)),
          "nDuplicateDropped": num(flow.total.iloc[7] - flow.total.iloc[8]),
          "nDroppedNoContributing": num(flow.total.iloc[-2] - flow.total.iloc[-1])}
    multi = PROJECT_ROOT / "analysis" / "phase1" / "repo_agent_files.csv"
    if multi.exists():
        r = pd.read_csv(multi)
        m |= {"nPackageRepos": num(len(r)), "nMultiAgentRepos": num((r.n_files > 1).sum())}
    agent = units[units.doc == "agent"]
    per_repo = agent.groupby("repo").size()
    m |= {"agentUnitsPerRepoMedian": num(per_repo.median()), "agentUnitsPerRepoNinety": num(per_repo.quantile(.9)),
          "agentUnitsPerRepoMax": num(per_repo.max()), "nCodeOnlyAgentUnits": num(agent.code_only.sum()),
          "readmeUnitMedianWords": num(units[units.doc == "README"].words.median()),
          "contribUnitMedianWords": num(units[units.doc == "CONTRIBUTING"].words.median())}
    from gapstudy.detector.items import split_items
    n_items = units[~units.toc].assign(n=lambda d: d.text.fillna("").map(lambda t: len(split_items(t))))
    m |= {"nItemsAgent": num(n_items[n_items.doc == "agent"].n.sum()),
          "nItemsHuman": num(n_items[n_items.doc != "agent"].n.sum())}
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
    words = d.pivot(index="repo", columns="doc", values="words")[["agent", "CONTRIBUTING"]].dropna()
    m["wordsGapContrib"] = num((words.agent - words.CONTRIBUTING).median())
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
            m |= {"detectorBestMatcher": {"tfidf": "TF-IDF"}.get(best.matcher, best.matcher.replace("_", r"\_")), "detectorFOne": num(best.f1, 2),
                  "detectorAUC": num(best.auc, 2)}
    rel = reliability_status()
    if rel.get("status") in ("complete", "partial"):
        for key, field in (("kappaCoverage", "coverage_kappa"), ("kappaWeighted", "coverage_weighted_kappa")):
            if rel.get(field) is not None:
                m[key] = num(rel[field], 2)
                if rel.get(f"{field}_ci"):
                    lo, hi = rel[f"{field}_ci"]
                    m[key + "CI"] = f"[{num(lo, 2)}, {num(hi, 2)}]"
        m["nSecondCodedUnits"] = num(rel["units"])
        m["relAgreement"] = pct(rel["coverage_agreement"])
        m["secondCoderModel"] = ", ".join(rel.get("second_coder_models") or []) or "an LLM"
        if rel.get("repo_agreement_median") is not None:
            m["relRepoMedian"] = pct(rel["repo_agreement_median"], 0)
            m["relReposFull"] = num(rel["repos_full_agreement"])
        if rel.get("category_jaccard") is not None:
            m["relCategoryJaccard"] = num(rel["category_jaccard"], 2)
        for tool, key in (("claude", "Claude"), ("agents", "Agents"), ("copilot-instructions", "Copilot")):
            if tool in rel.get("by_agent", {}):
                m[f"relKappa{key}"] = num(rel["by_agent"][tool]["kappa"], 2)
        conf = rel.get("confusion", {})
        if conf:
            off = [(a, b, n) for a, row in conf.items() for b, n in row.items() if a != b]
            a, b, n = max(off, key=lambda t: t[2])
            m["relTopConfusionN"] = num(n)
            m["relTopConfusionShare"] = pct(n / sum(t[2] for t in off), 0)
            m["relTopConfusionFrom"] = a.replace("_", "-")
            m["relTopConfusionTo"] = b.replace("_", "-")
    det = PROJECT_ROOT / "data" / "processed" / "scores"
    if det.exists():
        cols = {p.stem: pd.read_csv(p, usecols=["unit_id", "item_mean"]).set_index("unit_id").item_mean
                for p in sorted(det.glob("*.csv"))}
        if len(cols) > 1:
            rho = pd.DataFrame(cols).corr(method="spearman").to_numpy()
            off = rho[~np.eye(len(rho), dtype=bool)]
            m["matcherRhoMin"], m["matcherRhoMax"] = num(off.min(), 2), num(off.max(), 2)
    m |= provenance_numbers(labels)
    return m


def reliability_status() -> dict:
    path = PROJECT_ROOT / "analysis" / "phase5" / "reliability.json"
    return json.loads(path.read_text()) if path.exists() else {"status": "pending"}


def provenance_numbers(labels: pd.DataFrame) -> dict[str, str]:
    """Counts behind the methods text on how the labels were produced."""
    from gapstudy.analysis import provenance
    from gapstudy.drafting import load_drafts
    if "draft_shown" not in labels:
        return {}
    s = provenance.summary(labels, load_drafts(PROJECT_ROOT / "coding"))
    c = s["counts"]
    ns = s["need_source"]
    pick = lambda prefix: int(sum(v for k, v in ns.items() if k.startswith(prefix)))  # noqa: E731
    return {"nDraftsReviewed": num(s["n_reviewed"]), "nDraftsKept": num(s["n_reviewed"] - c["draft_corrected"]),
            "nDraftsCorrected": num(c["draft_corrected"]), "draftKeepRate": pct(s["accept_rate"]),
            "nAiFilled": num(s["n_ai_filled"]), "nBlindCoded": num(c["blind"]),
            "nNeedFirst": num(pick("first")), "nNeedFromSecond": num(pick("second")), "nNeedFilled": num(pick("model"))}


def findings() -> dict[str, str]:
    """Numbers and names behind the results prose (from gapstudy.summary.facts)."""
    try:
        from gapstudy.summary import facts
        f = facts()
    except FileNotFoundError:
        return {}
    tex = lambda s: str(s).replace("&", r"\&").replace("_", r"\_")  # noqa: E731
    m: dict[str, str] = {}
    for i, c in enumerate(f["cat_highest"], 1):
        word = ("One", "Two", "Three")[i - 1]
        m[f"catHigh{word}"] = tex(c["category"])
        m[f"catHigh{word}Share"] = pct(c["agent_only"])
    m |= {"catLow": tex(f["cat_lowest"]["category"]), "catLowShare": pct(f["cat_lowest"]["agent_only"])}
    sig = f["gee_sig_cats"]
    m["geeSigCats"] = ", ".join(f"{tex(r.term)} (OR {r.odds_ratio:.2f})" for r in sig.itertuples()) or "none"
    m["geeAgentMinP"] = num(f["gee_agent_min_p"], 2)
    n_terms = len(f["gee"])
    bonf = sig[sig.p < 0.05 / n_terms]
    m["geeNTerms"] = num(n_terms)
    m["geeBonferroniCats"] = " and ".join(tex(t) for t in bonf.term) or "none"
    m["geeNBonferroni"] = num(len(bonf))
    g = f["gee"]
    for term, key in (("agent:agents", "Agents"), ("agent:copilot-instructions", "Copilot")):
        if term in g.index:
            r = g.loc[term]
            m[f"geeOr{key}"] = f"{r.odds_ratio:.2f} [{r.lo:.2f}, {r.hi:.2f}]"
    if "provenance_by_draft" in f:
        pd_ = f["provenance_by_draft"]
        m |= {f"draftCorr{k}": pct(pd_.loc[c, "correction_rate"]) for c, k in
              (("agent_only", "AgentOnly"), ("partial", "Partial"), ("shared", "Shared"),
               ("agent_directed", "AgentDirected")) if c in pd_.index}
    bl = f.get("baseline")
    if bl and bl["n"]:
        m |= {"baselinePrecision": num(bl["precision"], 2), "baselineFOne": num(bl["f1"], 2),
              "testAgentOnlyShare": pct(bl["precision"], 0)}
    best = f["detector_best"]
    m["detectorDevFOne"] = num(best["dev_f1"], 2)
    m["detectorBestVariant"] = tex(str(best["variant"]).replace("_", " "))
    m["geeAgentsDiffer"] = "no" if f["gee_agent_min_p"] >= 0.05 else "yes"
    groups = f["need_groups"]
    m["needGroupTop"], m["needGroupTopShare"] = tex(groups.index[0]), pct(groups.iloc[0])
    m["needGroupProduct"] = pct(groups.get("Product", 0))
    m["needGroupDocs"] = pct(groups.get("Documentation", 0))
    m["needGroupTeamContext"] = pct(groups.get("Team", 0) + groups.get("Context", 0))
    for i, n in enumerate(f["needs_top"], 1):
        word = ("One", "Two", "Three")[i - 1]
        m[f"needTop{word}"], m[f"needTop{word}Share"] = tex(n["need"]), pct(n["share"])
    for i, b in enumerate(f["barriers_top"], 1):
        word = ("One", "Two", "Three")[i - 1]
        m[f"barrierTop{word}"], m[f"barrierTop{word}Share"] = tex(b["barrier"]), pct(b["share_of_gap_units"])
    m["noBarrierShare"] = pct(f["no_barrier_share"])
    m["sensLow"], m["sensHigh"] = pct(f["sens_range"][0]), pct(f["sens_range"][1])
    for key, name in (("blind", "Blind"), ("drafted", "Drafted")):
        r = f.get("sens_mode", {}).get(key)
        if r:
            m[f"agentOnly{name}"] = f"{pct(r['agent_only'])} [{pct(r['lo'])}, {pct(r['hi'])}]"
            m[f"n{name}Repos"] = num(r["repos"])
    cm = f.get("coding_mode")
    if cm:
        pp = lambda x: f"{100 * x:+.1f}".replace("-", "$-$")  # noqa: E731
        m["codingModeDiff"] = f"{pp(cm['difference'])} percentage points [{pp(cm['lo'])}, {pp(cm['hi'])}]"
        m["codingModeSignificant"] = "no" if cm["lo"] <= 0 <= cm["hi"] else "yes"
    if "repo_facts" in f:
        rf, sp = f["repo_facts"], f["repo_spread"]
        m |= {"nRepoKnowledge": num(rf["repos"]), "repoAnyAgentOnly": num(rf["any_agent_only"]),
              "repoAnyAgentOnlyShare": pct(rf["any_agent_only"] / rf["repos"], 0),
              "repoAllAgentOnly": num(rf["all_agent_only"]), "repoNoShared": num(rf["no_shared"]),
              "repoNoSharedShare": pct(rf["no_shared"] / rf["repos"], 0),
              "repoAgentOnlyMedian": pct(sp.loc["agent_only", "median"]), "repoAgentOnlyQOne": pct(sp.loc["agent_only", "q1"]),
              "repoAgentOnlyQThree": pct(sp.loc["agent_only", "q3"]), "repoGapMedian": pct(sp.loc["any_gap", "median"])}
    m["nConflictUnits"] = num(f["flags"].get("conflict", 0))
    m["nLinksOutUnits"] = num(f["flags"].get("links_out", 0))
    b, d = f["detector_best"], f["detector"]
    m |= {"detectorPrecision": num(b["precision"], 2), "detectorRecall": num(b["recall"], 2),
          "detectorMacroFOne": num(b["macro_f1"], 2), "detectorHitOne": pct(b["retrieval_hit@1"], 0),
          "detectorHitFive": pct(b["retrieval_hit@5"], 0), "detectorNTest": num(b["n_test"]),
          "detectorNDev": num(b["n_dev"]), "detectorFOneMin": num(d.f1.min(), 2), "detectorFOneMax": num(d.f1.max(), 2),
          "detectorAUCMin": num(d.auc.min(), 2), "detectorAUCMax": num(d.auc.max(), 2),
          "detectorLLM": "yes" if len(f["detector_llm"]) else "no"}
    if f["errors_false_agent_only"] is not None:
        m["detectorFalseAgentOnly"] = num(f["errors_false_agent_only"])
        m["detectorMissedAgentOnly"] = num(f["errors_missed_agent_only"])
    if f.get("docs_check"):
        d = f["docs_check"]
        m |= {"docsCheckRepos": num(d["repos"]), "docsCheckCovered": num(d["covered_by_docs"]),
              "docsCheckUnits": num(d["agent_only_units"]), "docsCheckShare": pct(d["share"])}
    return m


def main() -> None:
    macros = {**sampling(), **corpus(), **results(), **findings()}
    switches = {"agentsdiffer": macros.pop("geeAgentsDiffer", "no") == "yes",
                "llmjudge": macros.pop("detectorLLM", "no") == "yes",
                "secondcoderllm": reliability_status().get("kind") == "human-llm",
                "codingmodediffers": macros.pop("codingModeSignificant", "no") == "yes"}
    lines = ["% Generated by `python -m gapstudy.paper_numbers`. Do not edit by hand.",
             r"\providecommand{\TBD}{\textcolor{red}{\textbf{[TBD]}}}"]
    lines += [rf"\newcommand{{\{k}}}{{{v}}}" for k, v in sorted(macros.items())]
    second = reliability_status().get("status") in ("complete", "partial")
    lines += [r"\newif\ifsecondcoder", r"\secondcodertrue" if second else r"\secondcoderfalse"]
    for name, on in switches.items():
        lines += [rf"\newif\if{name}", rf"\{name}{'true' if on else 'false'}"]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    waiting = set() if second else {"kappaCoverage", "kappaWeighted"}  # only printed once a second coder exists
    tbd = sum(v == TBD and k not in waiting for k, v in macros.items())
    mode = ({"human-llm": "human + LLM second annotator", "inter-rater": "two human annotators",
             "intra-rater": "one annotator, re-coded"}.get(reliability_status().get("kind"), "two annotators")
            if second else "single annotator (reliability pending)")
    print(f"wrote {len(macros)} macros to {OUT} ({tbd} still TBD; {mode})")


if __name__ == "__main__":
    main()
