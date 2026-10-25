import pandas as pd

from gapstudy.fetch import git_blob_sha
from gapstudy.filters import is_link_only, near_duplicates
from gapstudy.sample import draw, duplicate_copies
from gapstudy.snapshot import find_doc, locate


class FakeGH:
    """Serves git-trees responses from a dict keyed by SHA."""

    def __init__(self, trees, commits=()):
        self.trees, self.commits = trees, list(commits)

    def get_json(self, path, params=None):
        if path.endswith("/commits"):
            return self.commits
        sha = path.rsplit("/", 1)[-1]
        return {"tree": self.trees[sha]} if sha in self.trees else None


def blob(path, sha="x", mode="100644"):
    return {"path": path, "type": "blob", "sha": sha, "mode": mode}


def folder(path, sha):
    return {"path": path, "type": "tree", "sha": sha, "mode": "040000"}


def test_locate_picks_newest_commit_holding_the_blob():
    gh = FakeGH({
        "c2": [blob("CLAUDE.md", "new"), blob("README.md")],
        "c1": [blob("CLAUDE.md", "old"), blob("README.md"), blob("CONTRIBUTING.md", "k")],
    })
    snap = locate(gh, "o/r", "CLAUDE.md", "old", [("c2", "d2"), ("c1", "d1")])
    assert snap.commit == "c1" and snap.source == "package_history"
    assert snap.docs["contributing"]["path"] == "CONTRIBUTING.md"


def test_locate_falls_back_to_api_history_and_nested_path():
    gh = FakeGH(
        {"c9": [folder(".github", "t1")], "t1": [blob("copilot-instructions.md", "b")]},
        commits=[{"sha": "c9", "commit": {"committer": {"date": "d9"}}}],
    )
    snap = locate(gh, "o/r", ".github/copilot-instructions.md", "b", [])
    assert snap.commit == "c9" and snap.source == "api_history"


def test_locate_reports_symlinked_agent_file():
    gh = FakeGH({"c1": [blob("CLAUDE.md", "b", mode="120000")]})
    assert locate(gh, "o/r", "CLAUDE.md", "b", [("c1", "d")]).agent_is_symlink


def test_find_doc_prefers_dot_github_then_root_then_docs():
    gh = FakeGH({"g": [blob("CONTRIBUTING.md", "gh")], "d": [blob("contributing.rst", "dd")]})
    root = [folder(".github", "g"), folder("docs", "d"), blob("Contributing.md", "root")]
    assert find_doc(gh, "o/r", root, "contributing")["path"] == ".github/CONTRIBUTING.md"
    root = [folder("docs", "d"), blob("README")]
    assert find_doc(gh, "o/r", root, "contributing")["path"] == "docs/contributing.rst"
    assert find_doc(gh, "o/r", root, "readme")["path"] == "README"
    assert find_doc(gh, "o/r", [blob("CONTRIBUTORS.md")], "contributing") is None


def test_link_only():
    assert is_link_only("@AGENTS.md\n")
    assert is_link_only("# CLAUDE.md\n\nSee [AGENTS.md](AGENTS.md) for instructions.")
    assert not is_link_only("- Main branch is master\n- Run `cargo fmt` and `cargo test` after each task\n"
                            "- Husk files use .husk or .hk extensions, never edit generated parsers by hand")
    assert not is_link_only("Run make verify before committing; never edit src/gen/.")  # no pointer


def test_near_duplicates_ignore_same_repo():
    texts = pd.Series(["run make verify before every commit please"] * 3 + ["something else entirely"])
    dup = near_duplicates(texts, pd.Series(["a", "a", "b", "c"]))
    assert dup[0] == 2 and dup[2] in (0, 1) and dup[3] is None


def test_duplicate_copies_keeps_most_starred():
    df = pd.DataFrame({"repo": ["a", "b", "c"], "stars": [5, 50, 9], "near_duplicate_of": [1, 0, None]})
    assert duplicate_copies(df).tolist() == [True, False, False]


def test_draw_equal_allocation_unique_repos_and_reproducible():
    rows = [{"repo": f"r{i % 40}", "tool": t} for i in range(60)
            for t in ("claude", "agents", "copilot-instructions")]
    eligible = pd.DataFrame(rows).drop_duplicates()
    a, b = draw(eligible, 5, seed=1), draw(eligible, 5, seed=1)
    assert a.equals(b)
    s = a[a.in_sample]
    assert s.tool.value_counts().tolist() == [5, 5, 5] and s.repo.is_unique and a.repo.is_unique


def test_git_blob_sha_matches_git():
    assert git_blob_sha("hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"
