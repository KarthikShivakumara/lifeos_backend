from __future__ import annotations

from dataclasses import dataclass
from app.rag.chunker import DocumentChunk
from app.rag.embeddings import embedding_engine


@dataclass
class SearchResult:
    chunk: DocumentChunk
    similarity_score: float


class VectorStore:
    def __init__(self) -> None:
        self.chunks: list[DocumentChunk] = []
        self.vectors: list[dict[str, float]] = []

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            vec = embedding_engine.get_embedding(f"{chunk.title} {chunk.topic} {chunk.text}")
            self.chunks.append(chunk)
            self.vectors.append(vec)

    def search(self, query: str, top_k: int = 3, min_score: float = 0.05) -> list[SearchResult]:
        query_vec = embedding_engine.get_embedding(query)
        if not query_vec or not self.chunks:
            return []

        results: list[SearchResult] = []
        for chunk, vec in zip(self.chunks, self.vectors):
            sim = embedding_engine.cosine_similarity(query_vec, vec)
            if sim >= min_score:
                results.append(SearchResult(chunk=chunk, similarity_score=sim))

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]
