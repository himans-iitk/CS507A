"""Phase 8: the paper's RQ1 figure as TikZ (paper/figures/rq1_coverage.tex), from the pipeline outputs.

    python -m gapstudy.paper_figures

Drawn in LaTeX so fonts match the paper and no plotting library is needed. One single-column
figure, two panels of 100%-stacked horizontal bars (agent-only | partially covered | shared):
(a) by agent, post-stratified repository means; (b) by instruction category, unit level, sorted
by agent-only share. Colour is an ordinal one-hue blue ramp (darkest = agent-only, the finding),
validated with the dataviz skill's ordinal checks; agent-only shares are printed on the bars.
"""

from __future__ import annotations

from gapstudy.github_client import PROJECT_ROOT
from gapstudy.paper_tables import tex
from gapstudy.summary import facts

OUT = PROJECT_ROOT / "paper" / "figures"
COLORS = {"covA": "184F95", "covP": "3987E5", "covS": "86B6EF", "ink": "3A3A38", "rule": "D6D5D0"}
BAR_CM = 4.4      # length of a 100% bar
ROW_CM = 0.30     # row pitch
THICK_CM = 0.20   # bar thickness (thin marks)
LABEL_MIN = 0.05  # print a share inside a segment only if it is at least this wide


def bar(y: float, shares: list[float], labels: list[bool]) -> list[str]:
    out, x = [], 0.0
    for (color, share), show in zip(zip(("covA", "covP", "covS"), shares), labels):
        w = share * BAR_CM
        if w > 0:
            out.append(rf"\fill[{color}] ({x:.3f},{y - THICK_CM / 2:.3f}) rectangle ({x + w:.3f},{y + THICK_CM / 2:.3f});")
            if show and share >= LABEL_MIN:
                ink = "white" if color != "covS" else "ink"
                out.append(rf"\node[font=\tiny\sffamily,text={ink},inner sep=0] at ({x + w / 2:.3f},{y:.3f}) "
                           rf"{{{100 * share:.0f}}};")
        x += w
    # 1pt surface gaps between segments (white doing the separating)
    x = 0.0
    for share in shares[:-1]:
        x += share * BAR_CM
        out.append(rf"\draw[white,line width=0.9pt] ({x:.3f},{y - THICK_CM / 2 - 0.01:.3f}) -- ({x:.3f},{y + THICK_CM / 2 + 0.01:.3f});")
    return out


def axis(y: float) -> list[str]:
    out = [rf"\draw[rule,line width=0.3pt] (0,{y:.3f}) -- ({BAR_CM},{y:.3f});"]
    for t in (0, 25, 50, 75, 100):
        x = t / 100 * BAR_CM
        out.append(rf"\draw[rule,line width=0.3pt] ({x:.3f},{y:.3f}) -- ({x:.3f},{y - 0.06:.3f});")
        out.append(rf"\node[font=\tiny\sffamily,text=ink,anchor=north,inner sep=1pt] at ({x:.3f},{y - 0.06:.3f}) {{{t}\%}};")
    return out


def figure(f: dict) -> str:
    hl = f["headline"]
    agents = [("All repositories$^{*}$", "overall"), ("\\texttt{CLAUDE.md}", "claude"),
              ("\\texttt{AGENTS.md}", "agents"), ("Copilot", "copilot-instructions")]
    cats = f["categories"].sort_values("agent_only", ascending=False)

    L = [r"\begin{figure}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    L += [rf"\definecolor{{{k}}}{{HTML}}{{{v}}}" for k, v in COLORS.items()]

    # legend, right-aligned with the end of the bars
    y = 0.0
    entries = (("covA", "Agent-only"), ("covP", "Partially covered"), ("covS", "Shared"))
    width = lambda name: 0.28 + 0.115 * len(name)  # noqa: E731  (swatch + text at \scriptsize)
    x = BAR_CM - sum(width(n) for _, n in entries) - 0.3 * (len(entries) - 1)
    for color, name in entries:
        L.append(rf"\fill[{color}] ({x:.2f},{y - 0.07:.2f}) rectangle ({x + 0.22:.2f},{y + 0.07:.2f});")
        L.append(rf"\node[font=\scriptsize\sffamily,text=ink,anchor=west,inner sep=1pt] at ({x + 0.26:.2f},{y:.2f}) {{{name}}};")
        x += width(name) + 0.3

    # (a) by agent
    y = -0.55
    L.append(rf"\node[font=\scriptsize\sffamily\bfseries,text=ink,anchor=west,inner sep=0] at (-3.3,{y:.2f}) {{(a) By agent}};")
    y -= 0.32
    for name, scope in agents:
        shares = [hl[(o, scope)][0] for o in ("agent_only", "partial", "shared")]
        total = sum(shares)
        shares = [s / total for s in shares]
        L.append(rf"\node[font=\scriptsize,text=ink,anchor=east,inner sep=0] at (-0.08,{y:.3f}) {{{name}}};")
        L += bar(y, shares, [True, True, True])
        y -= ROW_CM
    L += axis(y + ROW_CM - THICK_CM / 2 - 0.08)

    # (b) by category
    y -= 0.55
    L.append(rf"\node[font=\scriptsize\sffamily\bfseries,text=ink,anchor=west,inner sep=0] at (-3.3,{y:.2f}) "
             r"{(b) By instruction category (sections)};")
    y -= 0.32
    for r in cats.itertuples():
        shares = [r.agent_only, r.any_gap - r.agent_only, 1 - r.any_gap]
        L.append(rf"\node[font=\scriptsize,text=ink,anchor=east,inner sep=0] at (-0.08,{y:.3f}) "
                 rf"{{{tex(r.category)} \textcolor{{ink!60}}{{({r.units})}}}};")
        L += bar(y, shares, [True, False, False])
        y -= ROW_CM
    L += axis(y + ROW_CM - THICK_CM / 2 - 0.08)

    L += [r"\end{tikzpicture}",
          r"\Description{Two panels of stacked horizontal bars showing, for each agent file type and for each "
          r"instruction category, the shares of agent-file sections that are agent-only, partially covered and "
          r"shared with README and CONTRIBUTING.}",
          r"\caption{RQ1: How much agent-file knowledge is also in README and CONTRIBUTING. (a)~Average share "
          r"per repository; $^{*}$file types weighted by how common they are. (b)~Share of sections in each "
          r"instruction category (a section can have several), weighted for the limit of 10 labelled sections per "
          r"repository and sorted by the agent-only share printed on the bars (\%; values rounded, so a bar's "
          r"labels may not sum to 100).}",
          r"\label{fig:rq1}", r"\end{figure}", ""]
    return "\n".join(L)


def repo_histogram(f: dict) -> str:
    """Repositories by their share of agent-only knowledge (unweighted, knowledge units)."""
    from gapstudy.analysis.rq1 import BINS
    per = f.get("repo_shares")
    if per is None:
        return "% not available\n"
    counts = [int(((per.agent_only > lo) & (per.agent_only <= hi)).sum()) for lo, hi, _ in BINS]
    labels = [lab.replace("%", r"\%").replace("–", " to ") for _, _, lab in BINS]
    W, GAP, H = 1.12, 0.14, 2.2  # bar slot width, gap, plot height (cm)
    top = -(-max(counts) // 20) * 20  # axis ends on a gridline above the tallest bar
    L = [r"\begin{figure}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    L += [rf"\definecolor{{{k}}}{{HTML}}{{{v}}}" for k, v in COLORS.items()]
    width = len(counts) * W
    for t in range(0, top + 1, 20):
        y = t / top * H
        L.append(rf"\draw[rule,line width=0.3pt] (0,{y:.3f}) -- ({width:.3f},{y:.3f});")
        L.append(rf"\node[font=\tiny\sffamily,text=ink,anchor=east,inner sep=1pt] at (-0.05,{y:.3f}) {{{t}}};")
    for i, (c, lab) in enumerate(zip(counts, labels)):
        x0 = i * W + GAP / 2
        h = c / top * H
        if h > 0:
            L.append(rf"\fill[covA] ({x0:.3f},0) rectangle ({x0 + W - GAP:.3f},{h:.3f});")
        L.append(rf"\node[font=\scriptsize\sffamily,text=ink,anchor=south,inner sep=1pt] at ({x0 + (W - GAP) / 2:.3f},{h:.3f}) {{{c}}};")
        L.append(rf"\node[font=\scriptsize\sffamily,text=ink,anchor=north,inner sep=2pt] at ({x0 + (W - GAP) / 2:.3f},0) {{{lab}}};")
    L.append(rf"\draw[ink!70,line width=0.4pt] (0,0) -- ({width:.3f},0);")
    L.append(rf"\node[font=\scriptsize\sffamily,text=ink,anchor=north] at ({width / 2:.3f},-0.38) "
             r"{Share of the repository's agent-file sections that are agent-only};")
    L.append(rf"\node[font=\scriptsize\sffamily,text=ink,rotate=90,anchor=south] at (-0.45,{H / 2:.3f}) {{Repositories}};")
    L += [r"\end{tikzpicture}",
          r"\Description{Histogram of repositories by the share of their labelled agent-file sections that are "
          r"agent-only, in six bins from 0\% to 100\%.}",
          rf"\caption{{How many repositories have how many agent-only sections ({len(per)} repositories, each "
          r"counted once). In the 0\% bar, every labelled section is at least partly in README or CONTRIBUTING; "
          r"in the 100\% bar, none is.}",
          r"\label{fig:repos}", r"\end{figure}", ""]
    return "\n".join(L)


EXAMPLE_UNIT = "microsoft/generative-ai-with-javascript::agent::4"  # test-set section traced in Figure 1
FILE_NAMES = {"claude": "CLAUDE.md", "agents": "AGENTS.md", "copilot-instructions": "copilot-instructions.md"}


def example_facts(unit_id: str = EXAMPLE_UNIT) -> dict | None:
    """Everything Figure 1 says about the worked example, read from the pipeline outputs."""
    import json
    import pandas as pd
    from gapstudy.detector.items import split_items
    root = PROJECT_ROOT
    paths = {"units": root / "data/processed/units.csv", "labels": root / "coding/labels_v1.csv",
             "sample": root / "data/processed/sample.csv", "config": root / "detector/config.json",
             "codebook": root / "coding/codebook.json"}
    if not all(p.exists() for p in paths.values()):
        return None
    units = pd.read_csv(paths["units"]).set_index("unit_id")
    labels = pd.read_csv(paths["labels"]).set_index("unit_id")
    if unit_id not in labels.index:
        return None
    cfg = json.loads(paths["config"].read_text())
    cb = json.loads(paths["codebook"].read_text())
    scores = pd.read_csv(root / "data/processed/scores" / f"{cfg['matcher'].replace('/', '__')}.csv").set_index("unit_id")
    lab, unit = labels.loc[unit_id], units.loc[unit_id]
    repo = unit.repo
    smp = pd.read_csv(paths["sample"])
    row = smp[(smp.repo == repo) & smp.in_sample].iloc[0]
    per_doc = units[units.repo == repo].doc.value_counts()
    best = json.loads(scores.loc[unit_id, "item_max"])
    top_id = json.loads(scores.loc[unit_id, "top"])[0][0]
    score = float(scores.loc[unit_id, cfg["variant"]])
    name = lambda group, key: cb[group].get(key, {}).get("name", key)  # noqa: E731
    return {
        "repo": repo, "file": FILE_NAMES[unit.tool], "stars": int(row.stars), "set": lab["set"],
        "commit": str(row.snapshot_commit)[:7], "date": pd.to_datetime(row.snapshot_date).strftime("%-d %B %Y"),
        "readme": row.readme_path, "contributing": row.contributing_path,
        "n_agent": int(per_doc.get("agent", 0)), "n_readme": int(per_doc.get("README", 0)),
        "n_contrib": int(per_doc.get("CONTRIBUTING", 0)),
        "heading": str(unit.heading_path).split(" > ")[-1], "words": int(unit.words), "text": unit.text,
        "n_items": len(split_items(unit.text)), "item_best": best,
        "coverage": name("coverage", lab.coverage),
        "categories": [name("categories", c) for c in json.loads(lab.categories)],
        "need": name("needs", lab.need), "barriers": [name("barriers", b) for b in json.loads(lab.barriers)],
        "score": score, "threshold": float(cfg["threshold"]), "variant": cfg["variant"].replace("_", " "),
        "matcher": {"tfidf": "TF-IDF"}.get(cfg["matcher"], cfg["matcher"]),
        "predicted_agent_only": score < float(cfg["threshold"]),
        "top_heading": str(units.loc[top_id, "heading_path"]).split(" > ")[-1],
    }


def architecture(e: dict | None) -> str:
    """Figure 1: the method's stages (top) and one real section traced through them (bottom)."""
    import re
    from gapstudy.paper_tables import latex_text
    clean = lambda s: tex(re.sub(r"<[^>]+>", "", str(s)).strip())  # noqa: E731  (drop HTML anchors in headings)
    brk = lambda s: tex(s).replace("/", r"/\allowbreak ")  # noqa: E731  (let long paths wrap in narrow boxes)
    stages = [(r"Agent READMEs dataset", r"\nPackageFiles{} agent files"),
              (r"Same commit", r"README and CONTRIBUTING at the agent file's snapshot commit"),
              (r"Filter and sample", r"\nEligible{} eligible files; \nPerAgent{} per file type; \nSampleRepos{} repositories"),
              (r"Sections", r"split at headings; \nUnits{} sections"),
              (r"Labelling (RQ1, RQ2)", r"up to 10 sections per repository; \nQueued{} labelled"),
              (r"Detector (RQ3)", r"score of each section against the human sections")]
    L = [r"\begin{figure*}[t]", r"\centering",
         r"\begin{tikzpicture}[x=1cm,y=1cm,",
         r"  stage/.style={draw=black!50,fill=black!6,rounded corners=1.5pt,align=center,font=\scriptsize,"
         r"text width=2.5cm,minimum height=1.05cm,inner sep=2pt,anchor=north},",
         r"  ex/.style={draw=black!25,rounded corners=1.5pt,align=left,font=\scriptsize,text width=2.5cm,"
         r"minimum height=2.45cm,inner sep=2.5pt,anchor=north},",
         r"  arr/.style={-{Latex[length=1.6mm]},black!60,line width=0.5pt}]"]
    step = 2.95
    for i, (title, body) in enumerate(stages):
        L.append(rf"\node[stage] (s{i}) at ({i * step:.2f},0) {{\textbf{{{title}}}\\{body}}};")
    for i in range(len(stages) - 1):
        L.append(rf"\draw[arr] (s{i}.east) -- (s{i + 1}.west);")
    if e:
        best = ", ".join(f"{x:.2f}" for x in e["item_best"])
        cmp_ = "<" if e["predicted_agent_only"] else r"\geq"
        verdict = "agent-only" if e["predicted_agent_only"] else "covered"
        correct = "correct" if (e["predicted_agent_only"] == (e["coverage"] == "Agent-only")) else "wrong"
        cells = [
            rf"\texttt{{{tex(e['file'])}}} of the repository {brk(e['repo'])} "
            rf"({e['stars']} stars).",
            rf"Snapshot commit \texttt{{{e['commit']}}} ({e['date']}). Human documents: "
            rf"{tex(e['readme'])} and {brk(e['contributing'])}.",
            rf"Drawn for the \texttt{{{tex(e['file'])}}} group; labelled in the {tex(e['set'])} set, so it is "
            r"part of the RQ3 test data.",
            rf"{e['n_agent']} agent, {e['n_readme']} README and {e['n_contrib']} CONTRIBUTING sections. "
            rf"This one: \emph{{{clean(e['heading'])}}} ({e['words']} words, text below).",
            rf"\textbf{{Coverage:}} {tex(e['coverage'])}. \textbf{{Categories:}} {tex('; '.join(e['categories']))}. "
            rf"\textbf{{Need:}} {tex(e['need'])}. \textbf{{Barrier:}} {tex('; '.join(e['barriers']))}.",
            rf"{e['matcher']}, {e['n_items']} items; best matches {best}. {tex(e['variant']).capitalize()} "
            rf"${e['score']:.3f} {cmp_} {e['threshold']:.3f}$: {verdict} ({correct}). Closest human "
            rf"section: \emph{{{clean(e['top_heading'])}}}."]
        for i, c in enumerate(cells):
            L.append(rf"\node[ex] (e{i}) at ({i * step:.2f},-1.35) {{{c}}};")
            L.append(rf"\draw[black!30,densely dotted,line width=0.5pt] (s{i}.south) -- (e{i}.north);")
        width = (len(stages) - 1) * step + 2.5
        L.append(rf"\node[draw=black!25,fill=black!3,rounded corners=1.5pt,align=left,font=\scriptsize,"
                 rf"text width={width - 0.2:.2f}cm,inner sep=3pt,anchor=north west] at (-1.25,-3.95) "
                 rf"{{\textbf{{Example section}} (\texttt{{{tex(e['file'])}}}, \emph{{{clean(e['heading'])}}}): "
                 rf"{latex_text(e['text'])}}};")
    L += [r"\end{tikzpicture}",
          r"\Description{Six method stages in a row, from the Agent READMEs dataset to the detector, with one "
          r"real agent-file section traced below each stage.}",
          (r"\caption{Overview of the pipeline. Top: the six stages. Bottom: one real section from our data "
           r"traced through every stage" + (f", labelled {e['coverage'].lower()} by the annotator and "
           f"{'predicted' if e['predicted_agent_only'] else 'not predicted'} agent-only by the detector."
           if e else ".") + "}"),
          r"\label{fig:overview}", r"\end{figure*}", ""]
    return "\n".join(L)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "overview.tex").write_text(architecture(example_facts()))
    f = facts()
    (OUT / "rq1_coverage.tex").write_text(figure(f))
    (OUT / "rq1_repos.tex").write_text(repo_histogram(f))
    print(f"wrote {OUT / 'rq1_coverage.tex'} and {OUT / 'rq1_repos.tex'}")


if __name__ == "__main__":
    main()
