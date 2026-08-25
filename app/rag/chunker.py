from __future__ import annotations

from dataclasses import dataclass
from app.rag.document_loader import HealthDocument


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    title: str
    source: str
    source_url: str
    topic: str
    chunk_index: int
    text: str


class TextChunker:
    def __init__(self, chunk_size: int = 300, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, doc: HealthDocument) -> list[DocumentChunk]:
        words = doc.content.split()
        if not words:
            return []

        chunks: list[DocumentChunk] = []
        i = 0
        chunk_idx = 0
        while i < len(words):
            chunk_words = words[i : i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            chunk_id = f"{doc.document_id}-chk-{chunk_idx}"

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=doc.document_id,
                    title=doc.title,
                    source=doc.source,
                    source_url=doc.source_url,
                    topic=doc.topic,
                    chunk_index=chunk_idx,
                    text=chunk_text,
                )
            )

            i += self.chunk_size - self.overlap
            chunk_idx += 1

        return chunks

    def chunk_documents(self, docs: list[HealthDocument]) -> list[DocumentChunk]:
        all_chunks: list[DocumentChunk] = []
        for doc in docs:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks
