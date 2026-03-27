"""RAG pipeline — chunking, embedding, indexing, BM25, reranking, hybrid retrieval."""

from customer_support_agent.rag.retriever import hybrid_search

__all__ = ["hybrid_search"]
