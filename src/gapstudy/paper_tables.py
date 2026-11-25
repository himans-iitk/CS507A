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
    return f"{100 * x:.1f}" if pd.notna(x) else "n/a"


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
    return table("table*", "RQ1: Coverage of a repository's agent-file sections by its README and "
                 "CONTRIBUTING. Each value is the mean share of a repository's labelled knowledge sections (\\%), "
                 "with a 95\\% confidence interval from 1{,}000 bootstrap samples of repositories. The \\emph{All} "
                 "column weights each file type by how common it is among eligible files. Agent-directed sections "
                 "are excluded, so the \\nReposNoKnowledge{} repositories whose labelled sections are all "
                 "agent-directed are not counted (\\nRepoKnowledge{} of \\nSampleRepos{}).", "tab:rq1", "lrrrr",
                 r"Coverage & All & \texttt{CLAUDE.md} & \texttt{AGENTS.md} & Copilot", rows)


def rq1_categories(f: dict) -> str:
    gee = f["gee"]
    names = {v: k for k, v in gee.term.items()}
    rows = []
    for r in f["categories"].itertuples():
        key = names.get(r.category)
        if key is not None and key in gee.index:
            g = gee.loc[key]
            star = "$^{**}$" if g.p < 0.05 / len(gee) else ("$^{*}$" if g.p < 0.05 else "")
            odds = f"{g.odds_ratio:.2f}{star}"
        else:
            odds = "n/a"
        rows.append(f"{tex(r.category)} & {r.units} & {p1(r.agent_only)} & {odds} " + r"\\")
    body = table("table", "Agent-only share by instruction category. \\emph{Sections}: labelled sections (raw "
                 "count); \\emph{Agent-only}: \\% of them, weighted for the limit of 10 labelled sections per "
                 "repository. The odds ratio (GEE, clustered by repository) compares sections with the category to "
                 "all other sections; below 1 means less often agent-only. $^{*}$~$p < 0.05$ unadjusted; "
                 "$^{**}$~significant after Bonferroni correction for \\geeNTerms{} terms. A section can have "
                 "several categories. Shares for categories with few sections are descriptive.",
                 "tab:rq1cat", "@{}lrrr@{}", r"Category & Sections & Agent-only & Odds ratio", rows)
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
    return table("table", "RQ2: The newcomer needs~\\cite{dagenais2010landscape} that the missing knowledge "
                 "serves. Counts are gap sections (agent-only or partially covered, raw counts); shares are \\% of gap "
                 "sections, weighted for the limit of 10 labelled sections per repository, so a group's share can "
                 "differ slightly from the sum of its rounded rows. Needs were labelled only for gap sections.",
                 "tab:rq2needs", "lrr", r"Need & Sections & Share", rows)


def rq2_barriers(f: dict) -> str:
    rows = [rf"{tex(r.barrier)} & {r.units} & {p1(r.share_of_gap_units)} \\"
            for r in f["barriers"].itertuples() if r.group != "—"]
    note = ((f"No barrier was coded for {p1(f['no_barrier_share'])}\\% of gap units. " if f["no_barrier_share"] > 0 else "")
            + "A section can ease several barriers.")
    return table("table", "RQ2: The newcomer barriers~\\cite{steinmacher2015barriers} that the missing knowledge "
                 "would ease, named as in the source (gap sections, raw counts, and weighted \\% of gap sections).", "tab:rq2bar", "p{0.62\\linewidth}rr",
                 r"Barrier & Sections & Share", rows, note)


def rq3(f: dict) -> str:
    rows = []
    short = {"tfidf": "TF-IDF", "sentence-transformers/all-MiniLM-L6-v2": "MiniLM-L6",
             "BAAI/bge-base-en-v1.5": "bge-base", "Qwen/Qwen3-Embedding-0.6B": "Qwen3-Emb-0.6B"}
    for r in f["detector"].to_dict("records"):
        name = tex(short.get(r["matcher"], r["matcher"].split("/")[-1]))
        name = rf"\textbf{{{name}}}" if r["matcher"] == f["detector_best"]["matcher"] else name
        rows.append(f"{name} & {r['precision']:.2f} & {r['recall']:.2f} & {r['f1']:.2f} & {r['auc']:.2f} & "
                    f"{r['macro_f1']:.2f} & {r['retrieval_hit@1']:.2f}/{r['retrieval_hit@5']:.2f} " + r"\\")
        lo_f, hi_f = (float(x) for x in str(r["f1_ci"]).strip("()").split(","))
        lo_a, hi_a = (float(x) for x in str(r["auc_ci"]).strip("()").split(","))
        rows.append(rf"\quad{{\scriptsize\itshape {tex(r['variant'].replace('_', ' '))}}} & & & {{\scriptsize[{lo_f:.2f}, {hi_f:.2f}]}} & "
                    rf"{{\scriptsize[{lo_a:.2f}, {hi_a:.2f}]}} & & \\")
    for r in f["detector_llm"].to_dict("records"):
        rows.append(f"{tex(r['matcher'])} ({tex(r.get('mode', 'LLM'))}) & {r['precision']:.2f} & {r['recall']:.2f} & "
                    f"{r['f1']:.2f} & n/a & {r['macro_f1']:.2f} & n/a " + r"\\")
    bl = f.get("baseline")
    if bl and bl["n"]:
        rows.append(r"\midrule")
        rows.append(rf"\emph{{All agent-only}} & {bl['precision']:.2f} & {bl['recall']:.2f} & {bl['f1']:.2f} & "
                    rf"{bl['auc']:.2f} & n/a & n/a \\")
    b = f["detector_best"]
    body = table("table", "RQ3: Detection of agent-only sections in the test repositories "
                 f"({format(int(b['n_test']), ',').replace(',', '{,}')} sections). P, R, F1: precision, recall and F1 for agent-only. "
                 "AUC: area under the receiver operating characteristic curve. Mac.\\,F1: macro F1 over agent-only, "
                 "partial and shared. @1/@5: hit@1 and hit@5 (Section~\\ref{sec:detector}). Brackets: 95\\% "
                 "repository-bootstrap intervals. Italics: the score chosen on the development set; bold: the "
                 "selected matcher. \\emph{All agent-only}: every section labelled agent-only.", "tab:rq3", "@{}lrrrrrr@{}",
                 r"Matcher & P & R & F1 & AUC & Mac.\,F1 & @1/@5", rows)
    return body.replace(r"\small", r"\small\setlength{\tabcolsep}{3.5pt}", 1)


SENS_NAMES = {"all coded repos (primary)": "All labelled repositories (primary)",
              "without unedited /init files": r"Without unedited \texttt{/init} files",
              "without stub CONTRIBUTING": "Without stub CONTRIBUTING files",
              "without links_out units": "Without link-only sections",
              "only AI-drafted repos (pilot + main)": "Labelled from LLM drafts (pilot, main)",
              "only blind-coded repos (reliability set)": "Labelled blind (reliability set)"}


def sensitivity(f: dict) -> str:
    rows = []
    for r in f["sensitivity"].itertuples():
        if r.variant.startswith("only ") and r"\midrule" not in rows:
            rows.append(r"\midrule")  # rule before the coding-mode split
        rows.append(rf"{SENS_NAMES.get(r.variant, tex(r.variant))} & {r.repos} & "
                    + p1(r.agent_only) + rf" & {{\scriptsize[{p1(r.lo)}, {p1(r.hi)}]}} \\")
    return table("table", "How the agent-only share (\\%, mean over repositories, post-stratified) changes "
                 "when we leave out parts of the data, with 95\\% repository-bootstrap intervals. The last two rows "
                 "split the sample by how the labels were made; they differ in repositories as well as in labelling "
                 "mode.", "tab:sens", "@{}lrrr@{}", r"Variant & Repos & Agent-only & 95\% CI", rows).replace(
                     r"\small", r"\small\setlength{\tabcolsep}{4pt}", 1)


def provenance(f: dict) -> str:
    if "provenance" not in f:
        return ""
    p = f["provenance"]
    cols = [("draft_accepted", "Kept"), ("draft_details_edited", "Edited"),
            ("draft_corrected", "Corrected"), ("blind", "Blind")]
    cols = [(k, n) for k, n in cols if k in p and p[k].sum()]
    n = lambda x: f"{int(x):,}".replace(",", "{,}")  # noqa: E731
    rows = [f"{tex(s.capitalize())} & " + " & ".join(n(p.loc[s, k]) for k, _ in cols) + r" \\" for s in p.index]
    rows.append(r"\midrule")
    rows.append("Total & " + " & ".join(n(p[k].sum()) for k, _ in cols) + r" \\")
    return table("table", "How the final labels were made in each set: an LLM draft that the author kept "
                 "as it was, kept but edited in other fields, or corrected; or labelled blind with no draft.", "tab:prov",
                 "l" + "r" * len(cols),
                 "Set & " + " & ".join(n for _, n in cols), rows)


def flow(f: dict) -> str:
    """Sampling flow per agent file type, from data/processed/sampling_flow.csv."""
    path = PROJECT_ROOT / "data" / "processed" / "sampling_flow.csv"
    if not path.exists():
        return ""
    fl = pd.read_csv(path)
    names = {"all agent files in package": "Agent files in the dataset",
             "minus repo no longer exists": "Remove deleted repositories", "minus fork": "Remove forks",
             "minus archived": "Remove archived repositories",
             "minus snapshot commit not found": "Remove if snapshot commit not found",
             "minus agent file is a symlink": "Remove symbolic links",
             "minus agent file only links elsewhere": "Remove files that only link",
             "minus agent file not in English": "Remove files not in English",
             "minus copy of another repo's agent file": "Remove copied files",
             "minus no README at snapshot": "Remove if no README",
             "minus no CONTRIBUTING at snapshot": "Remove if no CONTRIBUTING"}
    n = lambda x: f"{int(x):,}".replace(",", "{,}")  # noqa: E731
    rows = [f"{names.get(r.step, tex(r.step))} & {n(r.claude)} & {n(r.agents)} & {n(r[3])} & {n(r.total)} " + r"\\"
            for r in fl.itertuples(index=False)]
    sample = pd.read_csv(path.with_name("sample.csv"), usecols=["tool", "in_sample"])
    per = sample[sample.in_sample].tool.value_counts()
    cells = [per.get(t, 0) for t in ("claude", "agents", "copilot-instructions")]
    rows += [r"\midrule", r"\textbf{Sampled} (one per repository) & " + " & ".join(map(n, cells))
             + f" & {n(sum(cells))} " + r"\\"]
    return table("table", "How we built the sample. Each row gives the number of agent files left after a "
                 "filtering step; the steps are applied in this order.", "tab:flow", "@{}lrrrr@{}",
                 r"Step & \texttt{CLAUDE.md} & \texttt{AGENTS.md} & Copilot & All", rows).replace(
                     r"\small", r"\footnotesize\setlength{\tabcolsep}{3pt}", 1)


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
    return table("table", "The corpus: three documents from each of \\nSampleRepos{} repositories, all from the "
                 "same commit. Medians per document (words, and Flesch Reading Ease~\\cite{flesch1948readability}, "
                 "where higher is easier) and per section (words, and sections per repository).", "tab:corpus",
                 "@{}lrrrrr@{}",
                 r"& \multicolumn{2}{c}{Per document} & \multicolumn{3}{c}{Sections} \\ "
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
    models = ", ".join(rel.get("second_coder_models") or []) or "an LLM"
    who = f"an LLM annotator ({models})" if rel.get("kind") == "human-llm" else "a second coder"
    return table("table", f"Agreement on the reliability set ({rel['units']} sections from {rel['repos']} "
                 f"repositories), labelled blind by the author (rows) and by {who} (columns). Bold cells on the "
                 "diagonal are sections where both chose the same label."
                 + (" This is agreement between a person and an LLM, not between two people."
                    if rel.get("kind") == "human-llm" else ""),
                 "tab:rel", "@{}lrrrrr@{}", r"Author $\downarrow$ / " + second.split()[0] + r" $\rightarrow$ & " +
                 " & ".join(n for _, n in COV) + " & Total", rows).replace(
                     r"\small", r"\small\setlength{\tabcolsep}{3.5pt}", 1)


def latex_text(s: str) -> str:
    """Markdown excerpt -> safe LaTeX: inline code to \\texttt, bold dropped, specials escaped."""
    import re
    s = re.sub(r"\s+", " ", str(s)).strip()
    s = s.replace("**", "").replace(" \u2014 ", ", ").replace("\u2014", ", ").replace("\u2013", " to ")
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
    body = table("table*", "Examples of agent-only knowledge, one for each common newcomer need. They were drawn at "
                 "random from agent-only sections of at most 60 words without code blocks, and shortened. None of "
                 "this appears in the repository's README or CONTRIBUTING.", "tab:examples",
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
