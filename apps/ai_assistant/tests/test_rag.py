"""Tests for chunking/ingestion/retrieval (uses the lightweight hashing embedder, no downloads)."""
import tempfile
from pathlib import Path

from django.test import SimpleTestCase, override_settings

from apps.ai_assistant.rag import retriever
from apps.ai_assistant.rag.chunking import load_knowledge_base

DOC = """# Box Breathing

## Steps
Breathe in for four seconds. Hold for four seconds. Breathe out for four seconds.

## Notes
Go gently and stop if dizzy.
"""


class ChunkingTests(SimpleTestCase):
    def test_chunks_have_metadata(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            root = Path(tmp)
            (root / "breathing").mkdir()
            (root / "breathing" / "box.md").write_text(DOC, encoding="utf-8")
            chunks = load_knowledge_base(root)
        self.assertTrue(chunks)
        self.assertEqual(chunks[0].metadata["category"], "breathing")
        self.assertEqual(chunks[0].metadata["title"], "Box Breathing")

    def test_missing_directory_returns_empty(self):
        self.assertEqual(load_knowledge_base("does/not/exist"), [])


class RetrievalTests(SimpleTestCase):
    def test_process_query_adds_context_for_short_followups(self):
        query = retriever.process_query("yes please", ["I feel anxious before exams"])
        self.assertIn("anxious", query)

    def test_retrieval_end_to_end_with_hashing_backend(self):
        from apps.ai_assistant.rag import vector_store
        from apps.ai_assistant.rag.ingest import ingest

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = Path(tmp) / "store"
            kb = Path(tmp) / "kb"
            (kb / "breathing").mkdir(parents=True)
            (kb / "breathing" / "box.md").write_text(DOC * 3, encoding="utf-8")
            (kb / "sleep").mkdir()
            (kb / "sleep" / "sleep.md").write_text(
                "# Sleep\n\n## Habits\nKeep a regular bedtime. Avoid caffeine late. Dim the lights before sleeping. " * 3,
                encoding="utf-8")
            with override_settings(VECTOR_STORE_DIR=store, KNOWLEDGE_BASE_DIR=kb):
                ingest(backend="hashing")
                results = retriever.retrieve("breathe in hold breathe out", top_k=2, max_distance=1.5)
                self.assertTrue(results)
                self.assertEqual(results[0].category, "breathing")
                # unrelated query + strict threshold -> nothing relevant
                self.assertEqual(retriever.retrieve("quantum chromodynamics", max_distance=0.1), [])

    def test_retrieval_failure_returns_empty_list(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            with override_settings(VECTOR_STORE_DIR=Path(tmp) / "empty_store"):
                self.assertEqual(retriever.retrieve("anything"), [])
