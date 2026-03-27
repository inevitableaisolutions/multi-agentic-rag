"""Tools for analytics logging — writes full interaction records to BigQuery/SQLite."""

import json
import time
from datetime import datetime, timezone

from google.adk.tools import ToolContext


def log_interaction(
    tool_context: ToolContext,
) -> dict:
    """Log the complete interaction to BigQuery for analytics.

    Reads classification, retrieval, and evaluation data from session state
    and writes a comprehensive interaction record.

    Args:
        tool_context: ADK tool context for session state access.

    Returns:
        Dict with log status.
    """
    classification = tool_context.state.get("triage_classification", {})
    retrieved_docs = tool_context.state.get("retrieved_docs", [])
    evaluation = tool_context.state.get("qa_evaluation", {})

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": str(tool_context.state.get("session_id", "unknown")),

        # Triage data
        "original_query": classification.get("original_query", ""),
        "rewritten_queries": json.dumps(classification.get("rewritten_queries", [])),
        "intent": classification.get("intent", ""),
        "sentiment": classification.get("sentiment", ""),
        "urgency": classification.get("urgency", ""),

        # Retrieval data
        "retrieved_doc_ids": json.dumps([d["source"] for d in retrieved_docs]),
        "num_docs_retrieved": len(retrieved_docs),

        # Evaluation data
        "faithfulness_score": evaluation.get("faithfulness", 0.0),
        "answer_relevance_score": evaluation.get("answer_relevance", 0.0),
        "context_relevance_score": evaluation.get("context_relevance", 0.0),
        "overall_score": evaluation.get("overall_score", 0.0),
        "hallucination_detected": evaluation.get("hallucination_detected", False),
        "compliance_passed": not evaluation.get("pii_in_response", False),
        "decision": evaluation.get("decision", ""),

        # Cache data
        "cache_hit": tool_context.state.get("cache_hit", False),
    }

    # Write to analytics backend
    try:
        from customer_support_agent.analytics.bigquery_client import get_analytics_client
        client = get_analytics_client()
        client.insert_row(row)
        return {"status": "logged", "timestamp": row["timestamp"]}
    except Exception as e:
        # Don't fail the pipeline if analytics logging fails
        return {"status": "log_failed", "error": str(e), "timestamp": row["timestamp"]}
