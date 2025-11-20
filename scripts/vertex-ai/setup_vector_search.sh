#!/bin/bash
###############################################################################
# Vertex AI Vector Search Setup Script
# Open Hand History Specification - v1.0.0
#
# Purpose: Automated setup of complete Vertex AI Vector Search infrastructure
# Architecture: TextEmbedding-004 (768D) + Tree-AH + Hybrid Search (BM25+Vector+RRF)
#
# Workflow:
#   1. Validate prerequisites (GCP project, auth, APIs)
#   2. Create GCS bucket for embeddings
#   3. Create Vertex AI Vector Search index
#   4. Create and deploy index endpoint
#   5. Generate environment variables for backend
#
# Usage:
#   bash scripts/vertex-ai/setup_vector_search.sh [--project PROJECT_ID] [--region REGION]
#
# Example:
#   bash scripts/vertex-ai/setup_vector_search.sh --project gg-poker-dev --region us-central1
###############################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
PROJECT_ID="${GCP_PROJECT:-gg-poker-dev}"
REGION="${GCP_REGION:-us-central1}"
INDEX_NAME="poker_hands_standard"
ENDPOINT_NAME="poker_hands_standard_endpoint"
DEPLOYED_INDEX_ID="poker_hands_standard_deployed"
GCS_BUCKET_NAME="ati-metadata-prod"
EMBEDDINGS_PREFIX="embeddings_standard"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--project PROJECT_ID] [--region REGION]"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

###############################################################################
# Helper Functions
###############################################################################

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
  if ! command -v "$1" &> /dev/null; then
    log_error "$1 is not installed. Please install it first."
    exit 1
  fi
}

###############################################################################
# Step 0: Prerequisites Check
###############################################################################

log_info "===== Prerequisites Check ====="
log_info "Project: $PROJECT_ID"
log_info "Region: $REGION"
echo ""

# Check required commands
log_info "Checking required commands..."
check_command gcloud
check_command python3
log_success "All required commands are available"
echo ""

# Check GCP authentication
log_info "Checking GCP authentication..."
if ! gcloud auth application-default print-access-token &> /dev/null; then
  log_error "GCP authentication not configured"
  echo "Please run: gcloud auth application-default login"
  exit 1
fi
log_success "GCP authentication configured"
echo ""

# Set project
log_info "Setting GCP project..."
gcloud config set project "$PROJECT_ID" --quiet
log_success "Project set to $PROJECT_ID"
echo ""

# Enable required APIs
log_info "Enabling required GCP APIs (this may take 1-2 minutes)..."
gcloud services enable aiplatform.googleapis.com --quiet 2>/dev/null || true
gcloud services enable storage.googleapis.com --quiet 2>/dev/null || true
gcloud services enable bigquery.googleapis.com --quiet 2>/dev/null || true
log_success "Required APIs enabled"
echo ""

###############################################################################
# Step 1: Create GCS Bucket for Embeddings
###############################################################################

log_info "===== Step 1: GCS Bucket Setup ====="
GCS_EMBEDDINGS_URI="gs://${GCS_BUCKET_NAME}/${EMBEDDINGS_PREFIX}/"

# Check if bucket exists
if gsutil ls -b "gs://${GCS_BUCKET_NAME}" &> /dev/null; then
  log_success "Bucket gs://${GCS_BUCKET_NAME} already exists"
else
  log_info "Creating GCS bucket: gs://${GCS_BUCKET_NAME}"
  gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://${GCS_BUCKET_NAME}"
  log_success "Bucket created"
fi

# Create embeddings directory
log_info "Creating embeddings directory: ${GCS_EMBEDDINGS_URI}"
gsutil ls "${GCS_EMBEDDINGS_URI}" &> /dev/null || echo "" | gsutil cp - "${GCS_EMBEDDINGS_URI}.placeholder"
log_success "Embeddings directory ready"
echo ""

###############################################################################
# Step 2: Create Vertex AI Vector Search Index
###############################################################################

log_info "===== Step 2: Create Vector Search Index ====="

# Check if index already exists
INDEX_ID_FILE="${SCRIPT_DIR}/index_id.txt"
if [[ -f "$INDEX_ID_FILE" ]]; then
  EXISTING_INDEX_ID=$(cat "$INDEX_ID_FILE")
  log_warn "Index ID file already exists: $EXISTING_INDEX_ID"
  echo -n "Delete and recreate index? (y/N): "
  read -r response
  if [[ "$response" =~ ^[Yy]$ ]]; then
    log_info "Deleting existing index..."
    gcloud ai indexes delete "$EXISTING_INDEX_ID" --region="$REGION" --quiet || true
    rm "$INDEX_ID_FILE"
  else
    log_info "Using existing index: $EXISTING_INDEX_ID"
    INDEX_ID="$EXISTING_INDEX_ID"
  fi
fi

# Create index if needed
if [[ ! -f "$INDEX_ID_FILE" ]]; then
  log_info "Creating Vertex AI index (this takes 5-10 minutes)..."
  log_info "Configuration:"
  log_info "  - Name: $INDEX_NAME"
  log_info "  - Dimensions: 768 (TextEmbedding-004)"
  log_info "  - Distance: DOT_PRODUCT_DISTANCE"
  log_info "  - Algorithm: Tree-AH (optimal for 768D)"
  log_info "  - Shard size: SMALL (for <100k vectors)"
  log_info "  - Update method: BATCH_UPDATE"
  echo ""

  python3 "${SCRIPT_DIR}/create_index.py" || {
    log_error "Failed to create index"
    exit 1
  }

  log_success "Index created successfully"
  INDEX_ID=$(cat "$INDEX_ID_FILE")
  log_info "Index ID: $INDEX_ID"
else
  INDEX_ID=$(cat "$INDEX_ID_FILE")
  log_info "Using existing index: $INDEX_ID"
fi
echo ""

###############################################################################
# Step 3: Create and Deploy Index Endpoint
###############################################################################

log_info "===== Step 3: Deploy Index Endpoint ====="

ENDPOINT_ID_FILE="${SCRIPT_DIR}/endpoint_id.txt"

# Check if endpoint already exists
if [[ -f "$ENDPOINT_ID_FILE" ]]; then
  EXISTING_ENDPOINT_ID=$(cat "$ENDPOINT_ID_FILE")
  log_warn "Endpoint ID file already exists: $EXISTING_ENDPOINT_ID"
  echo -n "Use existing endpoint? (Y/n): "
  read -r response
  if [[ "$response" =~ ^[Nn]$ ]]; then
    log_info "Deleting existing endpoint..."
    gcloud ai index-endpoints delete "$EXISTING_ENDPOINT_ID" --region="$REGION" --quiet || true
    rm "$ENDPOINT_ID_FILE"
  else
    log_info "Using existing endpoint: $EXISTING_ENDPOINT_ID"
    ENDPOINT_ID="$EXISTING_ENDPOINT_ID"
  fi
fi

# Create and deploy endpoint if needed
if [[ ! -f "$ENDPOINT_ID_FILE" ]]; then
  log_info "Creating and deploying index endpoint (this takes 10-15 minutes)..."
  python3 "${SCRIPT_DIR}/deploy_index.py" || {
    log_error "Failed to deploy endpoint"
    exit 1
  }

  log_success "Endpoint deployed successfully"
  ENDPOINT_ID=$(cat "$ENDPOINT_ID_FILE")
  log_info "Endpoint ID: $ENDPOINT_ID"
else
  ENDPOINT_ID=$(cat "$ENDPOINT_ID_FILE")
  log_info "Using existing endpoint: $ENDPOINT_ID"
fi
echo ""

###############################################################################
# Step 4: Generate Environment Variables
###############################################################################

log_info "===== Step 4: Environment Variables ====="

# Get numeric IDs for environment variables
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
INDEX_NUMERIC_ID=$(echo "$INDEX_ID" | grep -oP '\d+$')
ENDPOINT_NUMERIC_ID=$(echo "$ENDPOINT_ID" | grep -oP '\d+$')

ENDPOINT_RESOURCE_NAME="projects/${PROJECT_NUMBER}/locations/${REGION}/indexEndpoints/${ENDPOINT_NUMERIC_ID}"

# Create environment variables file
ENV_FILE="${SCRIPT_DIR}/vertex_ai.env"
cat > "$ENV_FILE" <<EOF
# Vertex AI Vector Search Configuration
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# Project: $PROJECT_ID
# Region: $REGION

# GCS Storage
GCS_BUCKET_ATI_METADATA=$GCS_BUCKET_NAME
GCS_EMBEDDINGS_PREFIX=$EMBEDDINGS_PREFIX
GCS_EMBEDDINGS_URI=$GCS_EMBEDDINGS_URI

# Vertex AI Index
VERTEX_INDEX_ID=$INDEX_NAME
VERTEX_INDEX_ENDPOINT_ID=${ENDPOINT_NAME}

# Vertex AI Endpoint (use this in backend)
VERTEX_AI_INDEX_ENDPOINT=$ENDPOINT_RESOURCE_NAME
VERTEX_AI_DEPLOYED_INDEX_ID=$DEPLOYED_INDEX_ID

# Embedding Configuration
VERTEX_EMBEDDING_MODEL=text-embedding-004
VERTEX_EMBEDDING_DIMENSION=768

# Search Configuration
SEARCH_TYPE=hybrid  # hybrid (BM25+Vector+RRF) | vector
SEARCH_TOP_K=5
SEARCH_SIMILARITY_THRESHOLD=0.7
EOF

log_success "Environment variables saved to: $ENV_FILE"
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}IMPORTANT: Add these to your .env.poc file:${NC}"
echo -e "${YELLOW}========================================${NC}"
cat "$ENV_FILE"
echo -e "${YELLOW}========================================${NC}"
echo ""

###############################################################################
# Step 5: Completion Summary
###############################################################################

log_info "===== Setup Complete ====="
log_success "Vertex AI Vector Search infrastructure is ready!"
echo ""
log_info "Next steps:"
echo "  1. Copy environment variables from $ENV_FILE to backend/.env"
echo "  2. Upload embeddings: python scripts/vertex-ai/upload_embeddings.py --limit 10"
echo "  3. Test search: python scripts/vertex-ai/test_search.py"
echo "  4. Update backend: backend/app/services/vertex_search.py"
echo ""
log_info "Infrastructure Summary:"
echo "  - GCS Bucket: gs://${GCS_BUCKET_NAME}/${EMBEDDINGS_PREFIX}/"
echo "  - Index: $INDEX_ID"
echo "  - Endpoint: $ENDPOINT_ID"
echo "  - Deployed Index ID: $DEPLOYED_INDEX_ID"
echo ""
log_info "Cost Estimate (monthly):"
echo "  - Vector Search Index: ~$50-70"
echo "  - Embedding API (initial): ~$10-20 (one-time)"
echo "  - GCS Storage: <$1"
echo ""
log_success "Setup completed successfully!"
