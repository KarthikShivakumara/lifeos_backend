from __future__ import annotations

from app.rag.vector_store import SearchResult, VectorStore


class MedicalRetriever:
    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    def retrieve(self, query: str, user_context_keywords: str | None = None, top_k: int = 3) -> list[SearchResult]:
        augmented_query = f"{query} {user_context_keywords or ''}".strip()
        return self.vector_store.search(augmented_query, top_k=top_k)
