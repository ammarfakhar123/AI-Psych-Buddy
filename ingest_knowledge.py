#!/usr/bin/env python
"""Build (or rebuild) the wellness knowledge vector index.

Usage:
    python ingest_knowledge.py                # rebuild from knowledge_base/
    python ingest_knowledge.py --backend hashing   # no neural model needed

Run it again whenever you add/edit documents in knowledge_base/.
"""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Ingest wellness documents into the vector database.")
    parser.add_argument("--dir", help="Knowledge base folder (default: knowledge_base/)")
    parser.add_argument("--backend", choices=["sentence-transformers", "hashing"],
                        help="Embedding backend (default: EMBEDDING_BACKEND from .env)")
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from apps.ai_assistant.rag.ingest import ingest

    try:
        chunks, documents, backend = ingest(knowledge_dir=args.dir, backend=args.backend)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    print(f"Done: {documents} documents -> {chunks} chunks stored (embeddings: {backend}).")


if __name__ == "__main__":
    main()
