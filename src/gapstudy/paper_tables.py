"""Phase 8: write the paper's result tables as LaTeX (paper/tables/*.tex) from the pipeline outputs.

    python -m gapstudy.paper_tables

Each file is a complete table environment that main.tex \\input{}s, so no result in the
paper is copied by hand. Tables whose inputs do not exist yet are written as a [TBD] stub.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from gapstudy.github_client import PROJECT_ROOT
from gapstudy.summary import TOOLS, facts

OUT = PROJECT_ROOT / "paper" / "tables"
DISPLAY = {"tfidf": "TF-IDF"}
ESCAPE = {"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#", "“": "``", "”": "''", "’": "'", "—": "---"}


def tex(s) -> str:
    s = str(s)
    for k, v in ESCAPE.items():
        s = s.replace(k, v)
    return s


def p1(x: float) -> str:
    return f"{100 * x:.1f}" if pd.notna(x) else "--"


def ci(t) -> str:
    return f"{p1(t[0])} {{\\scriptsize[{p1(t[1])}, {p1(t[2])}]}}"


def table(env: str, caption: str, label: str, spec: str, head: str, rows: list[str], note: str = "") -> str:
    body = [rf"\begin{{{env}}}[t]", rf"\caption{{{caption}}}", rf"\label{{{label}}}", r"\small",
            rf"\begin{{tabular}}{{{spec}}}", r"\toprule", head + r" \\", r"\midrule", *rows, r"\bottomrule",
            r"\end{tabular}"]
    if note:
        body += [r"\\[2pt]", rf"\parbox{{\linewidth}}{{\footnotesize {note}}}"]
    return "\n".join(body + [rf"\end{{{env}}}", ""])


def rq1_headline(f: dict) -> str:
    hl = f["headline"]
    rows = []
    for outcome, name in (("agent_only", "Agent-only"), ("partial", "Partially covered"), ("shared", "Shared"),
                          ("any_gap", "Agent-only or partial")):
        rows.append(f"{name} & " + " & ".join(ci(hl[(outcome, s)]) for s in ("overall", *TOOLS)) + r" \\")
    rows.append(r"\midrule")
    rows.append("Repositories & " + " & ".join(str(hl[("agent_only", s)][3]) for s in ("overall", *TOOLS)) + r" \\")
    return table("table*", "RQ1: share of a repository's agent-file knowledge by coverage in README and CONTRIBUTING "
                 "(mean per repository, \\%; 95\\% repository-bootstrap CI). \\emph{All} is post-stratified to the "
                 "eligible population.", "tab:rq1", "lrrrr",
                 r"Coverage & All & \texttt{CLAUDE.md} & \texttt{AGENTS.md} & Copilot", rows)


def rq1_categories(f: dict) -> str:
    gee = f["gee"]
    names = {v: k for k, v in gee.term.items()}
    rows = []
    for r in f["categories"].itertuples():
        key = names.get(r.category)
        if key is not None and key in gee.index:
            g = gee.loc[key]
            star = "$^{*}$" if g.p < 0.05 else ""
            odds = f"{g.odds_ratio:.2f}{star} {{\\scriptsize[{g.lo:.2f}, {g.hi:.2f}]}}"
        else:
            odds = "--"
        rows.append(f"{tex(r.category)} & {r.units} & {p1(r.agent_only)} & {p1(r.any_gap)} & {odds} " + r"\\")
    return table("table*", "RQ1 by instruction category: share of units that are agent-only and agent-only or "
                 "partially covered (\\%, unit level), and the odds ratio for agent-only from a logistic GEE "
                 "clustered by repository (category vs.\\ all others, adjusted for agent; $^{*}$ $p < 0.05$). "
                 "A unit can have several categories.", "tab:rq1cat", "lrrrr",
                 r"Category & Units & Agent-only & Agent-only or partial & Odds ratio [95\% CI]", rows)


def rq2_needs(f: dict) -> str:
    rows, last = [], None
    order = {g: i for i, g in enumerate(f["need_groups"].index)}  # largest group first
    needs = f["needs"].assign(_g=f["needs"].group.map(order)).sort_values(["_g", "share"], ascending=[True, False])
    for r in needs.itertuples():
        if r.group != last:
            if last is not None:
                rows.append(r"\addlinespace")
            share = f["need_groups"][r.group]
            rows.append(rf"\multicolumn{{2}}{{l}}{{\emph{{{tex(r.group)}}}}} & {p1(share)} \\")
            last = r.group
        rows.append(rf"\quad {tex(r.need)} & {r.units} & {p1(r.share)} \\")
    return table("table", "RQ2: newcomer needs~\\cite{dagenais2010landscape} served by agent-only or partially "
                 "covered knowledge (units, and share of gap units, \\%).", "tab:rq2needs", "lrr",
                 r"Need & Units & Share", rows)


def rq2_barriers(f: dict) -> str:
    rows = [rf"{tex(r.barrier)} & {r.units} & {p1(r.share_of_gap_units)} \\"
            for r in f["barriers"].itertuples() if r.group != "—"]
    note = f"No barrier was coded for {p1(f['no_barrier_share'])}\\% of gap units. Multi-label."
    return table("table", "RQ2: newcomer barriers~\\cite{steinmacher2015barriers} that the gap knowledge would "
                 "mitigate (units, share of gap units, \\%).", "tab:rq2bar", "p{0.62\\linewidth}rr",
                 r"Barrier & Units & Share", rows, note)


def rq3(f: dict) -> str:
    rows = []
    short = {"tfidf": "TF-IDF", "sentence-transformers/all-MiniLM-L6-v2": "MiniLM-L6",
             "BAAI/bge-base-en-v1.5": "bge-base", "Qwen/Qwen3-Embedding-0.6B": "Qwen3-Emb-0.6B"}
    for r in f["detector"].to_dict("records"):
        lo, hi = (float(x) for x in str(r["f1_ci"]).strip("()").split(","))
        alo, ahi = (float(x) for x in str(r["auc_ci"]).strip("()").split(","))
        name = tex(short.get(r["matcher"], r["matcher"].split("/")[-1]))
        name = rf"\textbf{{{name}}}" if r["matcher"] == f["detector_best"]["matcher"] else name
        rows.append(f"{name} & {r['precision']:.2f} & {r['recall']:.2f} & {r['f1']:.2f} & {r['auc']:.2f} & "
                    f"{r['macro_f1']:.2f} & {r['retrieval_hit@1']:.2f}/{r['retrieval_hit@5']:.2f} " + r"\\")
        rows.append(rf"\quad{{\scriptsize\itshape {tex(r['variant'])}}} & & & {{\scriptsize[{lo:.2f}, {hi:.2f}]}} & "
                    rf"{{\scriptsize[{alo:.2f}, {ahi:.2f}]}} & & \\")
    for r in f["detector_llm"].to_dict("records"):
        rows.append(f"{tex(r['matcher'])} ({tex(r.get('mode', 'LLM'))}) & {r['precision']:.2f} & {r['recall']:.2f} & "
                    f"{r['f1']:.2f} & -- & {r['macro_f1']:.2f} & -- " + r"\\")
    b = f["detector_best"]
    body = table("table", "RQ3: gap detector on held-out repositories "
                 f"(n = {int(b['n_test'])} units; score variant, in italics, and thresholds tuned on {int(b['n_dev'])} "
                 "pilot units). P, R and F1 for agent-only; macro-F1 over agent-only/partial/shared; @1/@5: the gold "
                 "covering section ranked first / in the top five. Bold: chosen on the pilot repositories. "
                 "Brackets: 95\\% repository-bootstrap CI.", "tab:rq3", "@{}lrrrrrr@{}",
                 r"Matcher & P & R & F1 & AUC & Mac.-F1 & @1/@5", rows)
    return body.replace(r"\small", r"\small\setlength{\tabcolsep}{3.5pt}", 1)


def sensitivity(f: dict) -> str:
    rows = [rf"{tex(r.variant)} & {r.repos} & {p1(r.agent_only)} \\" for r in f["sensitivity"].itertuples()]
    return table("table", "Sensitivity of the agent-only share (post-stratified, \\%).", "tab:sens", "lrr",
                 r"Variant & Repos & Agent-only", rows)


def provenance(f: dict) -> str:
    if "provenance" not in f:
        return ""
    p = f["provenance"]
    cols = [("draft_accepted", "Kept"), ("draft_details_edited", "Edited"),
            ("draft_corrected", "Corrected"), ("blind", "Blind")]
    cols = [(k, n) for k, n in cols if k in p and p[k].sum()]
    rows = [f"{tex(s.capitalize())} & " + " & ".join(str(int(p.loc[s, k])) for k, _ in cols) + r" \\" for s in p.index]
    rows.append(r"\midrule")
    rows.append("Total & " + " & ".join(str(int(p[k].sum())) for k, _ in cols) + r" \\")
    return table("table", "How the frozen labels were produced, per coding set: an AI draft the annotator kept "
                 "unchanged, kept with other fields edited, or corrected in coverage; or blind coding without a draft.", "tab:prov", "l" + "r" * len(cols),
                 "Set & " + " & ".join(n for _, n in cols), rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    f = facts()
    written = []
    for name, fn in (("rq1_headline", rq1_headline), ("rq1_categories", rq1_categories), ("rq2_needs", rq2_needs),
                     ("rq2_barriers", rq2_barriers), ("rq3", rq3), ("sensitivity", sensitivity),
                     ("provenance", provenance)):
        (OUT / f"{name}.tex").write_text(fn(f) or "% not available\n")
        written.append(name)
    print(f"wrote {len(written)} tables to {OUT}: {', '.join(written)}")


if __name__ == "__main__":
    main()
