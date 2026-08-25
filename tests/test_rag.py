from __future__ import annotations

from app.rag.chunker import TextChunker
from app.rag.document_loader import DocumentLoader
from app.rag.embeddings import embedding_engine
from app.rag.rag_service import rag_service
from app.rag.retriever import MedicalRetriever
from app.rag.vector_store import VectorStore


def test_document_loader_sources_and_metadata() -> None:
    loader = DocumentLoader()
    docs = loader.load_documents()
    assert len(docs) >= 5
    topics = [d.topic for d in docs]
    assert "hypertension" in topics
    assert "diabetes" in topics
    assert "heart_disease" in topics
    assert "obesity" in topics


def test_chunker_provenance_preservation() -> None:
    loader = DocumentLoader()
    chunker = TextChunker(chunk_size=100, overlap=20)
    docs = loader.load_documents()
    chunks = chunker.chunk_documents(docs)

    assert len(chunks) > len(docs)
    for c in chunks:
        assert c.document_id is not None
        assert c.title is not None
        assert c.source is not None
        assert c.source_url is not None


def test_vector_embeddings_and_store_retrieval() -> None:
    v_store = VectorStore()
    loader = DocumentLoader()
    chunker = TextChunker()
    chunks = chunker.chunk_documents(loader.load_documents())
    v_store.add_chunks(chunks)

    results = v_store.search("blood pressure sodium hypertension", top_k=2)
    assert len(results) > 0
    top_chunk = results[0].chunk
    assert "hypertension" in top_chunk.topic.lower() or "blood pressure" in top_chunk.text.lower()


def test_rag_service_singleton_retrieval() -> None:
    rag_service.initialize()
    res = rag_service.retrieve_relevant_guidelines("hba1c diabetes blood sugar", top_k=3)
    assert len(res) > 0
    assert any("diabetes" in r.chunk.topic for r in res)
