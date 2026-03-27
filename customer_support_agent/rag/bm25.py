"""BM25 sparse retrieval index.

Provides keyword-based search that complements dense vector search.
Catches exact matches that semantic search might miss (e.g., error codes).
"""

from rank_bm25 import BM25Okapi
import re


# Module-level cache
_bm25_index = None
_bm25_documents = None


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    text = text.lower()
    tokens = re.findall(r"\b\w+\b", text)
    return tokens


def build_bm25_index(documents: list[dict]) -> BM25Okapi:
    """Build a BM25 index from document chunks.

    Args:
        documents: List of dicts with 'content' key.

    Returns:
        BM25Okapi index.
    """
    tokenized_corpus = [_tokenize(doc["content"]) for doc in documents]
    return BM25Okapi(tokenized_corpus)


def get_bm25_index(documents: list[dict]) -> BM25Okapi:
    """Get or build the BM25 index (cached in memory)."""
    global _bm25_index, _bm25_documents

    if _bm25_index is None or _bm25_documents is not documents:
        _bm25_index = build_bm25_index(documents)
        _bm25_documents = documents

    return _bm25_index


def bm25_search(
    query: str,
    documents: list[dict],
    top_k: int = 10,
) -> list[dict]:
    """Search documents using BM25 keyword matching.

    Args:
        query: Search query string.
        documents: List of document dicts (same list used to build index).
        top_k: Number of top results to return.

    Returns:
        List of dicts with keys: doc_index, score, content, source, title, category
    """
    bm25 = get_bm25_index(documents)
    tokenized_query = _tokenize(query)

    scores = bm25.get_scores(tokenized_query)

    # Get top-k indices
    top_indices = scores.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:  # Only include non-zero scores
            doc = documents[idx]
            results.append({
                "doc_index": int(idx),
                "score": float(scores[idx]),
                "content": doc["content"],
                "source": doc["source"],
                "title": doc["title"],
                "category": doc["category"],
            })

    return results
