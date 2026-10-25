"""Phase 2, step 4: fetch the agent file, README and CONTRIBUTING at the snapshot commit.

Reads data/processed/sample.csv (in-sample rows, plus reserves with --reserves)
and writes one folder per repo under data/processed/corpus/<owner>__<name>/:
    agent.<ext>  README.<ext>  CONTRIBUTING.<ext>  meta.json
plus data/processed/corpus_manifest.csv with one row per repo.

    python -m gapstudy.fetch
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import PurePosixPath

import pandas as pd
from tqdm import tqdm

from gapstudy.github_client import PROJECT_ROOT, GitHubClient
from gapstudy.snapshot import blob_text

PROCESSED = PROJECT_ROOT / "data" / "processed"
CORPUS = PROCESSED / "corpus"


def git_blob_sha(text: str, encoding: str = "utf-8") -> str:
    data = text.encode(encoding)
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def verify(text: str, sha: str) -> bool:
    """True if ``text`` is the blob's content (a few repos store UTF-16 files)."""
    return any(git_blob_sha(text, enc) == sha for enc in ("utf-8", "utf-16-le"))


def ext(path: str) -> str:
    return PurePosixPath(path).suffix.lower() or ".txt"


def fetch_row(gh: GitHubClient, row: pd.Series) -> dict:
    folder = CORPUS / row.repo.replace("/", "__")
    folder.mkdir(parents=True, exist_ok=True)
    docs = {
        "agent": (row.file_path, row.blob_sha),
        "README": (row.readme_path, row.readme_blob_sha),
        "CONTRIBUTING": (row.contributing_path, row.contributing_blob_sha),
    }
    meta = {k: row[k] for k in ("repo", "tool", "rank", "stars", "snapshot_commit", "snapshot_date",
                                "snapshot_source", "init_unedited", "n_commits")}
    meta = {k: (v.item() if hasattr(v, "item") else v) for k, v in meta.items()}
    for kind, (path, sha) in docs.items():
        text = blob_text(gh, row.repo, sha)
        if text is None:
            raise RuntimeError(f"could not fetch {kind} {path} ({sha})")
        name = f"{kind}{ext(path)}"
        (folder / name).write_text(text)
        meta[kind] = {
            "path": path,
            "blob_sha": sha,
            "file": name,
            "format": ext(path).lstrip("."),
            "words": len(text.split()),
            "blob_verified": verify(text, sha),
        }
    (folder / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reserves", type=int, default=0, help="also fetch the first N reserves per agent")
    args = ap.parse_args()

    sample = pd.read_csv(PROCESSED / "sample.csv")
    screen = pd.read_csv(PROCESSED / "screen.csv")[["repo", "tool", "blob_sha"]]
    sample = sample.merge(screen, on=["repo", "tool"], how="left", validate="1:1")
    quota = sample[sample.in_sample].groupby("tool").size()
    todo = sample[sample["rank"] <= sample.tool.map(quota) + args.reserves]

    gh = GitHubClient()
    rows = []
    for _, row in tqdm(todo.iterrows(), total=len(todo)):
        m = fetch_row(gh, row)
        rows.append({
            "repo": m["repo"], "tool": m["tool"], "rank": m["rank"], "in_sample": bool(row.in_sample),
            "snapshot_commit": m["snapshot_commit"], "snapshot_date": m["snapshot_date"],
            "init_unedited": m["init_unedited"],
            **{f"{k.lower()}_{f}": m[k][f] for k in ("agent", "README", "CONTRIBUTING")
               for f in ("path", "format", "words", "blob_verified")},
        })
    manifest = pd.DataFrame(rows)
    manifest.to_csv(PROCESSED / "corpus_manifest.csv", index=False)
    print(f"fetched {len(manifest)} repos with {gh.network_calls} network calls")
    unverified = manifest.filter(like="blob_verified").eq(False).any(axis=1).sum()
    print(f"blob SHA mismatches (text differs from git object): {unverified}")
    print(manifest.groupby("tool")[["agent_words", "readme_words", "contributing_words"]].median())


if __name__ == "__main__":
    main()
