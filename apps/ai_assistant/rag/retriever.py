"""Retriever: find the knowledge chunks most relevant to a user's message."""
import logging
import re
from dataclasses import dataclass

from django.conf import settings

from .embeddings import EmbeddingError, get_embedder
from .vector_store import VectorStoreError, get_collection

logger = logging.getLogger(__name__)

_FILLER = re.compile(r"\b(please|hi|hello|hey|um|uh|just|really|like|you know|kind of|sort of)\b", re.IGNORECASE)


@dataclass
class RetrievedChunk:
    text: str
    title: str
    category: str
    source: str
    distance: float


def process_query(user_text, recent_user_messages=None):
    """Query processing: clean the text and add context from the previous user turn.

    Short follow-ups like "yes, how?" are meaningless alone, so we prepend the
    previous user message to keep the retrieval query meaningful.
    """
    query = _FILLER.sub(" ", user_text or "")
    query = re.sub(r"\s+", " ", query).strip()
    if len(query.split()) < 6 and recent_user_messages:
        query = f"{recent_user_messages[-1]} {query}".strip()
    return query[:600]


def retrieve(query, top_k=None, max_distance=None):
    """Return up to top_k relevant chunks (closest first). Returns [] on any failure."""
    top_k = top_k or settings.RAG_TOP_K
    max_distance = settings.RAG_MAX_DISTANCE if max_distance is None else max_distance
    if not query.strip():
        return []
    try:
        collection = get_collection()
        meta = collection.metadata or {}
        embedder = get_embedder(
            meta.get("embedding_backend", settings.EMBEDDING_BACKEND),
            meta.get("embedding_model", settings.EMBEDDING_MODEL),
        )
        if meta.get("embedding_backend") == "hashing":
            # Keyword vectors give larger distances than neural embeddings, so be less strict.
            max_distance = max(max_distance, 0.92)
        result = collection.query(
            query_embeddings=embedder.embed([query]),
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
    except (VectorStoreError, EmbeddingError) as exc:
        logger.warning("RAG retrieval unavailable: %s", exc)
        return []
    except Exception:
        logger.exception("Unexpected RAG retrieval failure")
        return []

    chunks = []
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    for text, metadata, distance in zip(documents, metadatas, distances):
        if distance <= max_distance:  # drop chunks that aren't really relevant
            chunks.append(
                RetrievedChunk(
                    text=text,
                    title=metadata.get("title", ""),
                    category=metadata.get("category", ""),
                    source=metadata.get("source", ""),
                    distance=float(distance),
                )
            )
    return chunks
