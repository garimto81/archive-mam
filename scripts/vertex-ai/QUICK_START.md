# Vertex AI Vector Search - Quick Start Guide

**Time to complete**: 30 minutes
**Prerequisite**: GCP project, authentication, BigQuery data

---

## 1. Automated Setup (Recommended)

```bash
# Run complete infrastructure setup
bash scripts/vertex-ai/setup_vector_search.sh

# Expected output:
# - GCS bucket created
# - Vertex AI index created (5-10 minutes)
# - Index endpoint deployed (10-15 minutes)
# - Environment variables generated

# Copy environment variables to backend/.env
cat scripts/vertex-ai/vertex_ai.env >> backend/.env
```

**Time**: 20-30 minutes

---

## 2. Upload Embeddings

```bash
# Test with 10 hands first
python scripts/vertex-ai/upload_embeddings.py --limit 10

# If successful, upload all hands
python scripts/vertex-ai/upload_embeddings.py
```

**Time**: 30 seconds (10 hands) to 30 minutes (10k hands)

---

## 3. Test Search

```bash
# Run all sample queries
python scripts/vertex-ai/test_search.py

# Custom query
python scripts/vertex-ai/test_search.py --query "Phil Ivey bluff"

# Expected output:
# - Search results with hand IDs
# - Latency metrics (p95, p99)
# - Performance summary
```

**Time**: 1-2 minutes

---

## 4. Verify Backend Integration

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# In another terminal, test search API
curl "http://localhost:8000/api/search?query=Phil%20Ivey&top_k=5"

# Expected response:
# {
#   "results": [
#     {"hand_id": "...", "distance": 0.95, ...}
#   ]
# }
```

**Time**: 1 minute

---

## Manual Setup (Alternative)

If you prefer step-by-step control:

```bash
# Step 1: Create index (5-10 minutes)
python scripts/vertex-ai/create_index.py

# Step 2: Deploy endpoint (10-15 minutes)
python scripts/vertex-ai/deploy_index.py

# Step 3: Copy environment variables
# (output from deploy_index.py)

# Step 4: Upload embeddings
python scripts/vertex-ai/upload_embeddings.py --limit 10

# Step 5: Test
python scripts/vertex-ai/test_search.py
```

---

## Troubleshooting

### Error: "Could not authenticate"

```bash
gcloud auth application-default login
gcloud config set project gg-poker-dev
```

### Error: "Index not found"

Wait 5-10 minutes after index creation before deploying endpoint.

### Error: "No results found"

1. Verify embeddings uploaded: `gsutil ls gs://ati-metadata-prod/embeddings_standard/`
2. Check environment variables in `backend/.env`
3. Lower similarity threshold in test

### Error: "Quota exceeded"

Upload in smaller batches:
```bash
python scripts/vertex-ai/upload_embeddings.py --limit 100
```

---

## Environment Variables (backend/.env)

```bash
# Add these after setup
VERTEX_AI_INDEX_ENDPOINT=projects/45067711104/locations/us-central1/indexEndpoints/3557757943715725312
VERTEX_AI_DEPLOYED_INDEX_ID=poker_hands_standard_deployed
VERTEX_EMBEDDING_MODEL=text-embedding-004
VERTEX_EMBEDDING_DIMENSION=768
SEARCH_TYPE=hybrid
SEARCH_TOP_K=5
SEARCH_SIMILARITY_THRESHOLD=0.7
```

---

## Sample Queries

```bash
# Player-specific
python scripts/vertex-ai/test_search.py --query "Phil Ivey bluff on river"

# Action-specific
python scripts/vertex-ai/test_search.py --query "all-in preflop pocket aces"

# Game type
python scripts/vertex-ai/test_search.py --query "no-limit holdem tournament"

# Situation
python scripts/vertex-ai/test_search.py --query "final table bubble"
```

---

## Cost Estimate

- **Initial setup**: $60-90/month (includes first 10k hands embedding)
- **Ongoing**: $50-75/month (index + incremental embeddings)
- **Scaling**: See `README.md` for 100k/500k/1M+ hand costs

---

## Next Steps

1. **Backend**: Update `backend/app/api/search.py` to use VertexSearchService
2. **Frontend**: Connect React search UI to backend API
3. **Production**: Deploy to Cloud Run with environment variables

---

## Full Documentation

See `scripts/vertex-ai/README.md` for:
- Detailed architecture explanation
- Complete troubleshooting guide
- Performance benchmarks
- Cost optimization tips
- Open Hand History integration details

---

**Questions?** Check `README.md` or `VERTEX_AI_SETUP_COMPLETE.md`
