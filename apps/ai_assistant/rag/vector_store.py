"""ChromaDB wrapper (local, persistent vector database)."""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "wellness_knowledge"


class VectorStoreError(Exception):
    pass


def get_client():
    try:
        import chromadb
        from chromadb.config import Settings

        settings.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(
            path=str(settings.VECTOR_STORE_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    except Exception as exc:
        raise VectorStoreError(f"vector database unavailable: {exc}") from exc


def get_collection(client=None):
    """Open the existing collection. Raises VectorStoreError if it was never built."""
    client = client or get_client()
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception as exc:
        raise VectorStoreError("knowledge base has not been ingested yet (run ingest_knowledge.py)") from exc


def rebuild_collection(chunks, embedder):
    """Drop and recreate the collection, then store all chunks with embeddings + metadata."""
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # didn't exist yet
    collection = client.create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "embedding_backend": embedder.name,
                  "embedding_model": settings.EMBEDDING_MODEL},
    )
    batch = 64
    for start in range(0, len(chunks), batch):
        part = chunks[start:start + batch]
        collection.add(
            ids=[c.id for c in part],
            documents=[c.text for c in part],
            embeddings=embedder.embed([c.text for c in part]),
            metadatas=[c.metadata for c in part],
        )
    return collection
