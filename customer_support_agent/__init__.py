"""Customer Support Intelligence — Agentic RAG System.

ADK entry point. Exports root_agent for discovery by `adk run` and `adk web`.
"""

from customer_support_agent.agent import root_agent

__all__ = ["root_agent"]
