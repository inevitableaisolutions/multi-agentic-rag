#!/bin/bash
# GCP Infrastructure Setup Script
# Run this once to set up all required GCP resources.
#
# Usage:
#   chmod +x infra/setup.sh
#   ./infra/setup.sh YOUR_PROJECT_ID

set -euo pipefail

PROJECT_ID="${1:?Usage: ./infra/setup.sh PROJECT_ID}"
REGION="us-central1"
BQ_DATASET="support_analytics"

echo "=== Setting up GCP infrastructure for project: $PROJECT_ID ==="

# Set project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "--- Enabling APIs ---"
gcloud services enable \
    aiplatform.googleapis.com \
    bigquery.googleapis.com \
    run.googleapis.com \
    discoveryengine.googleapis.com \
    storage.googleapis.com \
    cloudbuild.googleapis.com

# Create BigQuery dataset
echo "--- Creating BigQuery dataset ---"
bq --location=US mk -d --exists_ok "$PROJECT_ID:$BQ_DATASET"

# Create BigQuery table
echo "--- Creating BigQuery table ---"
bq query --use_legacy_sql=false "
CREATE TABLE IF NOT EXISTS \`$PROJECT_ID.$BQ_DATASET.interactions\` (
    timestamp           TIMESTAMP   NOT NULL,
    session_id          STRING,
    original_query      STRING,
    rewritten_queries   STRING,
    intent              STRING,
    sentiment           STRING,
    urgency             STRING,
    retrieved_doc_ids   STRING,
    num_docs_retrieved  INT64,
    faithfulness_score      FLOAT64,
    answer_relevance_score  FLOAT64,
    context_relevance_score FLOAT64,
    overall_score           FLOAT64,
    hallucination_detected  BOOL,
    compliance_passed       BOOL,
    decision                STRING,
    cache_hit               BOOL
)
PARTITION BY DATE(timestamp)
CLUSTER BY intent, decision;
"

# Set up application default credentials
echo "--- Setting up authentication ---"
gcloud auth application-default login

echo ""
echo "=== Setup complete! ==="
echo "Project: $PROJECT_ID"
echo "BigQuery dataset: $BQ_DATASET"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and set GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
echo "  2. Run: adk web customer_support_agent"
echo "  3. Deploy: gcloud run deploy customer-support-agent --source . --region $REGION"
