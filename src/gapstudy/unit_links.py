"""Write a page of direct links to each unit of a coding set (for verifiers).

    python -m gapstudy.unit_links [--set pilot] [--port 8507]

Writes coding/<set>_links.md: one link per unit, grouped by repo, with the
AI draft's coverage so verifiers can see what they are checking.
"""

from __future__ import annotations

import argparse
from urllib.parse import quote

import pandas as pd

from gapstudy.drafting import load_drafts
from gapstudy.labels import CODING
from gapstudy.labeltool.app import persistent_token

COVERAGE = {"agent_only": "agent-only", "partial": "partial", "shared": "shared", "agent_directed": "agent-directed"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="pilot", choices=["pilot", "reliability", "main"])
    ap.add_argument("--port", type=int, default=8507)
    args = ap.parse_args()

    queue = pd.read_csv(CODING / "queue.csv")
    units = queue[queue.set == args.set].sort_values("queue_pos")
    drafts = load_drafts(CODING)
    base = f"http://localhost:{args.port}/?token={persistent_token(CODING)}"
    lines = [f"# {args.set.title()} set: {len(units)} units in {units.repo.nunique()} repos", "",
             "Start the tool first: `.venv/bin/python -m gapstudy.labeltool.app`. Each link opens one unit.", ""]
    for repo, g in units.groupby("repo", sort=False):
        lines += [f"## {repo} ({g.tool.iloc[0]}, {len(g)} units)", ""]
        for i, uid in enumerate(g.unit_id, 1):
            draft = COVERAGE.get(drafts.get(uid, {}).get("coverage"), "no draft")
            lines.append(f"{i}. [{uid.split('::', 1)[1]}]({base}&unit={quote(uid, safe='')}) · draft: {draft}")
        lines.append("")
    out = CODING / f"{args.set}_links.md"
    out.write_text("\n".join(lines))
    print(f"{len(units)} links -> {out}")


if __name__ == "__main__":
    main()
