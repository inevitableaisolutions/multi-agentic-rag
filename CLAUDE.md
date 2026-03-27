# Customer Support Intelligence — Agentic RAG System on GCP

## What This Is
A production-grade multi-agent customer support system built with Google ADK on GCP.

## Architecture
```
Query → Guardrails (PII/injection/topic) → Semantic Cache → Agent 1 (Query Processing) → Agent 2 (Hybrid RAG) → Agent 3 (Evaluation) → BigQuery + Response
```

## Key Files
- `customer_support_agent/agent.py` — Root SequentialAgent + 3 sub-agents
- `customer_support_agent/__init__.py` — ADK entry point (exports root_agent)
- `customer_support_agent/config/settings.py` — All configuration (Pydantic Settings)
- `customer_support_agent/config/prompts.py` — All agent system prompts
- `customer_support_agent/rag/retriever.py` — Hybrid retrieval orchestrator
- `customer_support_agent/tools/` — Agent tools (query processing, retrieval, evaluation, analytics)
- `customer_support_agent/guardrails/` — Input guardrails (PII, injection, topic)
- `customer_support_agent/cache/semantic_cache.py` — FAISS-based semantic cache
- `DECISIONS.md` — Decision log: every choice, failure, and version change
- `INTERVIEW_PREP.md` — Complete walkthrough + interview Q&A

## How to Run
```bash
source .venv/bin/activate
# Local with API key:
export GOOGLE_API_KEY="your-key"
adk web customer_support_agent

# With GCP:
export GOOGLE_CLOUD_PROJECT="your-project"
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
adk web customer_support_agent
```

## Tech Stack
- Google ADK (agent framework)
- Vertex AI Gemini 2.5 Flash (LLM)
- Vertex AI gemini-embedding-001 (embeddings, 768d)
- FAISS (dense vector search) + rank_bm25 (sparse search)
- Vertex AI Ranking API (reranking)
- BigQuery (analytics) + SQLite (fallback)
- Cloud Run (deployment)

## Rules
- All credentials in `.env` (gitignored). NEVER in code.
- Log ALL decisions in `DECISIONS.md` — especially failures and changes.
- Use `config/settings.py` for all configuration. No hardcoded values.
- Read official GCP docs before implementing any GCP API call.
