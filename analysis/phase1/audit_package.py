"""Phase 1: audit the Agent READMEs replication package (offline, no API calls).

Fetch the inputs first:
    git clone https://github.com/woraamy/Agent-Context-File-Analysis.git data/raw/agent_context_pkg
    (git -C data/raw/agent_context_pkg checkout 77b16a9a53c99efcda1c98c98c4afcd807f7227c)

Writes analysis/phase1/agent_files.csv (one row per agent file) and
analysis/phase1/repo_agent_files.csv (one row per repo), and prints the
summary numbers quoted in FINDINGS.md.
"""

from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "data" / "raw" / "agent_context_pkg"
OUT = Path(__file__).resolve().parent
TOOLS = ["claude", "agents", "copilot-instructions"]


def load_agent_files() -> pd.DataFrame:
    frames = []
    for tool in TOOLS:
        static = pd.read_csv(PKG / f"datasets/derived/static/{tool}_static_dataset.csv", low_memory=False)
        hist = pd.read_csv(
            PKG / f"datasets/derived/commits/{tool}_commit_changes.csv",
            low_memory=False,
            usecols=["repository_owner", "repository_name", "file_path", "commit_sha", "commit_date"],
        )
        latest = (hist.sort_values("commit_date")
                      .groupby(["repository_owner", "repository_name", "file_path"])
                      .agg(n_commits=("commit_sha", "size"),
                           latest_commit_sha=("commit_sha", "last"),
                           latest_commit_date=("commit_date", "last"))
                      .reset_index())
        static = static.merge(latest, on=["repository_owner", "repository_name", "file_path"], how="left")
        static["tool"] = tool
        frames.append(static)

    df = pd.concat(frames, ignore_index=True)
    df["repo"] = df.repository_owner + "/" + df.repository_name
    df["words"] = df.static_content.fillna("").str.count(r"\w+")
    return df.rename(columns={"file_commit": "blob_sha", "stargazers_count": "stars"})[[
        "repo", "tool", "file_path", "branch", "stars", "blob_sha", "words",
        "n_commits", "latest_commit_sha", "latest_commit_date", "file_url",
    ]]


def summarize_labels() -> None:
    import sys
    sys.path.insert(0, str(PKG))  # labels.py is pure-Python taxonomy helpers
    from manifest_analysis.classification.labels import DISPLAY_NAMES, label_columns, labels_from_manual_row

    lab = pd.read_csv(PKG / "datasets/derived/classification/inputs/final_am_classification_3.csv")
    cols = label_columns(lab.columns)
    labels = [labels_from_manual_row(row, cols) for _, row in lab.iterrows()]
    counts = Counter(label for row in labels for label in row)
    print(f"\nManual labels: {len(lab)} files (file-level, multi-label) "
          f"by source {lab.source_dataset.value_counts().to_dict()}")
    for key, n in counts.most_common():
        print(f"  {DISPLAY_NAMES[key]:30s} {100 * n / len(lab):5.1f}%")


def main() -> None:
    df = load_agent_files()
    df.to_csv(OUT / "agent_files.csv", index=False)

    print("Per agent:")
    print(df.groupby("tool").agg(files=("repo", "size"), repos=("repo", "nunique"),
                                 median_words=("words", "median"), median_stars=("stars", "median"),
                                 median_commits=("n_commits", "median")).to_string())

    repos = df.groupby("repo").agg(n_files=("tool", "size"),
                                   tools=("tool", lambda t: "+".join(sorted(t))))
    repos.to_csv(OUT / "repo_agent_files.csv")
    print(f"\nTotal: {len(df)} files in {len(repos)} repos; "
          f"{(repos.n_files > 1).sum()} repos have more than one agent file")
    print(repos.tools.value_counts().to_string())

    summarize_labels()


if __name__ == "__main__":
    main()
