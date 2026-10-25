"""Phase 4: decide what gets coded, in which order.

Repos are split into three sets, each stratified by agent:
    pilot        20 repos  coded first while the codebook is refined; the detector's dev set
    reliability  40 repos  coded next, then re-coded blind >= 14 days later (intra-rater kappa)
    main         the rest
Within each repo at most CAP agent units are coded (a seeded random subset of the
codable units); each coded unit carries weight = codable units / coded units, so
repo-level estimates stay unbiased.

    python -m gapstudy.assign [--cap 10] [--seed 507]
Writes coding/assignments.csv (one row per repo) and coding/queue.csv (one row per unit).
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from gapstudy.github_client import PROJECT_ROOT

PROCESSED = PROJECT_ROOT / "data" / "processed"
CODING = PROJECT_ROOT / "coding"
SET_SIZES = {"pilot": 20, "reliability": 40}
STUB_CONTRIBUTING_WORDS = 50


def stratified_sets(repos: pd.DataFrame, rng: np.random.Generator) -> pd.Series:
    """Assign pilot/reliability/main, spreading each set evenly over agents."""
    order = repos.sample(frac=1, random_state=rng.integers(2**32))
    order["k"] = order.groupby("tool").cumcount()  # position within its agent
    order = order.sort_values(["k", "tool"])        # interleave agents: c, a, p, c, a, p, ...
    sets, start = pd.Series("main", index=order.index), 0
    for name, size in SET_SIZES.items():
        sets.iloc[start:start + size] = name
        start += size
    return sets.reindex(repos.index)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=10)
    ap.add_argument("--seed", type=int, default=507)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    units = pd.read_csv(PROCESSED / "units.csv")
    manifest = pd.read_csv(PROCESSED / "corpus_manifest.csv")
    manifest = manifest[manifest.in_sample]

    repos = manifest[["repo", "tool", "init_unedited", "contributing_words", "readme_words"]].copy()
    repos["stub_contributing"] = repos.contributing_words < STUB_CONTRIBUTING_WORDS
    repos["set"] = stratified_sets(repos.reset_index(drop=True), rng).values

    codable = units[(units.doc == "agent") & ~units.toc]
    picked = pd.concat(g.sample(min(len(g), args.cap), random_state=rng.integers(2**32))
                       for _, g in codable.groupby("repo"))
    counts = codable.groupby("repo").size().rename("codable_units")
    repos = repos.merge(counts, on="repo")
    repos["coded_units"] = repos.codable_units.clip(upper=args.cap)
    repos["weight"] = repos.codable_units / repos.coded_units

    # Coding order: pilot, then reliability, then main; shuffled within each set.
    set_rank = repos.set.map({"pilot": 0, "reliability": 1, "main": 2})
    order = pd.DataFrame({"r": set_rank, "u": rng.random(len(repos))}).sort_values(["r", "u"]).index
    repos.loc[order, "repo_order"] = range(len(repos))
    repos["repo_order"] = repos.repo_order.astype(int)
    queue = (picked[["unit_id", "repo", "n"]]
             .merge(repos[["repo", "tool", "set", "repo_order", "weight"]], on="repo")
             .sort_values(["repo_order", "n"]).reset_index(drop=True))
    queue["queue_pos"] = queue.index

    CODING.mkdir(exist_ok=True)
    repos.sort_values("repo_order").to_csv(CODING / "assignments.csv", index=False)
    queue.to_csv(CODING / "queue.csv", index=False)
    print(repos.groupby(["set", "tool"]).size().unstack().to_string())
    print(queue.groupby("set").size().rename("units").to_string())
    print(f"total units to code: {len(queue)} | stub CONTRIBUTING repos: {repos.stub_contributing.sum()}")


if __name__ == "__main__":
    main()
