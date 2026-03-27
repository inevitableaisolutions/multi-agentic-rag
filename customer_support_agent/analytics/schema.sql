-- BigQuery DDL for the interactions analytics table.
-- Partitioned by date for efficient time-range queries.
-- Clustered by intent and decision for fast aggregation.

CREATE TABLE IF NOT EXISTS `{project}.{dataset}.{table}` (
    -- Identifiers
    timestamp           TIMESTAMP   NOT NULL,
    session_id          STRING,

    -- Triage (Agent 1)
    original_query      STRING,
    rewritten_queries   STRING,     -- JSON array
    intent              STRING,     -- billing, technical, account, general
    sentiment           STRING,     -- positive, neutral, negative, frustrated
    urgency             STRING,     -- low, medium, high, critical

    -- Retrieval (Agent 2)
    retrieved_doc_ids   STRING,     -- JSON array
    num_docs_retrieved  INT64,

    -- Evaluation (Agent 3)
    faithfulness_score      FLOAT64,
    answer_relevance_score  FLOAT64,
    context_relevance_score FLOAT64,
    overall_score           FLOAT64,
    hallucination_detected  BOOL,
    compliance_passed       BOOL,
    decision                STRING,     -- approve, revise, escalate

    -- Cache
    cache_hit               BOOL
)
PARTITION BY DATE(timestamp)
CLUSTER BY intent, decision;
