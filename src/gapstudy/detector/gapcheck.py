"""gapcheck: list agent-file sections a repository's human docs do not cover.

    gapcheck path/to/repo [--json] [--matcher M --threshold T]

Finds CLAUDE.md, AGENTS.md and .github/copilot-instructions.md, compares each
section with README and CONTRIBUTING (GitHub's lookup order: .github/, root,
docs/), and labels it agent-only / partial / shared with the matcher and
thresholds in detector/config.json (written by gapstudy.detector.evaluate).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from gapstudy.detector.evaluate import CONFIG, predict3
from gapstudy.detector.items import split_items
from gapstudy.detector.matchers import make
from gapstudy.detector.score import score_repo
from gapstudy.snapshot import DOC_DIRS, DOC_PATTERNS
from gapstudy.units import features, split

AGENT_FILES = ("CLAUDE.md", "AGENTS.md", ".github/copilot-instructions.md")


def find_ci(root: Path, rel: str) -> Path | None:
    """Case-insensitive lookup of a relative path."""
    cur = root
    for part in rel.split("/"):
        match = next((p for p in cur.iterdir() if p.name.lower() == part.lower()), None) if cur.is_dir() else None
        if match is None:
            return None
        cur = match
    return cur if cur.is_file() else None


def find_doc(root: Path, kind: str) -> Path | None:
    for d in DOC_DIRS:
        folder = root / d if d else root
        if folder.is_dir():
            for p in sorted(folder.iterdir()):
                if p.is_file() and DOC_PATTERNS[kind].match(p.name):
                    return p
    return None


def units_of(path: Path, doc: str) -> list[dict]:
    rows = []
    for u in split(path.read_text(errors="replace")):
        if not features(u.heading, u.text)["toc"]:
            rows.append({"unit_id": f"{doc}::{u.n}", "doc": doc, "heading_path": u.heading_path,
                         "text": u.text, "items": split_items(u.text)})
    return rows


def check(root: Path, config: dict) -> pd.DataFrame:
    agent = [u for rel in AGENT_FILES if (p := find_ci(root, rel)) for u in units_of(p, rel)]
    human = [u for kind in ("readme", "contributing") if (p := find_doc(root, kind))
             for u in units_of(p, p.relative_to(root).as_posix())]
    if not agent:
        raise SystemExit(f"No agent context file ({', '.join(AGENT_FILES)}) in {root}")
    agent, human = pd.DataFrame(agent), pd.DataFrame(human, columns=["unit_id", "doc", "heading_path", "text", "items"])
    a_items = agent[["unit_id", "items"]].explode("items").dropna()
    h_items = human[["unit_id", "items"]].explode("items").dropna()

    corpus = list(agent.text) + list(human.text) + list(a_items["items"]) + list(h_items["items"])
    m = make(config["matcher"], corpus=corpus)
    enc = lambda texts, role: m.encode(list(texts), role=role) if len(texts) else np.zeros((0, 1))
    rows = score_repo(agent, human, enc(agent.text, "query"), enc(human.text, "doc"),
                      {"vec": enc(a_items["items"], "query"), "owner": a_items.unit_id.to_numpy()},
                      {"vec": enc(h_items["items"], "doc"), "owner": h_items.unit_id.to_numpy()})
    out = agent[["unit_id", "doc", "heading_path"]].merge(pd.DataFrame(rows), on="unit_id")
    variant = config["variant"]
    if variant.startswith("item_cov@"):
        tau = float(variant.split("@")[1])
        out["score"] = out.item_max.map(lambda s: float(np.mean([x >= tau for x in json.loads(s)])))
    else:
        out["score"] = out[variant]
    out["label"] = predict3(out.score.to_numpy(), config["t1"], config["t2"])
    out.loc[out.score < config["threshold"], "label"] = "agent_only"
    out["best_match"] = out.top.map(lambda t: json.loads(t)[0][0] if json.loads(t) else "")
    return out[["doc", "heading_path", "label", "score", "best_match"]]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo", type=Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--matcher")
    ap.add_argument("--threshold", type=float, help="agent-only below this score (overrides config)")
    args = ap.parse_args()

    config = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    if args.matcher:
        config["matcher"] = args.matcher
    if args.threshold is not None:
        config.update(threshold=args.threshold, t1=args.threshold, t2=config.get("t2", args.threshold),
                      variant=config.get("variant", "item_mean"))
    if not {"matcher", "threshold", "variant"} <= config.keys():
        raise SystemExit("No detector/config.json yet (run gapstudy.detector.evaluate after coding), "
                         "or pass --matcher and --threshold.")
    result = check(args.repo, config)
    if args.json:
        print(result.to_json(orient="records", indent=2))
        return
    if config.get("provisional"):
        print("note: thresholds are provisional (tuned before the labels were frozen)", file=sys.stderr)
    counts = result.label.value_counts().to_dict()
    print(f"{len(result)} agent sections: {counts.get('agent_only', 0)} agent-only, "
          f"{counts.get('partial', 0)} partial, {counts.get('shared', 0)} shared\n")
    for r in result.sort_values("score").itertuples():
        head = r.heading_path or "(no heading)"
        print(f"  {r.label:<10} {r.score:5.2f}  {r.doc} › {head}" + (f"   ~ {r.best_match}" if r.label != "agent_only" else ""))


if __name__ == "__main__":
    main()
