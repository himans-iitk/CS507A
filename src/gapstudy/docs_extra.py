"""Phase 4: inventory of docs/ Markdown at the snapshot commit (sensitivity check).

The main analysis compares agent files with README and CONTRIBUTING only. Here we
list the Markdown/reST files under docs/ for every sampled repo, and download them
for a seeded subsample, so Phase 7 can test whether counting docs/ as human
documentation changes the agent-only rate.

    python -m gapstudy.docs_extra [--subsample 30]
Writes data/processed/docs_inventory.csv and corpus/<repo>/docs/... for the subsample.
"""

from __future__ import annotations

import argparse
import re

import pandas as pd
from tqdm import tqdm

from gapstudy.fetch import verify
from gapstudy.github_client import PROJECT_ROOT, GitHubClient
from gapstudy.snapshot import blob_text, tree

PROCESSED = PROJECT_ROOT / "data" / "processed"
CORPUS = PROCESSED / "corpus"
DOC_FILE = re.compile(r"\.(md|markdown|mdx|rst)$", re.I)
MAX_FILES, MAX_BYTES = 60, 2_000_000


def docs_files(gh: GitHubClient, repo: str, commit: str) -> list[dict]:
    """Markdown/reST blobs under the top-level docs/ folder (recursive), or []."""
    root = tree(gh, repo, commit) or []
    docs = next((e for e in root if e["type"] == "tree" and e["path"].lower() == "docs"), None)
    if not docs:
        return []
    data = gh.get_json(f"repos/{repo}/git/trees/{docs['sha']}", {"recursive": "1"}) or {}
    return [{"path": f"{docs['path']}/{e['path']}", "sha": e["sha"], "size": e.get("size", 0)}
            for e in data.get("tree", []) if e["type"] == "blob" and DOC_FILE.search(e["path"])]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subsample", type=int, default=30)
    ap.add_argument("--seed", type=int, default=507)
    args = ap.parse_args()

    manifest = pd.read_csv(PROCESSED / "corpus_manifest.csv")
    manifest = manifest[manifest.in_sample]
    gh = GitHubClient()
    inventory, files = [], {}
    for row in tqdm(manifest.itertuples(), total=len(manifest)):
        found = docs_files(gh, row.repo, row.snapshot_commit)
        files[row.repo] = found
        inventory.append({"repo": row.repo, "tool": row.tool, "docs_files": len(found),
                          "docs_bytes": sum(f["size"] for f in found)})
    inv = pd.DataFrame(inventory)

    with_docs = inv[inv.docs_files > 0]
    sub = with_docs.sample(min(args.subsample, len(with_docs)), random_state=args.seed).repo
    inv["in_docs_subsample"] = inv.repo.isin(sub)
    inv["docs_fetched"] = 0
    for repo in tqdm(sub, desc="fetch"):
        budget, fetched = MAX_BYTES, 0
        for f in sorted(files[repo], key=lambda f: (f["path"].count("/"), f["path"]))[:MAX_FILES]:
            if f["size"] > budget:
                continue
            text = blob_text(gh, repo, f["sha"])
            if text is None or not verify(text, f["sha"]):
                continue
            dest = CORPUS / repo.replace("/", "__") / f["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
            budget -= f["size"]
            fetched += 1
        inv.loc[inv.repo == repo, "docs_fetched"] = fetched

    inv.to_csv(PROCESSED / "docs_inventory.csv", index=False)
    print(f"repos with docs/ Markdown: {len(with_docs)} / {len(inv)} | "
          f"median files {with_docs.docs_files.median():.0f} | network calls {gh.network_calls}")
    print(f"subsample: {len(sub)} repos, {int(inv.docs_fetched.sum())} files fetched")


if __name__ == "__main__":
    main()
