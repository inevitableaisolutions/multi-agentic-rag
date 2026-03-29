"""FastAPI backend — serves the custom dashboard + agent pipeline API.

Performance: Runner, SessionService, and FAISS index are created ONCE at startup.
Each query reuses these — no rebuild overhead.

Endpoints:
    GET  /           → Dashboard UI
    POST /api/query  → Run query through the full pipeline
    GET  /health     → Health check
"""

import os
import time
import traceback

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()

# Set GCP env vars before any Google imports
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.getenv("GOOGLE_CLOUD_PROJECT", ""))
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"))
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "TRUE"))

app = FastAPI(title="Customer Support Intelligence")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Startup: pre-build everything ONCE ──────────────────────────

runner = None
session_service = None
semantic_cache = None


@app.on_event("startup")
async def startup():
    """Pre-build FAISS index, Runner, and Cache at server start — not per-request."""
    global runner, session_service, semantic_cache

    print("[startup] Building FAISS index and BM25 index...")
    start = time.time()

    # Pre-build RAG indexes (this is what was taking 10+ seconds per request)
    from customer_support_agent.rag.indexer import get_index
    index, docs = get_index()
    print(f"[startup] FAISS index built: {index.ntotal} vectors, {len(docs)} docs ({time.time()-start:.1f}s)")

    # Pre-build BM25 index
    from customer_support_agent.rag.bm25 import get_bm25_index
    get_bm25_index(docs)
    print(f"[startup] BM25 index built ({time.time()-start:.1f}s)")

    # Initialize ADK Runner (reused across all requests)
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from customer_support_agent.agent import root_agent

    session_service = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name="csi", session_service=session_service)
    print(f"[startup] ADK Runner ready ({time.time()-start:.1f}s)")

    # Initialize semantic cache
    from customer_support_agent.cache.semantic_cache import SemanticCache
    semantic_cache = SemanticCache(similarity_threshold=0.70, ttl_seconds=3600)
    print(f"[startup] Semantic cache ready")

    print(f"[startup] All systems go! Total startup: {time.time()-start:.1f}s")


class QueryRequest(BaseModel):
    query: str


@app.get("/")
async def dashboard():
    return FileResponse("static/index.html")


@app.post("/api/query")
async def process_query(request: QueryRequest):
    """Run a query through: guardrails → cache → agents → response."""
    global runner, session_service, semantic_cache

    start_time = time.time()
    query = request.query

    try:
        # ─── Step 1: Guardrails ──────────────────────────────────
        from customer_support_agent.guardrails import run_guardrails
        guardrails_result = run_guardrails(query)

        if not guardrails_result["is_safe"]:
            details = guardrails_result.get("details", {})
            return {
                "blocked": True,
                "blocked_reason": guardrails_result["blocked_reason"],
                "guardrails": {
                    "is_safe": False,
                    "pii_detected": guardrails_result["pii_detected"],
                    "injection_blocked": not details.get("injection", {}).get("is_safe", True),
                    "topic_blocked": not details.get("topic", {}).get("is_on_topic", True),
                },
                "response": None,
                "classification": None,
                "retrieved_docs": None,
                "evaluation": None,
                "cache_hit": False,
                "latency_ms": int((time.time() - start_time) * 1000),
            }

        sanitized_query = guardrails_result["sanitized_query"]

        # ─── Step 2: Semantic Cache ──────────────────────────────
        cache_result = None
        if semantic_cache:
            cache_result = semantic_cache.lookup(sanitized_query)

        if cache_result:
            return {
                "blocked": False,
                "blocked_reason": None,
                "guardrails": {
                    "is_safe": True,
                    "pii_detected": guardrails_result["pii_detected"],
                    "injection_blocked": False,
                    "topic_blocked": False,
                },
                "response": cache_result["cached_response"],
                "classification": cache_result.get("metadata", {}).get("classification"),
                "retrieved_docs": cache_result.get("metadata", {}).get("retrieved_docs"),
                "evaluation": cache_result.get("metadata", {}).get("evaluation"),
                "cache_hit": True,
                "cache_similarity": round(cache_result["similarity_score"], 3),
                "latency_ms": int((time.time() - start_time) * 1000),
            }

        # ─── Step 3: Run ADK Agent Pipeline ──────────────────────
        from google.genai import types

        session = await session_service.create_session(app_name="csi", user_id="user")
        content = types.Content(
            role="user",
            parts=[types.Part(text=sanitized_query)],
        )

        # Collect outputs from agents
        final_response = ""
        classification = None
        retrieved_docs = None
        evaluation = None

        async for event in runner.run_async(
            user_id="user",
            session_id=session.id,
            new_message=content,
        ):
            if not event.content or not event.content.parts:
                continue

            author = event.author or ""

            for part in event.content.parts:
                # Capture tool calls (agent decisions)
                if part.function_call:
                    name = part.function_call.name
                    args = dict(part.function_call.args or {})

                    if name == "process_query":
                        classification = {
                            "intent": args.get("intent", ""),
                            "sentiment": args.get("sentiment", ""),
                            "urgency": args.get("urgency", ""),
                            "rewritten_queries": args.get("rewritten_queries", []),
                        }

                    if name == "evaluate_response":
                        evaluation = {
                            "faithfulness": float(args.get("faithfulness_score", 0)),
                            "answer_relevance": float(args.get("answer_relevance_score", 0)),
                            "context_relevance": float(args.get("context_relevance_score", 0)),
                            "overall_score": float(args.get("overall_score", 0)),
                            "decision": args.get("decision", ""),
                            "hallucination_detected": args.get("hallucination_detected", False),
                            "pii_in_response": args.get("pii_in_response", False),
                        }

                if part.function_response:
                    name = part.function_response.name
                    resp = dict(part.function_response.response or {})

                    if name == "search_knowledge_base":
                        articles = resp.get("articles", [])
                        retrieved_docs = [
                            {"source": a.get("source", ""), "title": a.get("title", "")}
                            for a in articles
                        ]

                # Capture text responses from agents
                if part.text and author:
                    # Prefer retrieval agent's response
                    if "retrieval_generation" in author:
                        final_response = part.text
                    elif not final_response and "agent" in author:
                        final_response = part.text

        # Fallback: get response from session state
        if not final_response:
            sess = await session_service.get_session(
                app_name="csi", user_id="user", session_id=session.id
            )
            if sess and hasattr(sess, "state"):
                final_response = sess.state.get("knowledge_response", "I couldn't generate a response. Please try again.")

        # ─── Step 4: Store in Cache (non-blocking) ─────────────────
        if semantic_cache and final_response:
            try:
                semantic_cache.store(
                    query=sanitized_query,
                    response=final_response,
                    metadata={
                        "classification": classification,
                        "retrieved_docs": retrieved_docs,
                        "evaluation": evaluation,
                    },
                )
            except Exception as cache_err:
                print(f"[cache] Store failed (non-fatal): {cache_err}")

        return {
            "blocked": False,
            "blocked_reason": None,
            "guardrails": {
                "is_safe": True,
                "pii_detected": guardrails_result["pii_detected"],
            },
            "response": final_response,
            "classification": classification,
            "retrieved_docs": retrieved_docs,
            "evaluation": evaluation,
            "cache_hit": False,
            "latency_ms": int((time.time() - start_time) * 1000),
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "blocked": False,
            "blocked_reason": None,
            "guardrails": {"is_safe": True, "pii_detected": []},
            "response": f"An error occurred: {str(e)}",
            "classification": None,
            "retrieved_docs": None,
            "evaluation": None,
            "cache_hit": False,
            "latency_ms": int((time.time() - start_time) * 1000),
            "error": str(e),
        }


@app.get("/api/cache-stats")
async def cache_stats():
    """Return cache statistics."""
    if semantic_cache:
        return semantic_cache.stats
    return {"size": 0, "hits": 0, "misses": 0, "hit_rate": 0}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "customer-support-intelligence"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
