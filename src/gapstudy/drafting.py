"""AI-drafted labels: bundles for drafting, and validated storage of drafts.

    python -m gapstudy.drafting show <owner/repo>        # print the units to draft + human sections
    python -m gapstudy.drafting add <drafts.json>         # validate and append to coding/drafts.jsonl
    python -m gapstudy.drafting status                    # drafted vs queued, per set

A draft is one JSON object per unit:
    {"unit_id", "coverage", "categories", "evidence", "need", "barriers", "flags", "rationale"}
Drafts are suggestions shown to verifiers; they never count as final labels.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from gapstudy.github_client import PROJECT_ROOT
from gapstudy.labels import CODING

PROCESSED = PROJECT_ROOT / "data" / "processed"
DRAFTER = "claude-opus-5.5"


def load_drafts(coding_dir: Path = CODING) -> dict[str, dict]:
    path = coding_dir / "drafts.jsonl"
    out = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                out[d["unit_id"]] = d
    return out


def validate(draft: dict, codebook: dict, units: pd.DataFrame, queued: set[str]) -> list[str]:
    errs = []
    keys = lambda section: {k for k in codebook[section] if not k.startswith("_")}
    uid = draft.get("unit_id")
    if uid not in queued:
        return [f"{uid}: not in the coding queue"]
    if draft.get("coverage") not in keys("coverage"):
        errs.append(f"{uid}: bad coverage {draft.get('coverage')!r}")
    if bad := set(draft.get("categories", [])) - keys("categories"):
        errs.append(f"{uid}: unknown categories {sorted(bad)}")
    repo = units.loc[uid, "repo"]
    human = set(units[(units.repo == repo) & (units.doc != "agent")].index)
    if bad := set(draft.get("evidence", [])) - human:
        errs.append(f"{uid}: evidence not in this repo's human docs {sorted(bad)}")
    gap = draft.get("coverage") in ("agent_only", "partial")
    if gap and draft.get("need") not in keys("needs"):
        errs.append(f"{uid}: gap units need a valid 'need'")
    if not gap and (draft.get("need") or draft.get("barriers")):
        errs.append(f"{uid}: need/barriers only for agent_only or partial")
    if bad := set(draft.get("barriers", [])) - keys("barriers"):
        errs.append(f"{uid}: unknown barriers {sorted(bad)}")
    if draft.get("coverage") in ("partial", "shared") and not draft.get("evidence"):
        errs.append(f"{uid}: partial/shared needs evidence")
    if bad := set(draft.get("flags", [])) - set(codebook["flags"]):
        errs.append(f"{uid}: unknown flags {sorted(bad)}")
    if not str(draft.get("rationale", "")).strip():
        errs.append(f"{uid}: rationale required")
    return errs


def add(path: Path, coding_dir: Path = CODING, processed: Path = PROCESSED) -> int:
    codebook = json.loads((coding_dir / "codebook.json").read_text())
    units = pd.read_csv(processed / "units.csv").set_index("unit_id")
    queued = set(pd.read_csv(coding_dir / "queue.csv").unit_id)
    drafts = json.loads(Path(path).read_text())
    errs = [e for d in drafts for e in validate(d, codebook, units, queued)]
    if errs:
        raise SystemExit("Not added:\n  " + "\n  ".join(errs))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with (coding_dir / "drafts.jsonl").open("a") as f:
        for d in drafts:
            rec = {"unit_id": d["unit_id"], "coverage": d["coverage"], "categories": d.get("categories", []),
                   "evidence": d.get("evidence", []), "need": d.get("need"), "barriers": d.get("barriers", []),
                   "flags": d.get("flags", []), "rationale": d["rationale"].strip(),
                   "drafter": DRAFTER, "codebook_version": codebook["version"], "drafted_at": now}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return len(drafts)


def show(repo: str, coding_dir: Path = CODING, processed: Path = PROCESSED) -> str:
    units = pd.read_csv(processed / "units.csv")
    queue = pd.read_csv(coding_dir / "queue.csv")
    todo = queue[queue.repo == repo]
    agent = units.set_index("unit_id").loc[todo.unit_id]
    human = units[(units.repo == repo) & (units.doc != "agent")]
    head = lambda h: h if isinstance(h, str) and h else "(no heading)"
    data_uri = re.compile(r"data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+")
    out = [f"# {repo} · {todo.tool.iloc[0]} · {todo.set.iloc[0]} set · {len(todo)} units to draft", "",
           "## HUMAN DOCS (README, CONTRIBUTING)"]
    for h in human.itertuples():
        out += [f"[{h.unit_id}] {head(h.heading_path)}", data_uri.sub("data:…", h.text.strip()), ""]
    out.append("## AGENT UNITS TO DRAFT")
    for uid, a in agent.iterrows():
        out += [f"<<{uid}>> {head(a.heading_path)}", a.text.strip(), ""]
    return "\n".join(out)


def outline(repo: str, coding_dir: Path = CODING, processed: Path = PROCESSED) -> str:
    """Agent units in full; human docs as a section list (id, heading, words)."""
    units = pd.read_csv(processed / "units.csv")
    queue = pd.read_csv(coding_dir / "queue.csv")
    todo = queue[queue.repo == repo]
    agent = units.set_index("unit_id").loc[todo.unit_id]
    human = units[(units.repo == repo) & (units.doc != "agent")]
    head = lambda h: h if isinstance(h, str) and h else "(no heading)"
    out = [f"# {repo} · {todo.tool.iloc[0]} · {todo.set.iloc[0]} · {len(todo)} units", "## HUMAN SECTIONS"]
    out += [f"[{h.unit_id.split('::', 1)[1]}] {head(h.heading_path)} ({h.words}w)" for h in human.itertuples()]
    out.append("## AGENT UNITS")
    for uid, a in agent.iterrows():
        out += [f"<<{uid.split('::', 1)[1]}>> {head(a.heading_path)}", a.text.strip(), ""]
    return "\n".join(out)


def search(repo: str, pattern: str, context: int = 160, processed: Path = PROCESSED) -> str:
    """Human-doc passages matching a regex (case-insensitive), with section ids."""
    units = pd.read_csv(processed / "units.csv")
    human = units[(units.repo == repo) & (units.doc != "agent")]
    rx = re.compile(pattern, re.I)
    out = []
    for h in human.itertuples():
        for m in rx.finditer(h.text):
            a, b = max(0, m.start() - context), min(len(h.text), m.end() + context)
            out.append(f"[{h.unit_id.split('::', 1)[1]}] …{h.text[a:b].replace(chr(10), ' ')}…")
    return "\n".join(out) or f"no match for /{pattern}/"


def status(coding_dir: Path = CODING) -> pd.DataFrame:
    queue = pd.read_csv(coding_dir / "queue.csv")
    drafted = set(load_drafts(coding_dir))
    queue["drafted"] = queue.unit_id.isin(drafted)
    return queue.groupby("set").drafted.agg(["sum", "size"]).rename(columns={"sum": "drafted", "size": "queued"})


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show").add_argument("repo")
    sub.add_parser("outline").add_argument("repo")
    s = sub.add_parser("search")
    s.add_argument("repo")
    s.add_argument("patterns", nargs="+")
    sub.add_parser("add").add_argument("path", type=Path)
    sub.add_parser("status")
    args = ap.parse_args()
    if args.cmd == "show":
        sys.stdout.write(show(args.repo) + "\n")
    elif args.cmd == "outline":
        sys.stdout.write(outline(args.repo) + "\n")
    elif args.cmd == "search":
        for p in args.patterns:
            print(f"--- /{p}/\n{search(args.repo, p)}")
    elif args.cmd == "add":
        print(f"added {add(args.path)} drafts")
    else:
        print(status().to_string())


if __name__ == "__main__":
    main()
