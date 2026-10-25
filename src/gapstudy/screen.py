"""Phase 2, step 1: screen every agent file in the replication package.

For each file: repository status (exists, fork, archived), snapshot commit,
whether the agent file is a symlink, and which README/CONTRIBUTING exist at
that commit. All API responses are cached, so the script can be stopped and
re-run; finished rows are recomputed from the cache without network calls.

    python -m gapstudy.screen            # writes data/processed/screen.csv
"""

from __future__ import annotations

import argparse
import logging

import pandas as pd
from tqdm import tqdm

from gapstudy.github_client import PROJECT_ROOT, GitHubClient
from gapstudy.snapshot import locate

PKG = PROJECT_ROOT / "data" / "raw" / "agent_context_pkg" / "datasets"
OUT = PROJECT_ROOT / "data" / "processed" / "screen.csv"
TOOLS = ["claude", "agents", "copilot-instructions"]

log = logging.getLogger(__name__)


def load_package() -> tuple[pd.DataFrame, dict]:
    files, history = [], {}
    for tool in TOOLS:
        df = pd.read_csv(PKG / f"derived/static/{tool}_static_dataset.csv", low_memory=False)
        df["tool"] = tool
        files.append(df)
        commits = pd.read_csv(
            PKG / f"derived/commits/{tool}_commit_changes.csv", low_memory=False,
            usecols=["repository_owner", "repository_name", "file_path", "commit_sha", "commit_date"],
        ).sort_values("commit_date", ascending=False)
        for key, g in commits.groupby(["repository_owner", "repository_name", "file_path"]):
            history[key] = list(zip(g.commit_sha, g.commit_date))
    df = pd.concat(files, ignore_index=True)
    df["repo"] = df.repository_owner + "/" + df.repository_name
    return df, history


def repo_status(gh: GitHubClient, repo: str) -> dict:
    meta = gh.get_json(f"repos/{repo}")
    if meta is None:
        return {"repo_exists": False}
    return {
        "repo_exists": True,
        "repo_full_name_now": meta["full_name"],
        "fork": meta["fork"],
        "archived": meta["archived"],
        "language": meta.get("language"),
        "stars_now": meta["stargazers_count"],
    }


def screen_row(gh: GitHubClient, row: pd.Series, history: list) -> dict:
    out = {"repo": row.repo, "tool": row.tool, "file_path": row.file_path, "blob_sha": row.file_commit}
    out.update(repo_status(gh, row.repo))
    if not out["repo_exists"]:
        return out
    snap = locate(gh, row.repo, row.file_path, row.file_commit, history)
    out.update({
        "snapshot_commit": snap.commit,
        "snapshot_date": snap.commit_date,
        "snapshot_source": snap.source,
        "candidates_checked": snap.candidates_checked,
        "agent_is_symlink": snap.agent_is_symlink,
    })
    for kind in ("readme", "contributing"):
        doc = snap.docs.get(kind)
        out[f"{kind}_path"] = doc["path"] if doc else None
        out[f"{kind}_blob_sha"] = doc["blob_sha"] if doc else None
        out[f"{kind}_is_symlink"] = doc["symlink"] if doc else None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="screen only the first N files (for a dry run)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.WARNING)

    files, history = load_package()
    if args.limit:
        files = files.sample(args.limit, random_state=0)
    gh = GitHubClient()
    rows = []
    for _, row in tqdm(files.iterrows(), total=len(files), mininterval=30):
        key = (row.repository_owner, row.repository_name, row.file_path)
        try:
            rows.append(screen_row(gh, row, history.get(key, [])))
        except Exception as exc:  # keep going; failures are listed in the output
            log.error("%s %s: %s", row.repo, row.file_path, exc)
            rows.append({"repo": row.repo, "tool": row.tool, "file_path": row.file_path, "error": str(exc)})
    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT if not args.limit else OUT.with_name("screen_dryrun.csv"), index=False)
    print(f"screened {len(out)} files with {gh.network_calls} network calls")
    print(out.groupby("tool")[["snapshot_commit", "readme_path", "contributing_path"]].count())


if __name__ == "__main__":
    main()
