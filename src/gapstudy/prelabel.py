"""Phase 4: LLM pre-labels for instruction categories (codebook dimension A only).

Coverage labels are never pre-labelled: they are the gold standard the RQ3
detector is evaluated against. Works with any OpenAI-compatible chat endpoint,
e.g. an open-source model served by vLLM, Ollama or llama.cpp:

    python -m gapstudy.prelabel --base-url http://localhost:8000/v1 --model <name> [--limit 20]

Appends to coding/prelabels.csv and skips units already pre-labelled.
"""

from __future__ import annotations

import argparse
import json
import os
import re

import pandas as pd
import requests
from tqdm import tqdm

from gapstudy.github_client import PROJECT_ROOT

CODING = PROJECT_ROOT / "coding"
PROCESSED = PROJECT_ROOT / "data" / "processed"
JSON_OBJECT = re.compile(r"\{.*\}", re.S)


def system_prompt(codebook: dict) -> str:
    cats = "\n".join(f"- {k}: {v['definition']}" for k, v in codebook["categories"].items()
                     if not k.startswith("_"))
    return (
        "You classify one section of a repository's AI coding-agent context file (e.g. CLAUDE.md, "
        "AGENTS.md) into instruction categories. A section can belong to several categories.\n\n"
        f"Categories:\n{cats}\n\n"
        "Rules: documentation-related coding conventions are implementation_details; Git, commit and "
        "review practice is development_process; build or test commands inside a checklist still "
        "count as build_run / test.\n\n"
        'Answer with JSON only: {"categories": ["<key>", ...]}'
    )


def user_prompt(unit: pd.Series) -> str:
    heading = unit.heading_path if isinstance(unit.heading_path, str) and unit.heading_path else "(no heading)"
    return f"Section heading: {heading}\n\nSection text:\n{unit.text}"


def parse(content: str, valid: set[str]) -> list[str]:
    match = JSON_OBJECT.search(content or "")
    if not match:
        return []
    try:
        cats = json.loads(match.group()).get("categories", [])
    except (json.JSONDecodeError, AttributeError):
        return []
    return [c for c in dict.fromkeys(cats) if c in valid]


def classify(session: requests.Session, base_url: str, model: str, system: str, user: str,
             api_key: str | None = None) -> str:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    r = session.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, timeout=300, json={
        "model": model, "temperature": 0,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    })
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--limit", type=int, help="only the first N queued units (for a trial run)")
    args = ap.parse_args()

    codebook = json.loads((CODING / "codebook.json").read_text())
    valid = {k for k in codebook["categories"] if not k.startswith("_")}
    queue = pd.read_csv(CODING / "queue.csv")
    units = pd.read_csv(PROCESSED / "units.csv").set_index("unit_id")
    out = CODING / "prelabels.csv"
    done = set(pd.read_csv(out).unit_id) if out.exists() else set()
    todo = [u for u in queue.unit_id if u not in done][: args.limit]

    system, session = system_prompt(codebook), requests.Session()
    for unit_id in tqdm(todo):
        raw = classify(session, args.base_url, args.model, system, user_prompt(units.loc[unit_id]),
                       os.environ.get("LLM_API_KEY"))
        row = pd.DataFrame([{"unit_id": unit_id, "categories": json.dumps(parse(raw, valid)),
                             "model": args.model, "raw": raw}])
        row.to_csv(out, mode="a", header=not out.exists(), index=False)
    print(f"pre-labelled {len(todo)} units -> {out}")


if __name__ == "__main__":
    main()
