# Decision Log

Every architectural choice, component swap, failure, and version change is logged here.
Format: newest first.

---

## [2026-03-27] Decision: LLM Model Changed — gemini-2.0-flash → gemini-2.5-flash
**Choice:** gemini-2.5-flash via Vertex AI
**Previous:** gemini-2.0-flash
**Why changed:** gemini-2.0-flash returned 404 on newly created GCP project `multi-agent-support-gcp` (model not yet provisioned). gemini-2.5-flash was available immediately and is the newer, better model.
**Status:** Active (replaces gemini-2.0-flash decision below)

## [2026-03-27] Decision: Auth Changed — API Key → Vertex AI
**Choice:** Vertex AI with GCP project `multi-agent-support-gcp`
**Previous:** Google AI Studio free API key
**Why changed:** Free tier quota exhausted (limit: 0 for gemini-2.0-flash). Vertex AI with billing provides production-grade access with no quota issues. Also more impressive for the interview.
**Status:** Active

## [2026-03-27] Decision: Agent Framework — Google ADK
**Choice:** Google ADK (pip install google-adk)
**Alternatives considered:** LangGraph (more mature, 27.6k stars, typed state, checkpoint time-travel), CrewAI, AutoGen, Semantic Kernel
**Why:** Job posting asks for ADK agent. Native GCP integration (one-command Cloud Run deploy). Simpler API for sequential pipeline. Google-maintained = aligns with GTS ecosystem.
**Trade-off:** LangGraph has superior state management and graph orchestration. For complex branching workflows, LangGraph is better. For this linear pipeline on GCP, ADK is the right fit.
**Status:** Active

## [2026-03-27] Decision: Orchestration Pattern — SequentialAgent
**Choice:** ADK SequentialAgent (Agent 1 → Agent 2 → Agent 3)
**Alternatives considered:** LLM-driven delegation (transfer_to_agent), ParallelAgent, custom orchestrator
**Why:** Customer support is inherently sequential (classify → retrieve → evaluate). LLM routing adds ~500ms latency + non-determinism for zero benefit.
**Status:** Active

## [2026-03-27] Decision: LLM Model — Gemini 2.0 Flash
**Choice:** gemini-2.0-flash via Vertex AI
**Alternatives considered:** Gemini 2.5 Pro (smarter but slower/costlier), Claude, GPT-5
**Why:** Fast (~500-800ms), cheap ($0.10/1M input tokens), sufficient quality for all three agents. Pure Google ecosystem.
**Status:** Changed → gemini-2.5-flash (see entry above). Reason: 404 on new project, 2.5 is newer/better.

## [2026-03-27] Decision: Embedding Model — gemini-embedding-001 at 768 dims
**Choice:** gemini-embedding-001 with 768 dimensions
**Alternatives considered:** text-embedding-005 (768d, older), multilingual-e5 (open), 3072d full resolution
**Why:** Best quality Google embedding model. 768 is optimal for our data volume. Can scale to 3072 for higher precision.
**Status:** Active

## [2026-03-27] Decision: Dense Vector Search — FAISS (local)
**Choice:** FAISS (faiss-cpu, free, local)
**Alternatives considered:** Vertex AI Vector Search ($68.50/mo minimum always-on), Vertex AI Search (free 10K queries/mo), Pinecone, Weaviate
**Why:** Free, instant for <100K chunks, runs anywhere. Production path: Vertex AI Vector Search for managed scaling.
**Status:** Active

## [2026-03-27] Decision: Sparse Search — BM25 via rank_bm25
**Choice:** Python rank_bm25 library
**Alternatives considered:** Elasticsearch, SPLADE
**Why:** Standard keyword matching. Catches exact matches dense misses (e.g., error codes "E-401"). ES is overkill, SPLADE adds complexity for marginal gain.
**Status:** Active

## [2026-03-27] Decision: Hybrid Merge — Reciprocal Rank Fusion (RRF)
**Choice:** RRF algorithm
**Alternatives considered:** Linear combination, Convex combination
**Why:** Parameter-free, proven in research, fair weighting of dense + sparse without tuning.
**Status:** Active

## [2026-03-27] Decision: Reranking — Vertex AI Ranking API
**Choice:** semantic-ranker-default-004
**Alternatives considered:** Cohere Rerank, cross-encoder models
**Why:** Google-native, 2x faster than competitors, 1024 token context per record.
**Status:** Active

## [2026-03-27] Decision: Chunking — Fixed-length 512 tokens, 128 overlap
**Choice:** Fixed-length chunking
**Alternatives considered:** Semantic chunking, parent-child, layout parser (Document AI)
**Why:** Simple, predictable, good for structured markdown docs. Semantic chunking is slower/less predictable. Layout parser adds Document AI cost.
**Status:** Active

## [2026-03-27] Decision: RAG Evaluation — LLM-as-judge (custom prompts)
**Choice:** Gemini evaluates responses using custom prompts (same metrics as RAGAS + DeepEval)
**Alternatives considered:** RAGAS library, DeepEval library, Vertex AI Gen AI Evaluation
**Why:** Real-time per-query evaluation (not batch). Zero external deps. ONE Gemini call checks all metrics. Full control over CX-specific evaluation criteria. RAGAS/DeepEval are just prompts under the hood — we wrote the same prompts, customized for customer support.
**Status:** Active

## [2026-03-27] Decision: Analytics — BigQuery with SQLite fallback
**Choice:** BigQuery (production) + SQLite (local dev)
**Alternatives considered:** PostgreSQL, Elasticsearch, Snowflake
**Why:** GCP-native, serverless, SQL, free tier (10GB), dashboards via Looker. SQLite for offline dev.
**Status:** Active

## [2026-03-27] Decision: Input Guardrails — Regex + Gemini
**Choice:** Custom guardrails: regex PII detection + Gemini-based injection/topic detection
**Alternatives considered:** NVIDIA NeMo Guardrails, Google Cloud DLP API, Guardrails AI
**Why:** Lightweight, no extra dependencies, customizable. For enterprise: add Cloud DLP API for HIPAA/FERPA-grade PII detection.
**Status:** Active

## [2026-03-27] Decision: Semantic Cache — FAISS similarity cache
**Choice:** FAISS-based semantic cache (threshold 0.95)
**Alternatives considered:** Redis/Memorystore (exact match), GPTCache, no caching
**Why:** 40-60% cost savings on repeated/similar queries. Cache hit = skip all agents = instant response. FAISS is free and local.
**Status:** Active

## [2026-03-27] Decision: Python Version — 3.13
**Choice:** Python 3.13.11
**Alternatives considered:** Python 3.14.3 (installed, but too new for some packages)
**Why:** 3.14 may lack wheel support for faiss-cpu and other packages. 3.13 is stable and widely supported.
**Status:** Active
