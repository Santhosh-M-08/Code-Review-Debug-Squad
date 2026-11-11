"""ChromaDB vector store holding coding guidelines, bug patterns, debugging examples and testing tips.

Markdown files in ``knowledge_base/`` are split into one chunk per ``## `` section, embedded by
ChromaDB's default embedding function and retrieved by similarity search. The file-name prefix
(``style_``, ``bugs_``, ``testing_``) becomes the chunk's ``category`` so each agent can filter
for the guidance it needs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from . import config


def chunk_markdown(text: str, source: str, category: str) -> list:
    """Split markdown into chunks, one per ``## `` heading. Pure function (easy to unit test)."""
    chunks: list = []
    title = None
    buffer: list = []
    sections = []
    for line in text.splitlines():
        if line.startswith("## "):
            sections.append((title, buffer))
            title, buffer = line[3:].strip(), []
        else:
            buffer.append(line)
    sections.append((title, buffer))

    for title, lines in sections:
        body = "\n".join(lines).strip()
        if title and body:
            chunks.append(
                {
                    "id": f"{source}::{len(chunks)}",
                    "text": f"{title}\n{body}",
                    "metadata": {"source": source, "section": title, "category": category},
                }
            )
    return chunks


class KnowledgeBase:
    def __init__(self, persist_dir: Path = config.CHROMA_DIR, kb_dir: Path = config.KB_DIR):
        import chromadb  # imported lazily so the rest of the package works without it

        self.kb_dir = Path(kb_dir)
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = self.client.get_or_create_collection(
            config.COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
        if self.collection.count() == 0:
            self.ingest()

    def ingest(self) -> int:
        """(Re)build the index from the markdown files. Returns the number of chunks stored."""
        existing = self.collection.get()["ids"]
        if existing:
            self.collection.delete(ids=existing)

        chunks: list = []
        for path in sorted(self.kb_dir.glob("*.md")):
            category = path.stem.split("_", 1)[0]
            chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), path.name, category))
        if chunks:
            self.collection.add(
                ids=[c["id"] for c in chunks],
                documents=[c["text"] for c in chunks],
                metadatas=[c["metadata"] for c in chunks],
            )
        return len(chunks)

    def count(self) -> int:
        return self.collection.count()

    def search(self, query: str, k: int = config.RETRIEVAL_TOP_K, category: Optional[str] = None) -> list:
        """Similarity search. Returns dicts with id, text, source, section, category, distance."""
        total = self.collection.count()
        if total == 0 or not query.strip():
            return []
        kwargs = {"query_texts": [query], "n_results": min(k, total)}
        if category:
            kwargs["where"] = {"category": category}
        res = self.collection.query(**kwargs)
        hits = []
        for i, doc_id in enumerate(res["ids"][0]):
            meta = res["metadatas"][0][i]
            hits.append(
                {
                    "id": doc_id,
                    "text": res["documents"][0][i],
                    "source": meta["source"],
                    "section": meta["section"],
                    "category": meta["category"],
                    "distance": round(res["distances"][0][i], 3),
                }
            )
        return hits


def format_context(hits: list) -> str:
    """Render retrieved chunks for a prompt."""
    if not hits:
        return "(no reference guidance retrieved)"
    return "\n\n".join(f"[{h['source']} > {h['section']}]\n{h['text']}" for h in hits)
