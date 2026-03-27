"""Tools for Agent 1: Query Processing Agent.

Handles intent detection, query rewriting, expansion, and HyDE.
"""

from google.adk.tools import ToolContext


def process_query(
    original_query: str,
    intent: str,
    sentiment: str,
    urgency: str,
    rewritten_queries: list[str],
    expanded_terms: list[str],
    hypothetical_answer: str,
    tool_context: ToolContext,
) -> dict:
    """Process and classify a customer support query.

    Args:
        original_query: The customer's original query text.
        intent: Primary intent — one of: billing, technical, account, general.
        sentiment: Customer sentiment — one of: positive, neutral, negative, frustrated.
        urgency: Urgency level — one of: low, medium, high, critical.
        rewritten_queries: 2-3 clearer search queries rewritten from the original.
        expanded_terms: 3-5 related terms or synonyms for query expansion.
        hypothetical_answer: A brief hypothetical answer (2-3 sentences) for HyDE.
        tool_context: ADK tool context for session state access.

    Returns:
        Classification result dict.
    """
    classification = {
        "original_query": original_query,
        "intent": intent,
        "sentiment": sentiment,
        "urgency": urgency,
        "rewritten_queries": rewritten_queries,
        "expanded_terms": expanded_terms,
        "hypothetical_answer": hypothetical_answer,
    }

    # Write to session state for downstream agents
    tool_context.state["triage_classification"] = classification

    return {
        "status": "classified",
        "classification": classification,
    }
