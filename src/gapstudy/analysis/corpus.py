"""Descriptive comparison of the three documents per repo (needs no labels).

Length (words) and Flesch Reading Ease, computed with textstat as in the Agent
READMEs paper, on prose with code blocks removed. Agent file vs README and vs
CONTRIBUTING are compared within repos (paired Wilcoxon signed-rank).
"""

from __future__ import annotations

import json
import re

import pandas as pd
import textstat
from scipy.stats import wilcoxon

from gapstudy.analysis.data import PROCESSED

FENCE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.S | re.M)
INLINE_CODE = re.compile(r"`[^`\n]+`")
LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
MARKUP = re.compile(r"[#>*_|]+")


def prose(text: str) -> str:
    text = FENCE.sub(" ", text)
    text = INLINE_CODE.sub(" ", text)
    text = LINK.sub(r"\1", text)
    return MARKUP.sub(" ", text)


def documents() -> pd.DataFrame:
    rows = []
    for folder in sorted((PROCESSED / "corpus").iterdir()):
        meta = json.loads((folder / "meta.json").read_text())
        for doc in ("agent", "README", "CONTRIBUTING"):
            text = (folder / meta[doc]["file"]).read_text()
            p = prose(text)
            rows.append({"repo": meta["repo"], "tool": meta["tool"], "doc": doc,
                         "words": len(text.split()),
                         "flesch": textstat.flesch_reading_ease(p) if len(p.split()) >= 30 else float("nan")})
    return pd.DataFrame(rows)


def summary(docs: pd.DataFrame) -> pd.DataFrame:
    return docs.groupby("doc")[["words", "flesch"]].median().round(1).reindex(["agent", "README", "CONTRIBUTING"])


def paired_tests(docs: pd.DataFrame) -> pd.DataFrame:
    wide = docs.pivot(index="repo", columns="doc", values=["words", "flesch"])
    rows = []
    for metric in ("words", "flesch"):
        for other in ("README", "CONTRIBUTING"):
            pair = wide[metric][["agent", other]].dropna()
            diff = pair["agent"] - pair[other]
            stat, p = wilcoxon(pair["agent"], pair[other])
            rows.append({"metric": metric, "comparison": f"agent vs {other}", "repos": len(pair),
                         "median_difference": float(diff.median()), "agent_higher_share": float((diff > 0).mean()), "p": p})
    return pd.DataFrame(rows)
