"""Vertex AI Ranking API wrapper for reranking retrieved documents.

Uses semantic-ranker-default-004 for cross-encoder reranking.
Falls back to score-based sorting if Ranking API is unavailable.
"""

import os
from customer_support_agent.config.settings import settings


def rerank(
    query: str,
    documents: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Rerank documents using Vertex AI Ranking API.

    Falls back to sorting by existing score if the API is unavailable.

    Args:
        query: The search query.
        documents: List of dicts with 'content' and 'score' keys.
        top_k: Number of top results to return after reranking.

    Returns:
        Reranked list of document dicts (top_k items).
    """
    use_vertex = settings.GOOGLE_GENAI_USE_VERTEXAI and (
        settings.GOOGLE_CLOUD_PROJECT or os.environ.get("GOOGLE_CLOUD_PROJECT")
    )

    if use_vertex:
        try:
            return _vertex_rerank(query, documents, top_k)
        except Exception as e:
            # Fall back to score-based sorting
            print(f"Ranking API unavailable, falling back to score sort: {e}")
            return _fallback_rerank(documents, top_k)
    else:
        return _fallback_rerank(documents, top_k)


def _vertex_rerank(query: str, documents: list[dict], top_k: int) -> list[dict]:
    """Rerank using Vertex AI Discovery Engine Ranking API."""
    from google.cloud import discoveryengine_v1 as discoveryengine

    project_id = settings.GOOGLE_CLOUD_PROJECT or os.environ.get("GOOGLE_CLOUD_PROJECT")

    client = discoveryengine.RankServiceClient()

    # Build ranking request
    records = []
    for i, doc in enumerate(documents):
        records.append(
            discoveryengine.RankingRecord(
                id=str(i),
                content=doc["content"][:1000],  # 1024 token limit ≈ 4000 chars
                title=doc.get("title", ""),
            )
        )

    ranking_config = f"projects/{project_id}/locations/global/rankingConfigs/default_ranking_config"

    request = discoveryengine.RankRequest(
        ranking_config=ranking_config,
        model="semantic-ranker-default-004",
        query=query,
        records=records,
        top_n=top_k,
    )

    response = client.rank(request=request)

    # Map results back to original documents
    reranked = []
    for record in response.records:
        idx = int(record.id)
        doc = documents[idx].copy()
        doc["rerank_score"] = record.score
        reranked.append(doc)

    return reranked


def _fallback_rerank(documents: list[dict], top_k: int) -> list[dict]:
    """Simple fallback: sort by existing score and return top_k."""
    sorted_docs = sorted(documents, key=lambda d: d.get("score", 0), reverse=True)
    return sorted_docs[:top_k]
