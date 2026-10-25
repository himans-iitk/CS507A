"""Locate the snapshot commit of an agent file and the human docs at that commit.

The replication package stores each agent file's *blob* SHA, not a commit SHA.
The snapshot commit is the newest commit in the file's history at which the
file has that blob. Tree listings come from the git-trees API; subtrees are
fetched by their own SHA, so unchanged folders are served from the cache.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from gapstudy.github_client import RAW_ACCEPT, GitHubClient

SYMLINK_MODE = "120000"

# GitHub shows README/CONTRIBUTING from .github/ first, then the root, then docs/.
DOC_DIRS = (".github", "", "docs")
DOC_PATTERNS = {
    "readme": re.compile(r"^readme(\.(md|markdown|rst|txt|adoc))?$", re.I),
    "contributing": re.compile(r"^contributing(\.(md|markdown|rst|txt|adoc))?$", re.I),
}


@dataclass
class Snapshot:
    commit: str | None = None
    commit_date: str | None = None
    source: str | None = None  # "package_history" | "api_history"
    candidates_checked: int = 0
    agent_is_symlink: bool = False
    docs: dict[str, dict] = field(default_factory=dict)  # kind -> {path, blob_sha}


def tree(gh: GitHubClient, repo: str, sha: str) -> list[dict] | None:
    """Entries of the tree for a commit or tree SHA (non-recursive)."""
    data = gh.get_json(f"repos/{repo}/git/trees/{sha}")
    return data["tree"] if data else None


def subtree(gh: GitHubClient, repo: str, root: list[dict], dirname: str) -> list[dict] | None:
    if not dirname:
        return root
    for e in root:
        if e["type"] == "tree" and e["path"].lower() == dirname.lower():
            return tree(gh, repo, e["sha"])
    return None


def entry_at(gh: GitHubClient, repo: str, root: list[dict], path: str) -> dict | None:
    """Tree entry for ``path`` (one level of nesting is enough for our files)."""
    *dirs, name = path.split("/")
    entries = subtree(gh, repo, root, dirs[0]) if dirs else root
    for e in entries or []:
        if e["path"] == name:
            return e
    return None


def find_doc(gh: GitHubClient, repo: str, root: list[dict], kind: str) -> dict | None:
    """First README/CONTRIBUTING file in GitHub's lookup order, or None."""
    pattern = DOC_PATTERNS[kind]
    for dirname in DOC_DIRS:
        entries = subtree(gh, repo, root, dirname)
        for e in sorted(entries or [], key=lambda e: e["path"]):
            if e["type"] == "blob" and pattern.match(e["path"]):
                path = f"{dirname}/{e['path']}" if dirname else e["path"]
                return {"path": path, "blob_sha": e["sha"], "symlink": e["mode"] == SYMLINK_MODE}
    return None


def api_history(gh: GitHubClient, repo: str, path: str) -> list[tuple[str, str]]:
    data = gh.get_json(f"repos/{repo}/commits", {"path": path, "per_page": 100}) or []
    return [(c["sha"], c["commit"]["committer"]["date"]) for c in data]


def locate(
    gh: GitHubClient,
    repo: str,
    path: str,
    blob_sha: str,
    history: list[tuple[str, str]],
    max_candidates: int = 20,
) -> Snapshot:
    """Find the snapshot commit and the README/CONTRIBUTING present there.

    ``history`` is the file's (commit_sha, date) list from the package, newest first.
    """
    snap = Snapshot()
    sources = [("package_history", history), ("api_history", None)]
    seen: set[str] = set()
    for source, commits in sources:
        if commits is None:
            commits = api_history(gh, repo, path)
        for sha, date in commits[:max_candidates]:
            if sha in seen:
                continue
            seen.add(sha)
            snap.candidates_checked += 1
            root = tree(gh, repo, sha)
            entry = entry_at(gh, repo, root, path) if root else None
            if entry and entry["sha"] == blob_sha:
                snap.commit, snap.commit_date, snap.source = sha, date, source
                snap.agent_is_symlink = entry["mode"] == SYMLINK_MODE
                for kind in DOC_PATTERNS:
                    if doc := find_doc(gh, repo, root, kind):
                        snap.docs[kind] = doc
                return snap
    return snap


def blob_text(gh: GitHubClient, repo: str, blob_sha: str) -> str | None:
    resp = gh.get(f"repos/{repo}/git/blobs/{blob_sha}", accept=RAW_ACCEPT)
    return resp.body if resp.ok else None
