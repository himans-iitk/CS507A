"""Phase 5: check the pass-1 labels and freeze them as the analysis dataset.

    python -m gapstudy.freeze [--version v1] [--force]

Checks that every queued unit is labelled, under the current codebook version,
without internal inconsistencies. If all checks pass (or --force), writes
coding/labels_<version>.csv (one row per unit, list fields as JSON, with set,
tool and weight) and a SHA-256 checksum next to it. Analyses read only this file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from gapstudy.labels import CODING, LabelStore
from gapstudy.pilot_report import problems

LIST_FIELDS = ("categories", "evidence", "barriers", "flags")


def check(coding_dir: Path) -> tuple[pd.DataFrame, list[str]]:
    codebook = json.loads((coding_dir / "codebook.json").read_text())
    queue = pd.read_csv(coding_dir / "queue.csv")
    labels = LabelStore(coding_dir).to_frame(1)
    issues = []
    if labels.empty:
        return labels, [f"no labels: 0 / {len(queue)} units coded"]

    labels = labels[labels.unit_id.isin(queue.unit_id)]
    missing = queue[~queue.unit_id.isin(labels.unit_id)]
    if len(missing):
        by_set = missing.groupby("set").size().to_dict()
        issues.append(f"{len(missing)} queued units not labelled {by_set}")
    old = labels[labels.codebook_version != codebook["version"]]
    if len(old):
        issues.append(f"{len(old)} units labelled under an older codebook "
                      f"{old.codebook_version.value_counts().to_dict()} (use the tool's recheck mode)")
    for field in ("evidence", "need", "categories", "flags", "notes"):
        if field not in labels:
            labels[field] = None
    labels["problems"] = labels.apply(problems, axis=1)
    bad = labels[labels.problems.str.len() > 0]
    if len(bad):
        kinds = bad.problems.explode().value_counts().to_dict()
        issues.append(f"{len(bad)} units with consistency problems {kinds} (see gapstudy.pilot_report)")
    return labels.merge(queue[["unit_id", "repo", "tool", "set", "weight"]], on="unit_id"), issues


def freeze(coding_dir: Path, version: str, force: bool = False) -> Path:
    labels, issues = check(coding_dir)
    for issue in issues:
        print(f"  ✗ {issue}")
    if issues and not force:
        raise SystemExit("Not frozen. Fix the issues above or pass --force (and say so in the paper).")
    out = labels.drop(columns=["problems", "pass"], errors="ignore").copy()
    for field in LIST_FIELDS:
        if field in out:
            out[field] = out[field].map(lambda v: json.dumps(v or []))
    path = coding_dir / f"labels_{version}.csv"
    out.sort_values("unit_id").to_csv(path, index=False)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_suffix(".sha256").write_text(f"{digest}  {path.name}\n")
    print(f"  ✓ froze {len(out)} units → {path.name} (sha256 {digest[:12]}…)")
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    freeze(CODING, args.version, args.force)


if __name__ == "__main__":
    main()
