"""Ingestion: read documents -> chunk -> embed -> store in ChromaDB (with metadata)."""
import logging

from django.conf import settings

from .chunking import load_knowledge_base
from .embeddings import get_embedder_with_fallback
from .vector_store import rebuild_collection

logger = logging.getLogger(__name__)


def ingest(knowledge_dir=None, backend=None, model_name=None):
    """Rebuild the vector index from scratch. Returns (num_chunks, num_documents, backend_name)."""
    knowledge_dir = knowledge_dir or settings.KNOWLEDGE_BASE_DIR
    chunks = load_knowledge_base(knowledge_dir)
    if not chunks:
        raise FileNotFoundError(f"No .md/.txt knowledge documents found in {knowledge_dir}")

    embedder = get_embedder_with_fallback(
        backend or settings.EMBEDDING_BACKEND, model_name or settings.EMBEDDING_MODEL
    )
    rebuild_collection(chunks, embedder)
    documents = len({c.metadata["source"] for c in chunks})
    logger.info("Ingested %d chunks from %d documents using %s.", len(chunks), documents, embedder.name)
    return len(chunks), documents, embedder.name
