"""Phase 6: LLM coverage judgements for agent units (the "embeddings + LLM" matcher).

For each queued agent unit, the LLM sees the unit and the TOP_K human sections the
embedding matcher ranked highest, and answers agent_only / partial / shared. The
evaluation decides where to trust it (only for borderline embedding scores, with the
band tuned on dev). Uses any OpenAI-compatible endpoint, e.g. vLLM:

    python -m gapstudy.detector.llm_judge --scores data/processed/scores/<matcher>.csv \
        --base-url http://127.0.0.1:8000/v1 --model <name> [--limit 20]

Appends to data/processed/llm/<model>__<matcher>.csv and skips units already judged.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from gapstudy.github_client import PROJECT_ROOT
from gapstudy.prelabel import classify

PROCESSED = PROJECT_ROOT / "data" / "processed"
OUT_DIR = PROCESSED / "llm"
CODING = PROJECT_ROOT / "coding"
TOP_K = 5
MAX_WORDS = 400
LABELS = ("agent_only", "partial", "shared")
JSON_OBJECT = re.compile(r"\{.*\}", re.S)

SYSTEM = (
    "You compare a section of a repository's AI-agent context file (e.g. CLAUDE.md) with sections of the "
    "same repository's human documentation (README, CONTRIBUTING). Decide whether the KNOWLEDGE in the agent "
    "section (facts, commands, rules) is stated in the human sections. Paraphrases count; merely mentioning "
    "the same topic without the specifics does not; links to other places do not.\n"
    "- shared: every actionable fact, command or rule is in the human sections\n"
    "- partial: some of it is, or it is covered less specifically\n"
    "- agent_only: none of it is\n"
    'Answer with JSON only: {"coverage": "agent_only" | "partial" | "shared", "covered_by": [section numbers]}'
)


def clip(text: str, n: int = MAX_WORDS) -> str:
    words = text.split()
    return text if len(words) <= n else " ".join(words[:n]) + " …"


def prompt(unit: pd.Series, candidates: list[pd.Series]) -> str:
    head = lambda u: u.heading_path if isinstance(u.heading_path, str) and u.heading_path else "(no heading)"
    parts = [f"AGENT SECTION ({head(unit)}):\n{clip(unit.text)}", "", "HUMAN DOCUMENTATION SECTIONS:"]
    for i, c in enumerate(candidates, 1):
        parts += [f"[{i}] {c.doc} · {head(c)}:\n{clip(c.text)}", ""]
    if not candidates:
        parts.append("(none)")
    return "\n".join(parts)


def parse(content: str) -> tuple[str | None, list[int]]:
    m = JSON_OBJECT.search(content or "")
    if not m:
        return None, []
    try:
        data = json.loads(m.group())
    except json.JSONDecodeError:
        return None, []
    cov = data.get("coverage")
    covered = [int(i) for i in data.get("covered_by", []) if str(i).isdigit()]
    return (cov if cov in LABELS else None), covered


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True, type=Path)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    scores = pd.read_csv(args.scores).set_index("unit_id")
    units = pd.read_csv(PROCESSED / "units.csv").set_index("unit_id", drop=False)
    queue = pd.read_csv(CODING / "queue.csv")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.model.replace('/', '__')}__{args.scores.stem}.csv"
    done = set(pd.read_csv(out).unit_id) if out.exists() else set()
    todo = [u for u in queue.unit_id if u not in done and u in scores.index][: args.limit]

    session, key = requests.Session(), os.environ.get("LLM_API_KEY")

    def judge(unit_id: str) -> dict:
        cand_ids = [u for u, _ in json.loads(scores.loc[unit_id, "top"])][:TOP_K]
        raw = classify(session, args.base_url, args.model, SYSTEM,
                       prompt(units.loc[unit_id], [units.loc[c] for c in cand_ids]), key)
        cov, covered = parse(raw)
        evidence = [cand_ids[i - 1] for i in covered if 1 <= i <= len(cand_ids)]
        return {"unit_id": unit_id, "llm_coverage": cov, "llm_evidence": json.dumps(evidence),
                "model": args.model, "raw": raw}

    with ThreadPoolExecutor(args.workers) as pool:
        for row in tqdm(pool.map(judge, todo), total=len(todo)):
            pd.DataFrame([row]).to_csv(out, mode="a", header=not out.exists(), index=False)
    print(f"judged {len(todo)} units -> {out}")


if __name__ == "__main__":
    main()
