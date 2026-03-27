"""Tools for Agent 2: Retrieval & Generation Agent.

Handles hybrid search (dense + sparse + rerank) and returns relevant documents.
"""

from google.adk.tools import ToolContext
from customer_support_agent.rag.retriever import hybrid_search


def search_knowledge_base(
    query: str,
    intent: str,
    tool_context: ToolContext,
) -> dict:
    """Search the knowledge base using hybrid retrieval.

    Uses dense vector search (FAISS) + sparse keyword search (BM25),
    merges with Reciprocal Rank Fusion, and reranks with Vertex AI.

    Args:
        query: The search query (use rewritten query for best results).
        intent: The classified intent category to optionally filter results.
        tool_context: ADK tool context for session state access.

    Returns:
        Dict with retrieved articles and their relevance scores.
    """
    # Get expanded queries from triage classification if available
    classification = tool_context.state.get("triage_classification", {})
    expanded_queries = classification.get("rewritten_queries", [])

    # Also add expanded terms as a query
    expanded_terms = classification.get("expanded_terms", [])
    if expanded_terms:
        expanded_queries.append(" ".join(expanded_terms))

    # Run hybrid retrieval
    results = hybrid_search(
        query=query,
        expanded_queries=expanded_queries,
        intent_filter=intent if intent != "general" else None,
        top_k=5,
    )

    # Store retrieved doc IDs in session state for evaluation
    tool_context.state["retrieved_docs"] = [
        {"source": r["source"], "title": r["title"], "score": r.get("score", 0)}
        for r in results
    ]

    return {
        "status": "success",
        "num_results": len(results),
        "articles": [
            {
                "title": r["title"],
                "source": r["source"],
                "category": r["category"],
                "content": r["content"],
                "relevance_score": round(r.get("score", 0), 4),
            }
            for r in results
        ],
    }
