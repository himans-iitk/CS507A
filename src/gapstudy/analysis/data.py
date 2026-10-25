"""Load the coded units and everything the RQ1/RQ2 analyses need."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from gapstudy.detector.evaluate import load_labels
from gapstudy.github_client import PROJECT_ROOT
from gapstudy.labels import CODING

PROCESSED = PROJECT_ROOT / "data" / "processed"
TOOLS = ["claude", "agents", "copilot-instructions"]
TOOL_NAMES = {"claude": "CLAUDE.md", "agents": "AGENTS.md", "copilot-instructions": "copilot-instructions.md"}
KNOWLEDGE = ["agent_only", "partial", "shared"]  # agent-directed units carry no project knowledge
LIST_FIELDS = ("categories", "evidence", "barriers", "flags")


def frame_shares(processed: Path = PROCESSED) -> dict[str, float]:
    """Each agent's share of the eligible sampling frame (for post-stratification)."""
    c = pd.read_csv(processed / "candidates.csv")
    counts = c[c.excluded_by.isna()].tool.value_counts()
    return (counts / counts.sum()).to_dict()


def load(coding_dir: Path = CODING) -> tuple[pd.DataFrame, bool]:
    """One row per coded unit with repo-level flags; list fields parsed."""
    labels, provisional = load_labels(coding_dir)
    if labels.empty:
        return labels, provisional
    for f in LIST_FIELDS:
        if f in labels:
            labels[f] = labels[f].map(lambda v: json.loads(v) if isinstance(v, str) else (v or []))
    repos = pd.read_csv(coding_dir / "assignments.csv")[["repo", "stub_contributing", "init_unedited"]]
    return labels.merge(repos, on="repo", how="left"), provisional
