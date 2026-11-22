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
             r"{(b) By instruction category (units)};")
    y -= 0.32
    for r in cats.itertuples():
        shares = [r.agent_only, r.any_gap - r.agent_only, 1 - r.any_gap]
        L.append(rf"\node[font=\scriptsize,text=ink,anchor=east,inner sep=0] at (-0.08,{y:.3f}) "
                 rf"{{{tex(r.category)} \textcolor{{ink!60}}{{({r.units})}}}};")
        L += bar(y, shares, [True, False, False])
        y -= ROW_CM
    L += axis(y + ROW_CM - THICK_CM / 2 - 0.08)

    L += [r"\end{tikzpicture}",
          r"\caption{RQ1: coverage of agent-file knowledge in README and CONTRIBUTING. (a)~Mean share per "
          r"repository; $^{*}$post-stratified to the eligible population (95\% CIs in Table~\ref{tab:rq1}). "
          r"(b)~Share of knowledge units per instruction category (a unit can have several), sorted by the "
          r"agent-only share, which is printed on the bars (\%).}",
          r"\label{fig:rq1}", r"\end{figure}", ""]
    return "\n".join(L)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rq1_coverage.tex").write_text(figure(facts()))
    print(f"wrote {OUT / 'rq1_coverage.tex'}")


if __name__ == "__main__":
    main()
