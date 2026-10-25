"""Phase 2, steps 2-3: apply exclusions and draw the stratified sample.

Inputs: data/processed/screen.csv (from gapstudy.screen) and the package's
agent-file contents. Outputs in data/processed/:
    candidates.csv     every agent file with all flags and its exclusion reason
    sampling_flow.csv  files remaining after each exclusion step, per agent
    sample.csv         the sample, in draw order, plus ranked reserves

    python -m gapstudy.sample [--per-agent 67] [--seed 507]
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from gapstudy.filters import flag
from gapstudy.github_client import PROJECT_ROOT
from gapstudy.screen import load_package

PROCESSED = PROJECT_ROOT / "data" / "processed"
TOOLS = ["claude", "agents", "copilot-instructions"]


def duplicate_copies(df: pd.DataFrame) -> pd.Series:
    """True for every member of a near-duplicate cluster except its most-starred file.
    ``near_duplicate_of`` holds the index label of the matching file."""
    parent = {i: i for i in df.index}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in df.near_duplicate_of.dropna().items():
        parent[find(i)] = find(int(j))
    cluster = pd.Series({i: find(i) for i in df.index})
    in_cluster = cluster.map(cluster.value_counts()) > 1
    keeper = df[in_cluster].sort_values("stars", ascending=False).groupby(cluster[in_cluster]).head(1).index
    return in_cluster & ~df.index.isin(keeper)


# Applied in order; a file is attributed to the first rule it fails.
EXCLUSIONS = [
    ("repo no longer exists", lambda d: ~d.repo_exists.fillna(False).astype(bool)),
    ("fork", lambda d: d.fork.fillna(False).astype(bool)),
    ("archived", lambda d: d.archived.fillna(False).astype(bool)),
    ("snapshot commit not found", lambda d: d.snapshot_commit.isna()),
    ("agent file is a symlink", lambda d: d.agent_is_symlink.fillna(False).astype(bool)),
    ("agent file only links elsewhere", lambda d: d.link_only),
    ("agent file not in English", lambda d: d.lang.notna() & (d.lang != "en")),
    ("copy of another repo's agent file", lambda d: d.duplicate_copy),
    ("no README at snapshot", lambda d: d.readme_path.isna()),
    ("no CONTRIBUTING at snapshot", lambda d: d.contributing_path.isna()),
]


def build_candidates() -> pd.DataFrame:
    files, history = load_package()
    files["n_commits"] = [len(history.get((r.repository_owner, r.repository_name, r.file_path), []))
                          for r in files.itertuples()]
    files = flag(files.rename(columns={"stargazers_count": "stars"}))
    screen = pd.read_csv(PROCESSED / "screen.csv")
    df = files[["repo", "tool", "file_path", "stars", "n_commits", "words", "substantive_words",
                "link_only", "lang", "init_header", "never_edited", "near_duplicate_of"]].merge(
        screen.drop(columns=["blob_sha"]), on=["repo", "tool", "file_path"], how="left", validate="1:1")
    df["near_duplicate_repo"] = df.near_duplicate_of.map(lambda j: df.repo[int(j)] if pd.notna(j) else None)
    df["duplicate_copy"] = duplicate_copies(df)
    df["init_unedited"] = df.init_header & df.never_edited  # kept; used for sensitivity analysis

    df["excluded_by"] = None
    for name, rule in EXCLUSIONS:
        hit = df.excluded_by.isna() & rule(df)
        df.loc[hit, "excluded_by"] = name
    return df


def sampling_flow(df: pd.DataFrame) -> pd.DataFrame:
    rows, remaining = [], df
    rows.append({"step": "all agent files in package", **remaining.tool.value_counts().to_dict()})
    for name, _ in EXCLUSIONS:
        remaining = remaining[remaining.excluded_by != name]
        rows.append({"step": f"minus {name}", **remaining.tool.value_counts().to_dict()})
    flow = pd.DataFrame(rows).fillna(0).set_index("step")[TOOLS].astype(int)
    flow["total"] = flow.sum(axis=1)
    return flow


def draw(eligible: pd.DataFrame, per_agent: int, seed: int) -> pd.DataFrame:
    """Equal allocation per agent; one file per repo. Every eligible file gets a rank,
    so files beyond the quota are the ordered reserve list for replacements."""
    rng = np.random.default_rng(seed)
    order = {t: eligible[eligible.tool == t].sample(frac=1, random_state=rng.integers(2**32)) for t in TOOLS}
    used_repos, picked = set(), []
    # Round-robin across agents so no agent gets first pick of shared repos.
    cursors = {t: 0 for t in TOOLS}
    counts = {t: 0 for t in TOOLS}
    while any(cursors[t] < len(order[t]) for t in TOOLS):
        for t in TOOLS:
            while cursors[t] < len(order[t]):
                row = order[t].iloc[cursors[t]]
                cursors[t] += 1
                if row.repo in used_repos:
                    continue
                used_repos.add(row.repo)
                counts[t] += 1
                picked.append({**row.to_dict(), "rank": counts[t], "in_sample": counts[t] <= per_agent})
                break
    return pd.DataFrame(picked)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-agent", type=int, default=67)
    ap.add_argument("--seed", type=int, default=507)
    args = ap.parse_args()

    df = build_candidates()
    df.to_csv(PROCESSED / "candidates.csv", index=False)
    flow = sampling_flow(df)
    flow.to_csv(PROCESSED / "sampling_flow.csv")
    print(flow.to_string())

    eligible = df[df.excluded_by.isna()]
    sample = draw(eligible, args.per_agent, args.seed)
    sample.to_csv(PROCESSED / "sample.csv", index=False)
    s = sample[sample.in_sample]
    print(f"\nsample: {len(s)} files, {s.repo.nunique()} repos; per agent {s.tool.value_counts().to_dict()}")
    print(f"reserves: {(~sample.in_sample).sum()} | /init-unedited in sample: {s.init_unedited.sum()}")
    short = [t for t in TOOLS if (s.tool == t).sum() < args.per_agent]
    if short:
        print(f"WARNING: fewer than {args.per_agent} eligible files for {short}")


if __name__ == "__main__":
    main()
