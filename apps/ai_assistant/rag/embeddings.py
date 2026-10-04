"""Embedding backends: turn text into vectors so similar meanings are close together.

* "sentence-transformers" (default): neural embeddings, best quality.
* "hashing": lightweight keyword-based vectors (no download, no torch). Used as an
  automatic fallback so the app still works if the neural model can't be loaded.
"""
import logging

import numpy as np

logger = logging.getLogger(__name__)

HASHING = "hashing"
SENTENCE_TRANSFORMERS = "sentence-transformers"

_cache = {}


class EmbeddingError(Exception):
    pass


_STOPWORDS = frozenset(
    "a an and are as at be but by for from has have i if in into is it its me my of on or so that the "
    "their then there these they this to was we were what when which who will with you your am been do does".split()
)


class HashingEmbedder:
    """Keyword-style vectors: words/bigrams are hashed into a fixed-size, L2-normalised vector.

    Pure numpy (fast to import, no model download). Similar wording -> similar vectors.
    """

    name = HASHING

    def __init__(self, n_features=1024):
        self.n_features = n_features

    def _vectorize(self, text):
        import re
        import zlib

        words = [w for w in re.findall(r"[a-z']+", text.lower()) if w not in _STOPWORDS]
        features = words + [f"{a}_{b}" for a, b in zip(words, words[1:])]
        vector = np.zeros(self.n_features, dtype=np.float32)
        for feature in features:
            vector[zlib.crc32(feature.encode("utf-8")) % self.n_features] += 1.0
        norm = np.linalg.norm(vector)
        return (vector / norm if norm else vector).tolist()

    def embed(self, texts):
        return [self._vectorize(t) for t in texts]


class SentenceTransformerEmbedder:
    name = SENTENCE_TRANSFORMERS

    def __init__(self, model_name):
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
        except Exception as exc:  # import error, no internet for first download, etc.
            raise EmbeddingError(f"could not load '{model_name}': {exc}") from exc

    def embed(self, texts):
        vectors = self._model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vectors, dtype=np.float32).tolist()


def get_embedder(backend, model_name="all-MiniLM-L6-v2"):
    """Return a cached embedder. Raises EmbeddingError if it can't be created."""
    key = (backend, model_name)
    if key not in _cache:
        if backend == HASHING:
            _cache[key] = HashingEmbedder()
        elif backend == SENTENCE_TRANSFORMERS:
            _cache[key] = SentenceTransformerEmbedder(model_name)
        else:
            raise EmbeddingError(f"unknown embedding backend '{backend}'")
    return _cache[key]


def get_embedder_with_fallback(backend, model_name):
    """Try the requested backend, else fall back to hashing. Returns the embedder."""
    try:
        return get_embedder(backend, model_name)
    except EmbeddingError as exc:
        logger.warning("Embedding backend '%s' unavailable (%s). Falling back to hashing.", backend, exc)
        return get_embedder(HASHING)
