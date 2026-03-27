"""Hybrid retrieval orchestrator.

Combines dense (FAISS) + sparse (BM25) retrieval with Reciprocal Rank Fusion,
followed by Vertex AI reranking. This is the main entry point for document retrieval.
"""

import numpy as np
import faiss

from customer_support_agent.rag.indexer import get_index
from customer_support_agent.rag.bm25 import bm25_search
from customer_support_agent.rag.reranker import rerank
from customer_support_agent.rag.embeddings import get_embeddings
from customer_support_agent.config.settings import settings


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    k: int = 60,
) -> list[dict]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion (RRF).

    RRF score = sum(1 / (k + rank)) across all lists where the doc appears.
    k=60 is the standard value from the original paper.

    Args:
        ranked_lists: List of ranked result lists. Each result must have 'doc_index'.
        k: RRF constant (default: 60).

    Returns:
        Merged list sorted by RRF score, with 'rrf_score' added.
    """
    rrf_scores = {}  # doc_index -> rrf_score
    doc_data = {}  # doc_index -> doc dict

    for ranked_list in ranked_lists:
        for rank, doc in enumerate(ranked_list):
            idx = doc["doc_index"]
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (k + rank + 1)
            if idx not in doc_data:
                doc_data[idx] = doc

    # Sort by RRF score
    sorted_indices = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    results = []
    for idx in sorted_indices:
        doc = doc_data[idx].copy()
        doc["rrf_score"] = rrf_scores[idx]
        doc["score"] = rrf_scores[idx]  # Use RRF as the unified score
        results.append(doc)

    return results


def dense_search(
    query: str,
    top_k: int = 10,
) -> list[dict]:
    """Search using dense FAISS vector similarity.

    Args:
        query: Search query string.
        top_k: Number of results to return.

    Returns:
        List of result dicts with doc_index, score, content, source, title, category.
    """
    index, documents = get_index()

    # Embed the query
    query_embedding = get_embeddings([query])
    faiss.normalize_L2(query_embedding)

    # Search
    scores, indices = index.search(query_embedding, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        doc = documents[idx]
        results.append({
            "doc_index": idx,
            "score": float(score),
            "content": doc["content"],
            "source": doc["source"],
            "title": doc["title"],
            "category": doc["category"],
        })

    return results


def hybrid_search(
    query: str,
    expanded_queries: list[str] | None = None,
    intent_filter: str | None = None,
    top_k: int = settings.RAG_TOP_K,
) -> list[dict]:
    """Perform hybrid retrieval: dense + sparse + RRF + rerank.

    Args:
        query: The main search query.
        expanded_queries: Additional queries from query expansion (optional).
        intent_filter: Filter results by category/intent (optional).
        top_k: Final number of results to return.

    Returns:
        List of top_k document dicts, reranked.
    """
    _, documents = get_index()

    # Dense retrieval
    dense_results = dense_search(query, top_k=10)

    # Also search with expanded queries if provided
    if expanded_queries:
        for eq in expanded_queries[:2]:  # Limit to 2 expansion queries
            extra_dense = dense_search(eq, top_k=5)
            dense_results.extend(extra_dense)

    # Sparse retrieval (BM25)
    sparse_results = bm25_search(query, documents, top_k=10)

    # Also BM25 on expanded queries
    if expanded_queries:
        for eq in expanded_queries[:2]:
            extra_sparse = bm25_search(eq, documents, top_k=5)
            sparse_results.extend(extra_sparse)

    # Reciprocal Rank Fusion to merge dense + sparse
    merged = reciprocal_rank_fusion([dense_results, sparse_results])

    # Optional: filter by intent/category
    if intent_filter:
        filtered = [d for d in merged if d.get("category") == intent_filter]
        # Fall back to unfiltered if too few results
        if len(filtered) >= 3:
            merged = filtered

    # Take top candidates for reranking (reranker is expensive, limit input)
    candidates = merged[:15]

    # Rerank
    reranked = rerank(query, candidates, top_k=top_k)

    return reranked
