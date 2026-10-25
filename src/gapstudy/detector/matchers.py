"""Text similarity backends for the gap detector.

Every matcher maps texts to L2-normalised vectors, so similarity is a dot product.
    tfidf          word 1-2-gram TF-IDF fitted on the whole corpus (lexical baseline)
    <hf model id>  a sentence-transformers embedding model, cached on disk
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from gapstudy.github_client import PROJECT_ROOT

CACHE = PROJECT_ROOT / "data" / "processed" / "embeddings"

# Query/document prefixes some models were trained with. The task here is symmetric
# ("is the same knowledge stated?"), so Qwen3-Embedding is used without its query instruction.
PREFIXES = {
    "intfloat/e5-base-v2": ("query: ", "passage: "),
}

# Pinned model revisions, so the paper can name the exact weights.
REVISIONS = {
    "sentence-transformers/all-MiniLM-L6-v2": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
    "BAAI/bge-base-en-v1.5": "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
    "Qwen/Qwen3-Embedding-0.6B": "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3",
}


class TfidfMatcher:
    name = "tfidf"

    def __init__(self, corpus: list[str]):
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2,
                                   token_pattern=r"(?u)\b[\w./-]{2,}\b").fit(corpus)

    def encode(self, texts: list[str], role: str = "doc"):
        return normalize(self.vec.transform(texts)).astype(np.float32)  # sparse; dense would be ~16 GB


def similarity(a, b) -> np.ndarray:
    """Cosine similarity of row-normalised (dense or sparse) matrices."""
    s = a @ b.T
    return s.toarray() if hasattr(s, "toarray") else np.asarray(s)


class EmbeddingMatcher:
    def __init__(self, model_id: str, device: str | None = None, batch_size: int = 64, cache: Path = CACHE):
        from sentence_transformers import SentenceTransformer  # slow import; only when used
        self.name = model_id
        self.model = SentenceTransformer(model_id, device=device, revision=REVISIONS.get(model_id))
        self.batch_size = batch_size
        Path(cache).mkdir(parents=True, exist_ok=True)
        self.cache_path = Path(cache) / f"{model_id.replace('/', '__')}.npz"  # one file per model
        self.cache: dict[str, np.ndarray] = {}
        if self.cache_path.exists():
            data = np.load(self.cache_path)
            self.cache = dict(zip(data["keys"], data["vecs"]))

    def encode(self, texts: list[str], role: str = "doc") -> np.ndarray:
        query_prefix, doc_prefix = PREFIXES.get(self.name, ("", ""))
        prefix = query_prefix if role == "query" else doc_prefix
        keys = [hashlib.sha1((prefix + t).encode()).hexdigest() for t in texts]
        todo = sorted({k: i for i, k in enumerate(keys) if k not in self.cache}.values())
        if todo:
            vecs = self.model.encode([prefix + texts[i] for i in todo], batch_size=self.batch_size,
                                     normalize_embeddings=True, show_progress_bar=len(todo) > 1000)
            self.cache.update({keys[i]: v.astype(np.float32) for i, v in zip(todo, vecs)})
            np.savez(self.cache_path, keys=np.array(list(self.cache)), vecs=np.stack(list(self.cache.values())))
        return np.stack([self.cache[k] for k in keys])


def make(name: str, corpus: list[str] | None = None, **kw):
    if name == "tfidf":
        return TfidfMatcher(corpus or [])
    return EmbeddingMatcher(name, **kw)
