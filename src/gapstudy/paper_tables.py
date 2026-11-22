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
        rows.append(f"{tex(r.category)} & {r.units} & {p1(r.agent_only)} & {odds} " + r"\\")
    body = table("table", "RQ1 by instruction category: share of units that are agent-only (\\%, unit level) "
                 "and the odds ratio for agent-only from a logistic GEE clustered by repository (category vs.\\ "
                 "all others, adjusted for agent type; $^{*}$ $p < 0.05$). A unit can have several categories.",
                 "tab:rq1cat", "@{}lrrr@{}", r"Category & Units & Agent-only & Odds ratio [95\% CI]", rows)
    return body.replace(r"\small", r"\footnotesize\setlength{\tabcolsep}{3.5pt}", 1)


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
    note = ((f"No barrier was coded for {p1(f['no_barrier_share'])}\\% of gap units. " if f["no_barrier_share"] > 0 else "")
            + "Multi-label: a unit can ease several barriers.")
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


SENS_NAMES = {"all coded repos (primary)": "All coded repositories (primary)",
              "without unedited /init files": r"Without unedited \texttt{/init} files",
              "without stub CONTRIBUTING": "Without stub CONTRIBUTING files",
              "without links_out units": "Without units whose topic is only linked",
              "only AI-drafted repos (pilot + main)": "Only AI-drafted labels (pilot, main)",
              "only blind-coded repos (reliability set)": "Only blind-coded labels (reliability)"}


def sensitivity(f: dict) -> str:
    rows = []
    for r in f["sensitivity"].itertuples():
        if r.variant.startswith("only ") and not any(x.startswith("Only") for x in rows):
            rows.append(r"\midrule")  # rule before the coding-mode split
        lo, hi = getattr(r, "lo", float("nan")), getattr(r, "hi", float("nan"))
        rows.append(rf"{SENS_NAMES.get(r.variant, tex(r.variant))} & {r.repos} & "
                    + (ci((r.agent_only, lo, hi)) if pd.notna(lo) else p1(r.agent_only)) + r" \\")
    return table("table", "Sensitivity of the agent-only share (post-stratified, \\%; 95\\% repository-bootstrap "
                 "CI). The last two rows split the sample by how the labels were produced.", "tab:sens",
                 "@{}lrr@{}", r"Variant & Repos & Agent-only", rows)


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


def flow(f: dict) -> str:
    """Sampling flow per agent file type, from data/processed/sampling_flow.csv."""
    path = PROJECT_ROOT / "data" / "processed" / "sampling_flow.csv"
    if not path.exists():
        return ""
    fl = pd.read_csv(path)
    names = {"all agent files in package": "Agent files in the dataset",
             "minus repo no longer exists": "$-$ repository deleted", "minus fork": "$-$ fork",
             "minus archived": "$-$ archived", "minus snapshot commit not found": "$-$ snapshot commit not found",
             "minus agent file is a symlink": "$-$ agent file is a symlink",
             "minus agent file only links elsewhere": "$-$ agent file only links elsewhere",
             "minus agent file not in English": "$-$ not in English",
             "minus copy of another repo's agent file": "$-$ copy of another repository's file",
             "minus no README at snapshot": "$-$ no README at snapshot",
             "minus no CONTRIBUTING at snapshot": "$-$ no CONTRIBUTING at snapshot"}
    n = lambda x: f"{int(x):,}".replace(",", "{,}")  # noqa: E731
    rows = [f"{names.get(r.step, tex(r.step))} & {n(r.claude)} & {n(r.agents)} & {n(r[3])} & {n(r.total)} " + r"\\"
            for r in fl.itertuples(index=False)]
    sample = pd.read_csv(path.with_name("sample.csv"), usecols=["tool", "in_sample"])
    per = sample[sample.in_sample].tool.value_counts()
    cells = [per.get(t, 0) for t in ("claude", "agents", "copilot-instructions")]
    rows += [r"\midrule", r"\textbf{Sampled} (one per repository) & " + " & ".join(map(n, cells))
             + f" & {n(sum(cells))} " + r"\\"]
    return table("table", "Sampling flow: agent files remaining after each exclusion, applied in order "
                 "(each file counted at its first failing rule).", "tab:flow", "@{}lrrrr@{}",
                 r"Step & \texttt{CLAUDE} & \texttt{AGENTS} & Copilot & All", rows).replace(
                     r"\small", r"\small\setlength{\tabcolsep}{3pt}", 1)


def corpus(f: dict) -> str:
    """Documents and knowledge units per document type."""
    units_path = PROJECT_ROOT / "data" / "processed" / "units.csv"
    if not units_path.exists():
        return ""
    u = pd.read_csv(units_path, usecols=["repo", "doc", "words", "toc", "code_only"])
    d = f["docs"]
    rows = []
    for doc, name in (("agent", "Agent file"), ("README", "README"), ("CONTRIBUTING", "CONTRIBUTING")):
        g, dd = u[u.doc == doc], d[d.doc == doc]
        rows.append(f"{name} & {int(dd.words.median()):,} & {dd.flesch.median():.1f} & {len(g):,} & "
                    f"{int(g.words.median())} & {int(g.groupby('repo').size().median())} " + r"\\")
    rows = [r.replace(",", "{,}") for r in rows]
    return table("table", "The corpus: \\nSampleRepos{} repositories, three documents each at the snapshot commit. "
                 "Medians per document (words; Flesch Reading Ease~\\cite{flesch1948readability} on prose, "
                 "higher is easier) and per knowledge unit (words; units per repository).", "tab:corpus", "@{}lrrrrr@{}",
                 r"& \multicolumn{2}{c}{Per document} & \multicolumn{3}{c}{Knowledge units} \\ "
                 r"\cmidrule(lr){2-3}\cmidrule(l){4-6} Document & Words & Flesch & All & Words & Per repo",
                 rows).replace(r"\small", r"\small\setlength{\tabcolsep}{4pt}", 1)


COV = (("agent_only", "Agent-only"), ("partial", "Partial"), ("shared", "Shared"), ("agent_directed", "Agent-dir."))


def reliability(f: dict) -> str:
    """Confusion matrix of the blind double-coded set (first annotator x second annotator)."""
    rel = f["reliability"]
    conf = rel.get("confusion")
    if not conf:
        return ""
    second = "LLM annotator" if rel.get("kind") == "human-llm" else "Second coder"
    rows = []
    for a, name in COV:
        row = conf.get(a, {})
        cells = [(rf"\textbf{{{row.get(b, 0)}}}" if a == b else str(row.get(b, 0))) for b, _ in COV]
        rows.append(f"{name} & " + " & ".join(cells) + f" & {sum(row.values())} " + r"\\")
    col = [sum(conf.get(a, {}).get(b, 0) for a, _ in COV) for b, _ in COV]
    rows += [r"\midrule", "Total & " + " & ".join(map(str, col)) + f" & {sum(col)} " + r"\\"]
    kind = "human--LLM" if rel.get("kind") == "human-llm" else "inter-rater"
    return table("table", f"Coverage labels on the blind reliability set ({rel['units']} units, {rel['repos']} "
                 f"repositories; {kind} agreement). Rows: first annotator; columns: {second}.",
                 "tab:rel", "@{}lrrrrr@{}", r"First $\downarrow$ / " + second.split()[0] + r" $\rightarrow$ & " +
                 " & ".join(n for _, n in COV) + " & Total", rows).replace(
                     r"\small", r"\small\setlength{\tabcolsep}{3.5pt}", 1)


def latex_text(s: str) -> str:
    """Markdown excerpt -> safe LaTeX: inline code to \\texttt, bold dropped, specials escaped."""
    import re
    s = re.sub(r"\s+", " ", str(s)).strip()
    s = s.replace("**", "")
    s = "".join(ch for ch in s if ord(ch) < 0x2000 or ch in "–—’“”…")
    parts = re.split(r"(`[^`]*`)", s)
    out = []
    for p in parts:
        code = p.startswith("`") and p.endswith("`") and len(p) > 1
        p = p.strip("`") if code else p
        p = (p.replace("\\", "\0").replace("{", r"\{").replace("}", r"\}")
             .replace("\0", r"\textbackslash{}").replace("$", r"\$").replace("^", r"\^{}").replace("~", r"\~{}")
             .replace("<", r"\textless{}").replace(">", r"\textgreater{}"))
        p = tex(p)
        if not code:
            p = re.sub(r"(^|\s)[-*]\s+", lambda m: m.group(1) + r"\textbullet\ ", p)  # list markers
        out.append(rf"\texttt{{{p}}}" if code else p)
    return "".join(out)


def clip(s: str, words: int) -> str:
    """First `words` words as LaTeX, with an ellipsis if shortened."""
    w = str(s).split()
    return latex_text(" ".join(w[:words])) + (r" \dots" if len(w) > words else "")


def examples(f: dict, rows_max: int = 6, words: int = 32) -> str:
    ex = f.get("examples")
    if ex is None or ex.empty:
        return ""
    ex = ex[~ex.text.str.contains("```", regex=False)].drop_duplicates("need")
    file = {"claude": r"\texttt{CLAUDE.md}", "agents": r"\texttt{AGENTS.md}",
            "copilot-instructions": "Copilot"}
    rows = []
    for r in ex.head(rows_max).itertuples():
        heading = str(r.heading).split(" > ")[-1] if isinstance(r.heading, str) and r.heading else ""
        where = rf"{tex(r.repo)} ({file.get(r.tool, tex(r.tool))})"
        rows.append(rf"{tex(r.need)} & {where}" + (rf"\newline\emph{{{latex_text(heading)}}}" if heading else "")
                    + rf" & {clip(r.text, words)} \\")
        rows.append(r"\addlinespace[2pt]")
    rows = rows[:-1]
    body = table("table*", "Examples of agent-only knowledge, one per frequent newcomer need (seeded random draw "
                 "among agent-only units of at most 60 words without code blocks; text shortened). None of it "
                 "appears in the repository's README or CONTRIBUTING.", "tab:examples",
                 r"@{}p{0.17\linewidth}p{0.22\linewidth}p{0.57\linewidth}@{}",
                 r"Newcomer need & Repository (file), section & Agent-file text", rows)
    return body.replace(r"\small", r"\footnotesize", 1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    f = facts()
    written = []
    for name, fn in (("rq1_headline", rq1_headline), ("rq1_categories", rq1_categories), ("rq2_needs", rq2_needs),
                     ("rq2_barriers", rq2_barriers), ("rq3", rq3), ("sensitivity", sensitivity),
                     ("provenance", provenance), ("flow", flow), ("corpus", corpus), ("reliability", reliability),
                     ("examples", examples)):
        (OUT / f"{name}.tex").write_text(fn(f) or "% not available\n")
        written.append(name)
    print(f"wrote {len(written)} tables to {OUT}: {', '.join(written)}")


if __name__ == "__main__":
    main()
