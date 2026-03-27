# Customer Support Intelligence — Agentic RAG System on GCP

A production-grade multi-agent customer support system built with **Google ADK** on **Google Cloud Platform**.

## Architecture

```
Customer Query
       │
       ▼
┌─────────────────────────────────────────────────────┐
│  INPUT GUARDRAILS                                    │
│  PII Redaction → Injection Detection → Topic Check   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  SEMANTIC CACHE                                      │
│  Similar query answered before? → Return cached      │
│  (40-60% cost savings)                               │
└──────────────────────┬──────────────────────────────┘
                       │ (cache miss)
                       ▼
┌─────────────────────────────────────────────────────┐
│  AGENT 1: Query Processing (Gemini, temp=0.1)        │
│  Intent → Rewrite → Expand → HyDE                   │
├─────────────────────────────────────────────────────┤
│  AGENT 2: Retrieval & Generation (Gemini, temp=0.3)  │
│  Dense (FAISS) + Sparse (BM25) → RRF → Rerank       │
├─────────────────────────────────────────────────────┤
│  AGENT 3: Evaluation (Gemini, temp=0.1)              │
│  Faithfulness → Relevance → Compliance → Decision    │
└──────────────────────┬──────────────────────────────┘
                       │
                  ┌────┴────┐
                  ▼         ▼
             BigQuery    Response
            (Full Log)  (to user)
```

## Tech Stack

| Component | Service |
|-----------|---------|
| Agent Framework | Google ADK |
| LLM | Vertex AI Gemini 2.5 Flash |
| Embeddings | gemini-embedding-001 (768d) |
| Dense Search | FAISS |
| Sparse Search | BM25 (rank_bm25) |
| Reranking | Vertex AI Ranking API |
| Analytics | BigQuery + SQLite fallback |
| Guardrails | Regex + pattern matching |
| Cache | FAISS semantic similarity |
| Deployment | Cloud Run |

## Quick Start

### 1. Clone and set up environment
```bash
git clone <repo-url>
cd "Mutlti Agent System GCP"
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure authentication

**Option A: Google AI Studio (free, no GCP project needed)**
```bash
# Get a key at https://ai.google.dev
cp .env.example .env
# Edit .env: set GOOGLE_API_KEY and GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

**Option B: GCP with Vertex AI**
```bash
gcloud auth application-default login
cp .env.example .env
# Edit .env: set GOOGLE_CLOUD_PROJECT=your-project-id
```

### 3. Run the demo
```bash
python demo.py
```

### 4. Launch the ADK web UI
```bash
adk web customer_support_agent
```
Opens a browser chat interface where you can test queries interactively.

### 5. Deploy to Cloud Run (optional)
```bash
chmod +x infra/setup.sh
./infra/setup.sh YOUR_PROJECT_ID
gcloud run deploy customer-support-agent --source . --region us-central1
```

## Project Structure

```
customer_support_agent/
├── agent.py                    # Root SequentialAgent + 3 sub-agents
├── __init__.py                 # ADK entry point
├── config/settings.py          # Pydantic Settings
├── config/prompts.py           # Agent system prompts
├── guardrails/                 # PII, injection, topic boundary
├── cache/semantic_cache.py     # FAISS similarity cache
├── tools/                      # Agent tools (process, retrieve, evaluate, log)
├── rag/                        # Chunker, embeddings, FAISS, BM25, reranker, retriever
├── knowledge_base/             # 25 markdown docs (billing, technical, account, general)
├── analytics/                  # BigQuery client + SQLite fallback
└── eval/                       # Test dataset + batch evaluation
```

## Key Features

- **Input Guardrails**: PII redaction (SSN, email, phone, credit card), prompt injection detection, topic boundary enforcement
- **Semantic Cache**: FAISS-based similarity matching (threshold 0.95), 40-60% cost reduction
- **Advanced RAG**: Query rewriting, expansion, HyDE, hybrid dense+sparse retrieval, Vertex AI reranking
- **LLM-as-Judge Evaluation**: Faithfulness, answer relevance, context relevance, hallucination, bias, toxicity, PII checks
- **Full Analytics**: Every interaction logged to BigQuery with all metrics
- **Production Patterns**: Pydantic config, environment variables, graceful fallbacks, async logging

## Cost

~$0.25-$1.00 total for demo usage. BigQuery, Cloud Run, and Cloud Storage all within GCP free tiers.
