# Interview Prep: AI Engineer @ GTS (Global Technology Solutions)

**Interviewer:** Aaron Schroeder, Director of AI
**Role:** AI Engineer
**Key insight:** Aaron values practical, production-ready AI over hype. He comes from TTEC Digital, is governance-first, and is a Vertex AI expert. Speak in production terms, not research terms.

---

## Table of Contents

1. [60-Second Elevator Pitch](#1-60-second-elevator-pitch)
2. [Architecture Walkthrough](#2-architecture-walkthrough)
3. [Why This Architecture](#3-why-this-architecture)
4. [Why LLM-as-Judge](#4-why-llm-as-judge-not-ragasdeepeval)
5. [Every Component: What, Why, Alternatives](#5-every-component--what-why-alternatives)
6. [How GTS & Enterprises Do It Differently](#6-how-gts--enterprises-do-it-differently)
7. [Anticipated Interview Questions & Answers](#7-anticipated-interview-questions--answers)
8. [Technical Deep Dives](#8-technical-deep-dives)
9. [About GTS](#9-about-gts-company-context)

---

## 1. 60-Second Elevator Pitch

> "I built a production-grade Agentic RAG system for customer support on GCP using Google ADK. It starts with input guardrails -- PII redaction, prompt injection detection, and topic boundaries -- before any query reaches the AI. Then a semantic cache checks if a similar query was already answered, giving 40-60% cost savings. For new queries, three agents work in sequence: Agent 1 does advanced query processing -- intent detection, query rewriting, expansion, and HyDE. Agent 2 does hybrid retrieval -- dense vectors plus BM25 sparse search -- with Vertex AI reranking, then generates a grounded response. Agent 3 evaluates the response using LLM-as-judge metrics -- the same metrics as RAGAS and DeepEval but with custom prompts -- and decides to approve, revise, or escalate. Every interaction is logged to BigQuery with full metrics for dashboards and continuous improvement."

**Practice this until you can say it in 55-60 seconds without reading. Hit every bolded concept naturally.**

---

## 2. Architecture Walkthrough

### What happens when a customer sends a message (step by step):

```
Customer Query
     |
     v
[1] GUARDRAILS (pre-processing, before any LLM call)
     |-- PII Detector: regex patterns catch SSN, credit cards, phone, email, IP
     |   -> Redacts: "My SSN is 123-45-6789" -> "My SSN is [REDACTED_SSN]"
     |-- Injection Detector: 14 regex patterns for jailbreak attempts
     |   -> "Ignore previous instructions" -> BLOCKED, returns safe response
     |-- Topic Boundary: ensures query is about billing/technical/account/general
     |   -> "Write me a Python script" -> BLOCKED, returns redirect message
     |
     v
[2] SEMANTIC CACHE (FAISS-based, similarity threshold 0.70)
     |-- Embeds query with gemini-embedding-001 (3072 dims)
     |-- Cosine similarity search against cached queries
     |-- If hit (>= 0.70): return cached response instantly, skip all agents
     |-- If miss: proceed to agents
     |-- LRU eviction, 1-hour TTL, max 1000 entries
     |
     v
[3] AGENT 1: Query Processing (LlmAgent, temp=0.1)
     |-- Intent detection: billing | technical | account | general
     |-- Sentiment: positive | neutral | negative | frustrated
     |-- Urgency: low | medium | high | critical
     |-- Query rewriting: 2-3 clearer search queries
     |-- Query expansion: 3-5 related terms/synonyms
     |-- HyDE: generates hypothetical answer for embedding similarity
     |-- Writes classification to session state via tool_context.state
     |
     v
[4] AGENT 2: Retrieval & Generation (LlmAgent, temp=0.3)
     |-- Reads triage_classification from session state
     |-- DENSE SEARCH: FAISS (IndexFlatIP, cosine similarity)
     |   -> Main query: top 10 results
     |   -> Expanded queries (up to 2): top 5 each
     |-- SPARSE SEARCH: BM25 (rank_bm25 library)
     |   -> Main query: top 10 results
     |   -> Expanded queries (up to 2): top 5 each
     |-- HYBRID MERGE: Reciprocal Rank Fusion (k=60)
     |   -> Merges dense + sparse, parameter-free
     |-- OPTIONAL FILTER: by intent/category (if >= 3 results remain)
     |-- RERANKING: Vertex AI Ranking API (semantic-ranker-default-004)
     |   -> Top 15 candidates in, top 5 out
     |-- GENERATION: Gemini 2.5 Flash generates grounded response
     |   -> Cites knowledge base articles by title
     |   -> Matches tone to customer sentiment
     |   -> Never fabricates information
     |
     v
[5] AGENT 3: Evaluation (LlmAgent, temp=0.1)
     |-- LLM-as-Judge scoring (all in one Gemini call):
     |   -> Faithfulness (0.0-1.0): % of claims backed by retrieved docs
     |   -> Answer Relevance (0.0-1.0): does it answer the question?
     |   -> Context Relevance (0.0-1.0): were retrieved docs useful?
     |   -> Hallucination check (bool)
     |   -> Bias check (bool)
     |   -> Toxicity check (bool)
     |   -> Tone check (bool): matches customer sentiment?
     |   -> PII check (bool): no PII leakage in response?
     |-- Decision:
     |   -> overall >= 0.8 AND all checks pass -> APPROVE
     |   -> overall >= 0.6 OR minor issues -> REVISE (with specific feedback)
     |   -> overall < 0.6 OR critical issue -> ESCALATE to human
     |-- Logs FULL interaction to BigQuery via log_interaction tool
     |
     v
[6] BIGQUERY ANALYTICS
     |-- Every field logged: timestamp, session_id, original_query,
     |   rewritten_queries, intent, sentiment, urgency, retrieved_doc_ids,
     |   num_docs_retrieved, all eval scores, decision, cache_hit
     |-- Feeds Looker dashboards for CX leaders
     |-- Enables continuous improvement (find low-scoring patterns)
     |
     v
Customer receives response (or escalation to human agent)
```

### Key implementation details to mention:

- **ADK SequentialAgent** orchestrates all 3 agents -- deterministic, no LLM routing overhead
- **Session state** (`tool_context.state`) passes data between agents (triage_classification, retrieved_docs, qa_evaluation)
- **Output keys** (`output_key="triage_result"`) allow downstream agents to reference upstream outputs in their prompts via `{triage_result}`
- **Temperature tuning**: 0.1 for classification/evaluation (consistency), 0.3 for generation (natural tone)
- **Pydantic Settings** centralizes all config -- nothing hardcoded

---

## 3. Why This Architecture

### Why 3 agents instead of 1?

| Reason | Detail |
|--------|--------|
| **Separation of concerns** | Each agent has one job. Query processing is not retrieval is not evaluation. |
| **Different temperatures** | Classification needs 0.1 (deterministic). Generation needs 0.3 (natural). Evaluation needs 0.1 (consistent). One agent cannot have three temperatures. |
| **Failure isolation** | If retrieval fails, evaluation still catches it and escalates. A monolithic agent would just produce garbage. |
| **Measurable per-stage metrics** | You can measure: "Is Agent 1 classifying correctly? Is Agent 2 retrieving relevant docs? Is Agent 3 evaluating fairly?" One agent gives you one opaque metric. |
| **Independent testing** | Each agent can be unit tested with mocked inputs. |
| **Independent scaling** | In production, Agent 2 (retrieval) is the bottleneck -- you can scale it independently. |

### Why SequentialAgent (not LLM-driven routing)?

| Factor | SequentialAgent | LLM-Driven Routing |
|--------|----------------|-------------------|
| **Latency** | Zero routing overhead | +500ms per routing decision |
| **Determinism** | Always goes 1 -> 2 -> 3 | LLM might skip steps or loop |
| **Auditability** | Fully traceable, every step runs | Hard to explain why agent X was chosen |
| **Testing** | Unit test each stage | Non-deterministic, flaky tests |
| **Cost** | No routing LLM calls | Extra LLM calls for routing |
| **When to use routing** | Complex branching, multi-domain, user-directed flow | Simple, always-sequential pipelines like ours |

**Key talking point:** "Customer support is inherently sequential. Every query needs classification, retrieval, and evaluation -- always, in that order. LLM routing adds latency and non-determinism for zero benefit."

### Why Google ADK (not LangGraph)?

| Factor | Google ADK | LangGraph |
|--------|-----------|-----------|
| **GCP integration** | Native (one-command Cloud Run deploy) | Requires manual GCP wiring |
| **API simplicity** | `SequentialAgent(sub_agents=[...])` | Graph nodes, edges, state schemas |
| **Job fit** | Job posting asks for ADK | Would still be a great choice |
| **Ecosystem** | Google-maintained, Vertex AI native | LangChain ecosystem, more community |
| **State management** | `tool_context.state` (simple dict) | TypedDict with reducers (more powerful) |
| **Complex workflows** | Limited -- good for linear pipelines | Superior for branching, cycles, human-in-the-loop |

**What to say:** "I chose ADK because the job asks for it, it's native to GCP which is GTS's ecosystem, and for a sequential pipeline it's simpler. But I want to be honest -- LangGraph has superior state management and graph orchestration. If we needed complex branching workflows, conditional routing, or checkpoint-based time-travel debugging, I'd choose LangGraph."

---

## 4. Why LLM-as-Judge (Not RAGAS/DeepEval)

### What RAGAS and DeepEval actually do under the hood

This is the insight most people miss:

```
RAGAS "faithfulness" metric:
  1. Takes your response + context
  2. Constructs a prompt: "List all claims in this response..."
  3. Sends it to GPT-4 / Gemini
  4. Constructs another prompt: "For each claim, check if context supports it..."
  5. Sends that to GPT-4 / Gemini
  6. Parses the output and calculates a score

DeepEval "hallucination" metric:
  1. Takes your response + context
  2. Constructs a prompt: "Does this response contain info not in context?"
  3. Sends it to GPT-4 / Gemini
  4. Parses the output
```

**They are just prompts to LLMs.** The "framework" is prompt engineering + JSON parsing.

### Why we built custom instead

| Factor | RAGAS/DeepEval | Our LLM-as-Judge |
|--------|---------------|-------------------|
| **Execution** | Batch (run after the fact) | Real-time (per-query, in the pipeline) |
| **Dependencies** | pip install ragas (+ openai + langchain + datasets) | Zero external deps -- just Gemini |
| **LLM calls** | 2-4 calls per metric (RAGAS uses separate calls per metric) | ONE call for all 8 metrics |
| **Customization** | Generic prompts | CX-specific: tone matching, escalation rules, billing-specific checks |
| **Cost** | Multiple LLM calls per evaluation | Single Gemini call |
| **Latency** | Seconds (multiple serial LLM calls) | ~500ms (one call) |
| **Integration** | Separate pipeline | Built into Agent 3, writes to BigQuery |

### When you WOULD use RAGAS/DeepEval

- **Benchmarking**: When you need to compare your system against published baselines
- **Initial development**: Quick smoke test before building custom evaluation
- **Publishing scores**: Academic or marketing contexts where "RAGAS score = 0.87" carries weight
- **Team standardization**: When multiple teams need identical eval methodology

**What to say:** "RAGAS and DeepEval are great tools, but under the hood they're just prompts to LLMs. I wrote the same prompts -- faithfulness, answer relevance, context relevance, hallucination -- but customized for customer support and running in real-time as part of the pipeline, not as a batch job after the fact. One Gemini call scores all 8 metrics. Zero external dependencies."

---

## 5. Every Component -- What, Why, Alternatives

| Component | What We Use | Why | Alternatives | Why Not |
|-----------|------------|-----|-------------|---------|
| **Agent Framework** | Google ADK | Job requirement, native GCP, simple for sequential pipeline | LangGraph, CrewAI, AutoGen, Semantic Kernel | LangGraph is better for complex graphs; CrewAI/AutoGen are role-play focused |
| **Orchestration** | SequentialAgent | Deterministic, zero-overhead routing | LLM delegation, ParallelAgent | Routing adds latency + non-determinism for linear flow |
| **LLM** | Gemini 2.5 Flash | Fast (~500-800ms), cheap ($0.10/1M input), sufficient quality | Gemini 2.5 Pro, Claude, GPT-4o | 2.5 Pro is smarter but slower/costlier; others break Google ecosystem |
| **Embeddings** | gemini-embedding-001 (3072d) | Best Google embedding model, good balance of quality vs. compute | text-embedding-005, multilingual-e5, OpenAI ada-002 | text-embedding-005 is older; open models need self-hosting |
| **Dense Search** | FAISS (faiss-cpu, IndexFlatIP) | Free, local, instant for <100K chunks | Vertex AI Vector Search, Pinecone, Weaviate | Vertex AI = $68.50/mo minimum; Pinecone/Weaviate = non-GCP |
| **Sparse Search** | rank_bm25 (Python) | Standard keyword matching, catches exact terms dense misses | Elasticsearch, SPLADE | ES is overkill for this scale; SPLADE adds complexity for marginal gain |
| **Hybrid Merge** | Reciprocal Rank Fusion (k=60) | Parameter-free, proven in research, fair weighting | Linear combination, convex combination | Linear/convex require tuning weights |
| **Reranking** | Vertex AI Ranking API (semantic-ranker-default-004) | Google-native, 2x faster than competitors, 1024 token context | Cohere Rerank, cross-encoder models | Cohere = non-GCP; cross-encoders = self-hosted, slower |
| **Chunking** | Fixed-length 512 tokens, 128 overlap | Simple, predictable for structured markdown | Semantic chunking, parent-child, Document AI layout parser | Semantic is slower/less predictable; layout parser adds Document AI cost |
| **Analytics** | BigQuery + SQLite fallback | GCP-native, serverless, SQL, free tier (10GB), Looker dashboards | PostgreSQL, Elasticsearch, Snowflake | BQ is serverless and GCP-native |
| **Deployment** | Cloud Run (via ADK) | One-command deploy, auto-scaling, GCP-native | GKE, App Engine, Cloud Functions | GKE is overkill; Functions has cold start issues |
| **Session State** | ADK tool_context.state | Built into ADK, shared across agents in a session | Redis, Firestore, custom | ADK state is sufficient for single-session flow |
| **Evaluation** | LLM-as-Judge (custom Gemini prompts) | Real-time, zero deps, one call for all metrics, CX-specific | RAGAS, DeepEval, Vertex AI Gen AI Eval | RAGAS/DeepEval are batch, multi-call, generic |
| **Guardrails** | Regex PII + regex injection + regex topic | Lightweight, no extra deps, customizable | NVIDIA NeMo Guardrails, Cloud DLP API, Guardrails AI | NeMo adds weight; Cloud DLP for enterprise upgrade path |
| **Cache** | FAISS semantic cache (0.70 threshold, LRU, 1hr TTL) | 40-60% cost savings, free, local | Redis/Memorystore (exact match), GPTCache | Exact match misses paraphrases; GPTCache is extra dep |

---

## 6. How GTS & Enterprises Do It Differently

### Google CCAI Architecture (What GTS Deploys for Enterprise Clients)

```
Customer (Phone/Chat/Email)
         |
         v
  [Dialogflow CX]  <-- Conversational AI, multi-turn state machine
         |
    +---------+---------+
    |         |         |
    v         v         v
 [Intent    [Agent    [Virtual
  Router]   Assist]   Agent]
    |         |         |
    v         v         v
  [CCAI Insights]  <-- Sentiment, topics, compliance monitoring
         |
         v
  [Vertex AI Search / RAG]  <-- Enterprise knowledge retrieval
         |
         v
  [Cloud DLP / Security]  <-- HIPAA/FERPA-grade PII handling
         |
         v
  Human Agent Handoff (via LivePerson, Genesys, NICE, etc.)
```

### Key Differences: Our System vs. Enterprise CCAI

| Aspect | Our System | Enterprise (CCAI) |
|--------|-----------|-------------------|
| **Conversation engine** | ADK SequentialAgent | Dialogflow CX (visual state machine) |
| **Multi-turn** | Single-turn (session state only) | Full conversation tree with context carryover |
| **Knowledge retrieval** | Custom hybrid RAG (FAISS + BM25 + rerank) | Vertex AI Search (managed, turnkey) |
| **PII handling** | Regex patterns (5 types) | Cloud DLP API (150+ info types, HIPAA/FERPA certified) |
| **Telephony** | None | CCAI telephony integration (SIP, PSTN) |
| **Agent assist** | AI-only responses | Real-time suggestions to human agents |
| **Observability** | BigQuery logging | CCAI Insights + Cloud Monitoring + Cloud Trace |
| **Compliance** | Basic (our guardrails) | SOC 2, HIPAA BAA, FedRAMP, FERPA |
| **Scale** | Demo-ready | 10K+ concurrent sessions |
| **Cost** | ~$0 (free tiers) | $10K-$100K+/month |

### What we already have that enterprises need

- Input guardrails (PII, injection, topic) -- enterprises just use more powerful versions
- Semantic caching -- enterprises use Redis/Memorystore but same concept
- Quality evaluation -- enterprises run this, just with more metrics
- Analytics pipeline -- BigQuery is the standard enterprise choice
- Hybrid retrieval -- same pattern, just with managed vector DBs

### What we would add for enterprise production

| Gap | Enterprise Solution |
|-----|-------------------|
| **Observability** | Cloud Trace for latency, Cloud Monitoring for uptime, error budgets |
| **Feedback loop** | Customer ratings feed back into eval metrics, retrain triggers |
| **Multi-turn conversations** | ADK Session + conversation history in Firestore |
| **Model fallback** | Primary: Gemini 2.5 Flash. Fallback: Gemini 2.5 Pro. Circuit breaker pattern. |
| **A/B testing** | Route % of traffic to new prompts/models, measure CSAT delta |
| **CI/CD for prompts** | Prompt versioning in Git, automated eval suite on PR, promotion gates |
| **PII at scale** | Cloud DLP API for HIPAA/FERPA compliance |
| **Load testing** | Locust or k6 against Cloud Run, auto-scaling validation |
| **Human-in-the-loop** | Escalation queue in the contact center platform (Genesys, NICE, etc.) |
| **Knowledge base refresh** | Scheduled re-indexing pipeline (Cloud Scheduler + Cloud Functions) |

---

## 7. Anticipated Interview Questions & Answers

### Q1: Walk me through what happens when a customer sends a message.

**Answer:** "Three phases. First, pre-processing: the query hits guardrails -- regex-based PII redaction strips out SSNs, credit cards, phone numbers, emails, and IPs. Prompt injection detection checks against 14 known patterns. Topic boundary enforcement ensures we're talking about customer support, not writing code or giving medical advice. Second, the semantic cache embeds the query and checks FAISS for a similar query answered within the last hour -- if similarity is above 0.70, we return the cached response instantly and skip everything else.

Third, the three-agent pipeline. Agent 1 classifies intent, sentiment, urgency, rewrites the query into 2-3 clearer search queries, expands with synonyms, and generates a hypothetical answer for HyDE. Agent 2 takes those queries and runs hybrid retrieval -- FAISS dense search plus BM25 sparse search -- merges results with Reciprocal Rank Fusion, optionally filters by intent, sends the top 15 candidates to Vertex AI's reranker, and generates a grounded response from the top 5 documents. Agent 3 evaluates the response on 8 metrics -- faithfulness, answer relevance, context relevance, hallucination, bias, toxicity, tone, and PII leakage -- then decides approve, revise, or escalate. Everything gets logged to BigQuery."

### Q2: Why ADK instead of LangGraph?

**Answer:** "Three reasons. First, the job posting asks for ADK, so I wanted to demonstrate fluency with the tool GTS uses. Second, ADK is native to GCP -- one-command Cloud Run deploy, native Vertex AI integration, no glue code. Third, for a sequential pipeline like this, ADK's SequentialAgent is simpler than LangGraph's graph nodes and edges.

That said, I want to be candid -- LangGraph is more powerful for complex workflows. It has typed state with reducers, checkpoint-based time-travel debugging, conditional edges, and cycles. If we needed complex branching, human-in-the-loop interrupts, or multi-path routing, I'd choose LangGraph. For a linear pipeline on GCP, ADK is the right fit."

### Q3: How would you scale to 10,000 concurrent users?

**Answer:** "Four changes. First, swap FAISS for Vertex AI Vector Search -- it's a managed service that auto-scales and supports streaming updates. Second, deploy on Cloud Run with aggressive auto-scaling settings -- Cloud Run handles concurrent requests natively, and each agent call is stateless.

Third, the semantic cache moves from in-memory FAISS to Redis (Memorystore) -- shared across all Cloud Run instances with sub-millisecond lookups. Fourth, BM25 moves from in-memory rank_bm25 to Elasticsearch on Elastic Cloud or Cloud Search -- the Python library doesn't share state across instances.

The pipeline architecture doesn't change. The agents, prompts, and evaluation logic stay identical. We're just swapping local components for managed services."

### Q4: What about latency?

**Answer:** "Let me break it down by component. Guardrails: regex, sub-1ms. Cache hit: ~50ms (one embedding call + FAISS lookup). Cache miss full pipeline: Agent 1 (Gemini call ~500ms) + Agent 2 (embedding ~100ms + FAISS ~5ms + BM25 ~10ms + reranking ~200ms + Gemini generation ~500ms) + Agent 3 (Gemini eval ~500ms) = roughly 1.8 seconds end-to-end.

For production optimization: parallel dense+sparse search saves ~100ms. Streaming the response from Agent 2 gives perceived latency under 1 second. The cache hit rate of 40-60% means most users see <100ms. The reranker is the most expensive single step -- you could skip it for low-urgency queries to save 200ms."

### Q5: How do you know answers are accurate?

**Answer:** "Three layers. First, grounding: Agent 2 is instructed to only use information from retrieved documents and cite sources by title. Second, evaluation: Agent 3 scores faithfulness -- it extracts every factual claim from the response and checks each one against the retrieved context. Faithfulness below 0.8 triggers revision or escalation. Third, hallucination detection: a separate boolean check specifically for information not present in the context.

On top of that, every interaction is logged to BigQuery with all scores. We can dashboard faithfulness over time, find queries where hallucination was flagged, and use that data to improve prompts or add missing knowledge base articles."

### Q6: What if the knowledge base doesn't have the answer?

**Answer:** "Three things happen. Agent 2's retrieval returns low-relevance documents. The agent is instructed to say honestly 'I don't have enough information to answer this' and recommend escalation. Agent 3's context relevance score will be low, answer relevance will be low, and it will trigger an ESCALATE decision. The interaction gets logged with these low scores, so we can find knowledge gaps -- queries that consistently get escalated tell us exactly what articles we need to write.

In a contact center deployment, ESCALATE routes to a human agent with the full context: the customer's query, what was retrieved, and why the AI couldn't answer."

### Q7: How is this different from OmniBot?

**Answer:** "OmniBot is GTS's production chatbot product built on Dialogflow CX -- it's a visual state machine for multi-turn conversations with telephony integration, agent assist, and enterprise compliance. My system is an Agentic RAG pipeline -- it's the intelligence layer that could sit behind something like OmniBot.

Specifically, my system adds: advanced query processing (HyDE, query expansion), hybrid retrieval with reranking (not just vector search), real-time quality evaluation with approve/revise/escalate, and analytics logging. These are capabilities that could enhance OmniBot's knowledge retrieval -- today OmniBot likely uses Vertex AI Search or Dialogflow knowledge connectors, which are good but don't have multi-stage retrieval or real-time evaluation."

### Q8: Why not just use Vertex AI Search?

**Answer:** "Vertex AI Search is excellent -- it's turnkey, managed, and handles chunking, indexing, and retrieval automatically. For many use cases, it's the right choice.

I built custom hybrid RAG for three reasons. First, learning: building each component taught me how retrieval actually works -- BM25, embeddings, RRF, reranking -- so I can debug and optimize when the managed service doesn't work perfectly. Second, control: I can tune chunk sizes, overlap, fusion parameters, reranking thresholds, and add HyDE -- Vertex AI Search is a black box. Third, the evaluation layer: Vertex AI Search gives you results, not quality scores. My Agent 3 evaluates every response before it reaches the customer.

In production at GTS, I'd likely use Vertex AI Search for the retrieval piece and layer evaluation on top."

### Q9: What about compliance and security?

**Answer:** "Current system has three guardrail layers: PII redaction (5 types via regex), prompt injection detection (14 patterns), and topic boundary enforcement. The evaluation agent also checks for PII leakage in responses, bias, and toxicity.

For enterprise compliance -- which is critical in GTS's verticals like healthcare and public sector -- I'd upgrade to: Cloud DLP API for HIPAA/FERPA-grade PII detection (150+ info types vs. our 5), VPC Service Controls for network isolation, Cloud Audit Logs for SOC 2 compliance, and data residency controls for GDPR. The guardrail architecture stays the same -- we just swap regex for Cloud DLP and add the GCP security services GTS already uses."

### Q10: Why 3 agents instead of 1?

**Answer:** "Five reasons. First, separation of concerns -- each agent has one clear responsibility. Second, different temperatures -- classification needs 0.1 for consistency, generation needs 0.3 for natural language, evaluation needs 0.1 for reliable scoring. You can't do that in one agent. Third, failure isolation -- if retrieval fails, the evaluation agent catches it and escalates rather than producing a bad response. Fourth, measurability -- I can separately measure classification accuracy, retrieval quality, and evaluation reliability. Fifth, testability -- each agent can be unit tested with mocked inputs from the previous stage.

A single agent would be faster but opaque. You'd get one response with no visibility into whether the query was classified correctly, whether the right documents were retrieved, or whether the response was actually faithful to the context."

### Q11: How would you handle multi-turn conversations?

**Answer:** "ADK has built-in session management. Right now I'm using `tool_context.state` for within-session state passing between agents. For multi-turn, I'd extend this in three ways.

First, conversation history: store the last N turns in session state so agents have context. Agent 1 would use conversation history to resolve pronouns -- 'What about the other plan?' refers to a plan mentioned earlier. Second, persistent sessions: store session state in Firestore with a session ID, so conversations survive across Cloud Run instances. Third, context window management: for long conversations, summarize older turns rather than passing the full history to stay within token limits.

The agent pipeline doesn't change. Agent 1 just gets richer context, Agent 2 can reference prior retrievals, and Agent 3 evaluates coherence across the conversation."

### Q12: What metrics would you show a CX leader?

**Answer:** "I'd build a Looker dashboard with four sections.

**Operational**: total queries handled, cache hit rate (cost savings), average response time, escalation rate, queries by intent and urgency.

**Quality**: average faithfulness score, average answer relevance, hallucination rate, % of responses approved vs. revised vs. escalated, trend over time.

**Customer Experience**: sentiment distribution (how many frustrated customers), resolution rate (approved on first pass), most common intents (where to invest in knowledge base).

**Cost**: total LLM calls, tokens consumed, cost per query, cache savings (queries not sent to LLM), projected monthly spend at current volume.

All of this data is already being logged to BigQuery by Agent 3. The dashboard is just SQL queries."

---

## 8. Technical Deep Dives

### HyDE (Hypothetical Document Embeddings)

**What:** Generate a hypothetical answer to the query, then embed *that* instead of the query. The hypothesis is closer in embedding space to actual answer documents than the question is.

**Example:**
- Query: "How do I reset my password?"
- HyDE: "To reset your password, go to Settings > Security > Reset Password. Enter your email and click the reset link sent to your inbox."
- The HyDE embedding is closer to actual password-reset docs than "How do I reset my password?" would be.

**Why it works:** Questions and answers live in different regions of embedding space. HyDE bridges that gap.

**When it hurts:** If the hypothetical answer is wrong, it pulls retrieval in the wrong direction. That's why we also search with the original query and expanded queries.

### BM25 (Best Match 25)

**What:** Classic term-frequency algorithm. Ranks documents by how often query terms appear, normalized by document length and collection statistics (IDF).

**Formula (simplified):** `score = sum(IDF(term) * TF(term, doc) * (k1 + 1) / (TF + k1 * (1 - b + b * docLen/avgDocLen)))`

**Why it matters for RAG:** Dense embeddings miss exact keyword matches. If a customer asks about error code "E-401", BM25 will find documents containing that exact string. Dense search might match semantically similar errors instead.

**Our implementation:** `rank_bm25` Python library. In-memory, no server needed. For production scale: Elasticsearch.

### Reciprocal Rank Fusion (RRF)

**What:** Merges multiple ranked lists into one. For each document, `RRF_score = sum(1 / (k + rank))` across all lists where it appears. k=60 is standard (from the original paper by Cormack et al.).

**Why:** Parameter-free. No need to tune weights between dense and sparse scores (which are on different scales). A document ranked #1 by both systems gets a higher RRF score than a document ranked #1 by one and absent from the other.

**Example:**
- Dense ranks doc A at #1, doc B at #3
- Sparse ranks doc B at #1, doc A at #5
- Doc A RRF: 1/61 + 1/65 = 0.0318
- Doc B RRF: 1/63 + 1/61 = 0.0323
- Doc B wins because it's consistently near the top in both systems.

### FAISS (Facebook AI Similarity Search)

**What:** Library for efficient dense vector similarity search. We use `IndexFlatIP` (inner product on L2-normalized vectors = cosine similarity).

**Why IndexFlatIP:** Exact search, no approximation. For <100K vectors, brute-force is fast enough (<5ms). For millions of vectors: switch to `IndexIVFFlat` (approximate) or `IndexHNSW`.

**Production path:** Vertex AI Vector Search (managed FAISS-like service with auto-scaling, streaming updates, and filtering).

### Chunking Strategy

**Our choice:** Fixed-length, 512 tokens, 128-token overlap.

**Why 512:** Matches well with embedding model context. Large enough to capture a complete thought. Small enough for precise retrieval.

**Why 128 overlap:** Ensures no information is lost at chunk boundaries. A sentence that spans two chunks appears in both.

**Alternatives we considered:**
- Semantic chunking (split at topic boundaries): slower, less predictable chunk sizes
- Parent-child (small chunks for retrieval, return parent for context): more complex, better for long documents
- Document AI layout parser: adds cost, better for PDFs with complex layouts

### Embedding Dimensions (3072)

**Model:** gemini-embedding-001 supports up to 3072 dimensions. We use 3072 (full resolution).

**Why 3072:** Maximum retrieval precision. At our data volume (<100K chunks), the memory cost is acceptable: 3072 * 4 bytes * 100K docs = ~1.2GB. The quality improvement from full resolution is significant for distinguishing similar knowledge base articles (e.g., "password reset" vs. "2FA recovery").

**When to use 768:** Large-scale deployments (millions of docs) where memory and compute cost matters more than marginal quality gain.

### Vertex AI Ranking API

**Model:** `semantic-ranker-default-004`

**What it does:** Cross-encoder reranking. Unlike bi-encoder embeddings (which encode query and document separately), the reranker encodes query+document together. This captures fine-grained relevance signals that bi-encoders miss.

**Why it's after RRF:** Reranking is expensive (one model call per query-document pair). We only rerank the top 15 candidates from RRF, not all documents.

**Context limit:** 1024 tokens per record. Our 512-token chunks fit within this.

---

## 9. About GTS (Company Context)

### What GTS Does

Global Technology Solutions (GTS) is a CX/contact center transformation company. They help enterprises modernize their customer experience operations -- moving from legacy IVR systems and basic chatbots to AI-powered solutions.

### Their Products

| Product | What It Does |
|---------|-------------|
| **OmniBot** | AI chatbot platform built on Dialogflow CX. Multi-channel (web, phone, SMS). Their flagship conversational AI product. |
| **OmniAssistantAI** | Real-time agent assist -- AI suggests responses to human agents during live conversations. Reduces handle time, improves consistency. |
| **OmniDocsAI** | Document processing and knowledge management. Likely uses Document AI for extraction. |
| **OmniCompliance** | Compliance monitoring for contact centers. Call recording analysis, PCI/HIPAA compliance checks, quality scoring. |

### Their GCP Partnership

- **Google Cloud CCAI reseller** -- they sell and implement Google's Contact Center AI (CCAI) for enterprise clients
- **Vertex AI users** -- their AI products run on Vertex AI (Gemini, embeddings, search)
- **Google Cloud Partner** -- they have Google Cloud certifications and co-sell with Google

### Their Verticals

| Vertical | Why It Matters |
|----------|---------------|
| **Healthcare** | HIPAA compliance is mandatory. PII handling is critical. This is why our guardrails matter. |
| **SLED (State/Local/Education)** | Government contracts require FedRAMP, FERPA. Data residency matters. |
| **Public Sector** | Similar to SLED. Security-first. Often air-gapped environments. |
| **Education** | FERPA compliance. Student data protection. |

### Aaron Schroeder's Background

- **Previous:** TTEC Digital (major CX outsourcing company) -- he's seen enterprise CX at scale
- **Philosophy:** Governance-first AI. He cares about guardrails, compliance, and measurability before model performance.
- **Technical depth:** Vertex AI expert. He'll know if you're hand-waving about GCP services.
- **What impresses him:** Production thinking. "How would you deploy this?" "How would you monitor this?" "What happens when it fails?"

### Tailoring Your Answers for Aaron

| When he asks about... | Emphasize... |
|----------------------|-------------|
| Architecture | Guardrails FIRST, then capabilities |
| Evaluation | Measurability, BigQuery analytics, continuous improvement |
| Scale | Managed GCP services (Vertex AI Search, Cloud Run, Memorystore) |
| Compliance | Our guardrail architecture + Cloud DLP upgrade path |
| Cost | Cache savings, Gemini Flash pricing, pay-per-query Cloud Run |
| Innovation | HyDE, hybrid retrieval, real-time LLM-as-judge |

---

## Quick Reference Card (Print This)

```
SYSTEM FLOW:
  Query -> Guardrails (PII/inject/topic) -> Cache -> Agent 1 (classify)
  -> Agent 2 (retrieve+generate) -> Agent 3 (evaluate) -> BigQuery + Response

TECH STACK:
  ADK SequentialAgent | Gemini 2.5 Flash | gemini-embedding-001 (3072d)
  FAISS + BM25 + RRF + Vertex AI Reranker | BigQuery | Cloud Run

3 AGENTS:
  Agent 1: Query Processing (temp=0.1) - intent, sentiment, urgency, HyDE
  Agent 2: Retrieval & Generation (temp=0.3) - hybrid search, grounded response
  Agent 3: Evaluation (temp=0.1) - 8 metrics, approve/revise/escalate

KEY NUMBERS:
  Cache hit rate: 40-60% | Cache threshold: 0.70 | Chunks: 512 tokens
  RRF k=60 | Top-K: 5 | Rerank candidates: 15 | Embedding dims: 3072

WHY ADK: Job asks for it, native GCP, simpler for sequential
WHY 3 AGENTS: Separation of concerns, different temps, failure isolation
WHY CUSTOM EVAL: Real-time, one call, zero deps, CX-specific
```

---

---

## 10. Live Deployment & Links

| Resource | URL |
|----------|-----|
| **Live Demo** | https://multi-agentic-rag-zvgquhg7ta-uc.a.run.app |
| **GitHub Repo** | https://github.com/inevitableaisolutions/multi-agentic-rag |
| **GCP Project** | `multi-agent-support-gcp` (Google Cloud Console) |
| **BigQuery Analytics** | `support_analytics.interactions` table in BigQuery Console |

### GCP Services Used

| Service | What It Does In Our System |
|---------|---------------------------|
| **Vertex AI (Model Garden)** | Gemini 2.5 Flash (LLM for all 3 agents) + gemini-embedding-001 (3072d embeddings) |
| **Discovery Engine API** | Vertex AI Ranking API (semantic-ranker-default-004) for reranking |
| **Cloud Run** | Hosts the FastAPI app + custom dashboard, auto-scales 0→3 instances |
| **BigQuery** | Logs every interaction: query, intent, sentiment, eval scores, decision |
| **Cloud Build** | Builds Docker image from source during deployment |
| **Artifact Registry** | Stores the built Docker image |
| **Cloud Logging** | Automatic logs from Cloud Run |

### What We DON'T Use (and Why)

| Service | Why Not |
|---------|---------|
| **Vertex AI Vector Search** | $68.50/mo minimum. FAISS is free and sufficient at our scale. |
| **Vertex AI Agent Builder** | We use ADK (open source) for more control. |
| **Dialogflow CX** | That's what GTS uses for production chatbots (OmniBot). Our system could sit behind it. |
| **Cloud DLP** | Would use for enterprise HIPAA/FERPA. Our regex guardrails are the demo-grade equivalent. |

### Key Commands to Know

```bash
# Run locally
source .venv/bin/activate && python main.py

# Deploy to Cloud Run
gcloud run deploy multi-agentic-rag --source . --region us-central1 --project multi-agent-support-gcp

# Check deployment status
gcloud run services describe multi-agentic-rag --project multi-agent-support-gcp --region us-central1

# View logs
gcloud run logs read --service multi-agentic-rag --project multi-agent-support-gcp --region us-central1

# Query BigQuery analytics
bq query --project_id=multi-agent-support-gcp 'SELECT * FROM support_analytics.interactions ORDER BY timestamp DESC LIMIT 10'
```

---

*Read this document 2-3 times before the interview. Practice the elevator pitch out loud. For each Q&A, know the first sentence -- that's what you'll say under pressure. The rest will follow naturally once you start.*
