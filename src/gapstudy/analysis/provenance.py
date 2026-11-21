"""Where each frozen label came from: an AI draft the annotator accepted, a draft the
annotator corrected, or blind coding without any draft.

The paper's methods section reports these counts (generated, never typed), and the
draft-to-final confusion shows which kinds of drafts the annotator changed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from gapstudy.labels import CODING

ORIGINS = {
    "draft_accepted": "AI draft accepted unchanged",
    "draft_details_edited": "AI draft, coverage kept, other fields edited",
    "draft_corrected": "AI draft, coverage corrected by the annotator",
    "blind": "Coded without an AI draft (blind)",
}


def aliases(coding_dir: Path = CODING) -> dict[str, str]:
    """One person may have typed their name two ways; coding/coder_aliases.json maps them together."""
    path = coding_dir / "coder_aliases.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _truthy(v) -> bool:
    return str(v).strip().lower() in ("true", "1")


def origin(row) -> str:
    if not _truthy(row.get("draft_shown")):
        return "blind"
    if row.get("verdict") == "wrong":
        return "draft_corrected"
    if row.get("verdict") == "correct" or _truthy(row.get("accepted_draft")):
        return "draft_accepted"
    changed = row.get("changed_fields")
    changed = json.loads(changed.replace("'", '"')) if isinstance(changed, str) else (changed or [])
    return "draft_corrected" if "coverage" in changed else "draft_details_edited"


def annotate(labels: pd.DataFrame, drafts: dict[str, dict]) -> pd.DataFrame:
    df = labels.copy()
    df["origin"] = df.apply(origin, axis=1)
    df["draft_coverage"] = df.unit_id.map(lambda u: drafts.get(u, {}).get("coverage"))
    df["ai_filled"] = df.get("filled_by", pd.Series(index=df.index, dtype=object)).notna()
    return df


def summary(labels: pd.DataFrame, drafts: dict[str, dict]) -> dict:
    df = annotate(labels, drafts)
    reviewed = df[df.origin != "blind"]
    counts = {k: int((df.origin == k).sum()) for k in ORIGINS}
    by_set = pd.crosstab(df.set, df.origin).reindex(columns=list(ORIGINS), fill_value=0)
    by_draft = (reviewed.groupby("draft_coverage")
                .agg(drafts=("unit_id", "size"), corrected=("origin", lambda o: int((o == "draft_corrected").sum())))
                .assign(correction_rate=lambda t: t.corrected / t.drafts))
    corrected = reviewed[reviewed.origin == "draft_corrected"]
    confusion = pd.crosstab(corrected.draft_coverage, corrected.coverage) if len(corrected) else pd.DataFrame()
    return {
        "counts": counts,
        "n_reviewed": int(len(reviewed)),
        "accept_rate": float((reviewed.origin != "draft_corrected").mean()) if len(reviewed) else float("nan"),
        "n_ai_filled": int(df.ai_filled.sum()),
        "coders": sorted({aliases().get(c, c) for c in map(str, df.coder.dropna().unique())}),
        "by_set": by_set,
        "by_draft": by_draft,
        "confusion": confusion,
    }


def markdown(s: dict) -> list[str]:
    who = ("single annotator: " if len(s["coders"]) == 1 else "annotators: ") + ", ".join(s["coders"])
    L = ["## Label provenance", "",
         f"How each frozen label was produced ({who}).", "",
         "| Origin | Units |", "|---|---|"]
    L += [f"| {ORIGINS[k]} | {v} |" for k, v in s["counts"].items()]
    L += ["", f"Of {s['n_reviewed']} AI drafts reviewed, {s['accept_rate']:.1%} kept the drafted coverage. After a coverage correction, {s['n_ai_filled']} labels had missing evidence or newcomer-need "
          "fields completed by the model (marked `filled_by` in the data).", "",
          "### By coding set", "", s["by_set"].to_markdown(), "",
          "### Correction rate by drafted coverage", "",
          s["by_draft"].assign(correction_rate=lambda t: t.correction_rate.map("{:.1%}".format)).to_markdown(), ""]
    if not s["confusion"].empty:
        L += ["### Corrected drafts (rows: draft, columns: final)", "", s["confusion"].to_markdown(), ""]
    return L
