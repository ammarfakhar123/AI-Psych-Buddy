"""Split markdown knowledge documents into small, self-contained chunks.

Why chunk? Embedding a whole document blurs its meaning. Small chunks (a few
paragraphs under one heading) let the retriever return exactly the relevant part,
so we send the LLM only a little focused context instead of the entire knowledge base.
"""
import re
from dataclasses import dataclass
from pathlib import Path

MAX_CHUNK_CHARS = 900
MIN_CHUNK_CHARS = 120


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict


def _split_sections(markdown):
    """Return (document_title, [(section_heading, section_body), ...])."""
    title = ""
    sections = []
    heading, buffer = "Overview", []

    for line in markdown.splitlines():
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif line.startswith("## "):
            if "".join(buffer).strip():
                sections.append((heading, "\n".join(buffer).strip()))
            heading, buffer = line[3:].strip(), []
        else:
            buffer.append(line)
    if "".join(buffer).strip():
        sections.append((heading, "\n".join(buffer).strip()))
    return title, sections


def _pack_paragraphs(body, max_chars=MAX_CHUNK_CHARS):
    """Group paragraphs into pieces <= max_chars, repeating the last paragraph as overlap."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    pieces, current = [], []
    for paragraph in paragraphs:
        if current and len("\n\n".join(current + [paragraph])) > max_chars:
            pieces.append("\n\n".join(current))
            overlap = current[-1] if len(current[-1]) < max_chars // 3 else None
            current = [overlap] if overlap else []
        current.append(paragraph)
    if current:
        pieces.append("\n\n".join(current))
    return pieces


def chunk_document(path, root):
    """Chunk one markdown file. `root` is the knowledge_base directory."""
    path, root = Path(path), Path(root)
    markdown = path.read_text(encoding="utf-8")
    relative = path.relative_to(root).as_posix()
    category = path.relative_to(root).parts[0] if len(path.relative_to(root).parts) > 1 else "general"
    title, sections = _split_sections(markdown)
    title = title or path.stem.replace("_", " ").title()

    chunks = []
    for section_heading, body in sections:
        for piece in _pack_paragraphs(body):
            if len(piece) < MIN_CHUNK_CHARS and chunks and chunks[-1].metadata["source"] == relative:
                # Merge tiny trailing pieces into the previous chunk.
                chunks[-1].text += "\n\n" + piece
                continue
            index = len(chunks)
            chunks.append(
                Chunk(
                    id=f"{relative}::{index}",
                    text=f"{title} - {section_heading}\n{piece}",
                    metadata={
                        "source": relative,
                        "category": category,
                        "title": title,
                        "section": section_heading,
                        "chunk_index": index,
                    },
                )
            )
    return chunks


def load_knowledge_base(root):
    """Chunk every .md/.txt file under `root`. Returns [] if the folder is missing/empty."""
    root = Path(root)
    if not root.exists():
        return []
    chunks = []
    for path in sorted(list(root.rglob("*.md")) + list(root.rglob("*.txt"))):
        if path.name.lower() == "readme.md":
            continue
        chunks.extend(chunk_document(path, root))
    return chunks
