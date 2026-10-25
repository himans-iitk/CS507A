"""Content-based exclusion flags for agent files (offline, no API calls)."""

from __future__ import annotations

import re

import pandas as pd
from langdetect import DetectorFactory, LangDetectException, detect
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DetectorFactory.seed = 0

CODE_BLOCK = re.compile(r"```.*?```", re.S)
MD_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
URL = re.compile(r"https?://\S+")
AT_IMPORT = re.compile(r"(?<!\w)@[\w./-]+")  # Claude Code @path imports
FILE_REF = re.compile(r"\b[\w./-]+\.(md|mdc|txt)\b", re.I)
HEADING = re.compile(r"^#+\s.*$", re.M)
POINTER_WORDS = re.compile(
    r"\b(see|read|refer|refers|reference|follow|instructions?|guidelines?|rules?|in|to|the|for|and|"
    r"please|all|this|file|repository|repo|project|agents?|ai|claude|copilot|codex|more|details?|"
    r"also|our|at|of|located|found|use|contains?)\b",
    re.I,
)
INIT_HEADER = re.compile(r"This file provides guidance to Claude Code", re.I)
WORD = re.compile(r"\w+")


def prose(text: str) -> str:
    """Text with code blocks, links and URLs removed."""
    text = CODE_BLOCK.sub(" ", text)
    text = MD_LINK.sub(r"\1", text)
    return URL.sub(" ", text)


def substantive_words(text: str) -> int:
    """Words left after removing headings, links, file references and pointer phrasing."""
    t = HEADING.sub(" ", prose(text))
    t = AT_IMPORT.sub(" ", t)
    t = FILE_REF.sub(" ", t)
    t = POINTER_WORDS.sub(" ", t)
    return len(WORD.findall(t))


def is_link_only(text: str, max_words: int = 15) -> bool:
    """True when the file mainly points elsewhere (e.g. '@AGENTS.md', 'See CONTRIBUTING.md')."""
    has_pointer = bool(MD_LINK.search(text) or URL.search(text) or AT_IMPORT.search(text) or FILE_REF.search(text))
    return has_pointer and substantive_words(text) <= max_words


def language(text: str) -> str | None:
    sample = prose(text)
    if len(WORD.findall(sample)) < 5:
        return None
    try:
        return detect(sample[:5000])
    except LangDetectException:
        return None


def near_duplicates(texts: pd.Series, repos: pd.Series, threshold: float = 0.9) -> pd.Series:
    """For each text, the index label of the most similar file in *another repo*
    if cosine >= threshold, else None."""
    vec = TfidfVectorizer(ngram_range=(1, 3), min_df=1, sublinear_tf=True)
    sims = cosine_similarity(vec.fit_transform(texts.fillna("")), dense_output=True)
    repos = repos.to_numpy()
    out = []
    for i in range(len(texts)):
        row = sims[i].copy()
        row[repos == repos[i]] = 0  # same repo (another agent file) is not a template copy
        j = row.argmax()
        out.append(texts.index[j] if row[j] >= threshold else None)
    return pd.Series(out, index=texts.index, dtype=object)


def flag(df: pd.DataFrame) -> pd.DataFrame:
    """Add exclusion flags. Expects columns: repo, tool, static_content, n_commits."""
    text = df.static_content.fillna("")
    return df.assign(
        words=text.str.count(r"\w+"),
        substantive_words=text.map(substantive_words),
        link_only=text.map(is_link_only),
        lang=text.map(language),
        init_header=text.str.contains(INIT_HEADER),
        never_edited=df.n_commits.fillna(1) <= 1,
        near_duplicate_of=near_duplicates(text, df.repo),
    )
