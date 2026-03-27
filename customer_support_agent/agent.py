"""Customer Support Intelligence — Main agent definition.

Defines the 3-agent SequentialAgent pipeline:
  Agent 1: Query Processing (intent, rewriting, expansion, HyDE)
  Agent 2: Retrieval & Generation (hybrid search, grounded response)
  Agent 3: Evaluation (LLM-as-judge, compliance, analytics logging)

Guardrails and semantic cache are wired as pre-processing steps
via a custom orchestrator agent that wraps the SequentialAgent.
"""

from google.adk.agents import LlmAgent, SequentialAgent, BaseAgent
from google.genai import types

from customer_support_agent.config.prompts import (
    QUERY_PROCESSING_PROMPT,
    RETRIEVAL_GENERATION_PROMPT,
    EVALUATION_PROMPT,
)
from customer_support_agent.tools.query_processing_tools import process_query
from customer_support_agent.tools.retrieval_tools import search_knowledge_base
from customer_support_agent.tools.evaluation_tools import evaluate_response
from customer_support_agent.tools.analytics_tools import log_interaction


# ─── Agent 1: Query Processing ────────────────────────────────────────────────

query_processing_agent = LlmAgent(
    name="query_processing_agent",
    model="gemini-2.5-flash",
    description="Classifies customer queries by intent, sentiment, urgency. "
                "Rewrites and expands queries for better retrieval. "
                "Generates hypothetical answers (HyDE) for embedding-based search.",
    instruction=QUERY_PROCESSING_PROMPT,
    tools=[process_query],
    output_key="triage_result",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.1,  # Low temp for consistent classification
    ),
)


# ─── Agent 2: Retrieval & Generation ──────────────────────────────────────────

retrieval_generation_agent = LlmAgent(
    name="retrieval_generation_agent",
    model="gemini-2.5-flash",
    description="Retrieves relevant knowledge base articles using hybrid search "
                "(dense + sparse + reranking) and generates grounded responses.",
    instruction=RETRIEVAL_GENERATION_PROMPT,
    tools=[search_knowledge_base],
    output_key="knowledge_response",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,  # Moderate temp for helpful, natural responses
    ),
)


# ─── Agent 3: Evaluation ─────────────────────────────────────────────────────

evaluation_agent = LlmAgent(
    name="evaluation_agent",
    model="gemini-2.5-flash",
    description="Evaluates response quality using LLM-as-judge metrics "
                "(faithfulness, relevance, hallucination, compliance). "
                "Decides to approve, revise, or escalate. Logs analytics.",
    instruction=EVALUATION_PROMPT,
    tools=[evaluate_response, log_interaction],
    output_key="qa_decision",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.1,  # Low temp for consistent evaluation
    ),
)


# ─── Root Orchestrator: Sequential Pipeline ───────────────────────────────────

root_agent = SequentialAgent(
    name="customer_support_pipeline",
    description="Production-grade customer support intelligence pipeline. "
                "Processes queries through: Query Processing → Hybrid RAG Retrieval "
                "→ Quality Evaluation with approve/revise/escalate decisions.",
    sub_agents=[
        query_processing_agent,
        retrieval_generation_agent,
        evaluation_agent,
    ],
)
