from __future__ import annotations

from app.rag.chunker import TextChunker
from app.rag.document_loader import DocumentLoader
from app.rag.retriever import MedicalRetriever
from app.rag.vector_store import SearchResult, VectorStore


class RAGService:
    _instance: RAGService | None = None

    def __init__(self) -> None:
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.vector_store = VectorStore()
        self.retriever = MedicalRetriever(self.vector_store)
        self._initialized = False

    @classmethod
    def get_instance(cls) -> RAGService:
        if cls._instance is None:
            cls._instance = RAGService()
            cls._instance.initialize()
        return cls._instance

    def initialize(self) -> None:
        if self._initialized:
            return
        docs = self.loader.load_documents()
        chunks = self.chunker.chunk_documents(docs)
        self.vector_store.add_chunks(chunks)
        self._initialized = True

    def retrieve_relevant_guidelines(
        self, query: str, context_summary: str | None = None, top_k: int = 3
    ) -> list[SearchResult]:
        return self.retriever.retrieve(query, user_context_keywords=context_summary, top_k=top_k)


rag_service = RAGService.get_instance()
