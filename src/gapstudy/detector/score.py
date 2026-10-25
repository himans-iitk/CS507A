"""Phase 6: score every agent-file unit against its repo's README and CONTRIBUTING.

    python -m gapstudy.detector.score --matcher tfidf
    python -m gapstudy.detector.score --matcher BAAI/bge-base-en-v1.5 [--device cuda]

Writes data/processed/scores/<matcher>.csv with, per agent unit:
    unit_max   max cosine between the whole unit and any whole human section
    item_mean  mean over the unit's items of each item's best match among human items
    item_max   the per-item best matches (JSON), so item-level thresholds can be tuned later
    top        the 5 best-matching human sections (JSON): evidence ranking and LLM candidates
No labels are used here; thresholds are tuned in gapstudy.detector.evaluate.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from tqdm import tqdm

from gapstudy.detector.items import split_items
from gapstudy.detector.matchers import make, similarity
from gapstudy.github_client import PROJECT_ROOT

PROCESSED = PROJECT_ROOT / "data" / "processed"
OUT = PROCESSED / "scores"
TOP_K = 5


def load_units() -> tuple[pd.DataFrame, pd.DataFrame]:
    units = pd.read_csv(PROCESSED / "units.csv")
    units = units[~units.toc].copy()
    units["items"] = units.text.map(split_items)
    return units[units.doc == "agent"], units[units.doc != "agent"]


def flatten(df: pd.DataFrame) -> pd.DataFrame:
    return df[["unit_id", "repo", "items"]].explode("items").dropna(subset=["items"]).rename(columns={"items": "item"})


def score_repo(agent, human, a_unit, h_unit, a_items, h_items) -> list[dict]:
    """Vectors are row-aligned with agent/human (units) and their flattened items."""
    rows = []
    unit_sim = similarity(a_unit, h_unit) if len(human) else np.zeros((len(agent), 0))
    item_sim = similarity(a_items["vec"], h_items["vec"]) if len(h_items["owner"]) else None
    h_ids = human.unit_id.to_numpy()
    for i, unit_id in enumerate(agent.unit_id):
        mine = a_items["owner"] == unit_id
        if item_sim is not None and mine.any():
            per_item = item_sim[mine]                                   # agent items x human items
            item_best = per_item.max(axis=1)
            # a human section's score: best of section-level and any of its items' similarity
            by_section = pd.Series(per_item.max(axis=0)).groupby(h_items["owner"]).max()
            section_score = np.maximum(unit_sim[i], by_section.reindex(h_ids).fillna(0).to_numpy())
        else:
            item_best, section_score = np.zeros(1), unit_sim[i] if len(human) else np.zeros(0)
        order = np.argsort(-section_score)[:TOP_K]
        rows.append({
            "unit_id": unit_id,
            "unit_max": float(unit_sim[i].max()) if len(human) else 0.0,
            "item_mean": float(item_best.mean()),
            "item_max": json.dumps([round(float(x), 4) for x in item_best]),
            "top": json.dumps([[h_ids[j], round(float(section_score[j]), 4)] for j in order]),
        })
    return rows


def run(matcher_name: str, device: str | None = None) -> pd.DataFrame:
    agent, human = load_units()
    a_items, h_items = flatten(agent), flatten(human)
    corpus = list(agent.text) + list(human.text) + list(a_items.item) + list(h_items.item)
    matcher = make(matcher_name, corpus=corpus) if matcher_name == "tfidf" else make(matcher_name, device=device)

    vec = {
        "a_unit": matcher.encode(list(agent.text), role="query"),
        "h_unit": matcher.encode(list(human.text), role="doc"),
        "a_item": matcher.encode(list(a_items.item), role="query"),
        "h_item": matcher.encode(list(h_items.item), role="doc"),
    }
    pos = {name: {r: np.flatnonzero(df.repo.to_numpy() == r) for r in df.repo.unique()}
           for name, df in (("a_unit", agent), ("h_unit", human), ("a_item", a_items), ("h_item", h_items))}
    empty = np.array([], dtype=int)

    rows = []
    for repo in tqdm(agent.repo.unique(), desc=matcher_name, mininterval=10):
        ia, ih = pos["a_unit"][repo], pos["h_unit"].get(repo, empty)
        ja, jh = pos["a_item"].get(repo, empty), pos["h_item"].get(repo, empty)
        rows += score_repo(
            agent.iloc[ia], human.iloc[ih], vec["a_unit"][ia], vec["h_unit"][ih],
            {"vec": vec["a_item"][ja], "owner": a_items.unit_id.to_numpy()[ja]},
            {"vec": vec["h_item"][jh], "owner": h_items.unit_id.to_numpy()[jh]},
        )
    out = pd.DataFrame(rows)
    out.insert(1, "matcher", matcher_name)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matcher", required=True, help="'tfidf' or a sentence-transformers model id")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()
    scores = run(args.matcher, args.device)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{args.matcher.replace('/', '__')}.csv"
    scores.to_csv(path, index=False)
    print(f"{len(scores)} agent units scored -> {path}")
    print(scores[["unit_max", "item_mean"]].describe().round(3).to_string())


if __name__ == "__main__":
    main()
