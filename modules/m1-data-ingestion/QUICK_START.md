# M1 Data Ingestion - Quick Start Guide

**POKER-BRAIN WSOP Archive System - M1 Module**

> 5분 안에 M1 Data Ingestion Service를 로컬에서 실행하세요!

---

## 🚀 Quick Start (3 Steps)

### 1. Setup Environment

```bash
cd modules/m1-data-ingestion

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env (필수: GCP credentials)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
# PROJECT_ID=gg-poker
```

### 3. Run

```bash
# Start Flask server
python -m app.api

# Server runs at: http://localhost:8001
```

✅ **Done!** API is now running.

---

## 🧪 Test It

```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py -v
```

---

## 📡 API Examples

### 1. Health Check

```bash
curl http://localhost:8001/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "bigquery": "ok",
    "gcs": "ok",
    "pubsub": "ok"
  }
}
```

### 2. Start Ingestion

```bash
curl -X POST http://localhost:8001/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "gcs_path": "gs://gg-poker-ati/sample.jsonl",
    "event_id": "wsop2024_me",
    "tournament_day": 1
  }'
```

**Response**:
```json
{
  "job_id": "ingest-20241117-001",
  "status": "queued",
  "created_at": "2024-11-17T10:30:00Z"
}
```

### 3. Check Job Status

```bash
curl http://localhost:8001/v1/ingest/ingest-20241117-001/status
```

**Response**:
```json
{
  "job_id": "ingest-20241117-001",
  "status": "completed",
  "rows_processed": 1500,
  "rows_failed": 0
}
```

### 4. Get Statistics

```bash
# Last 24 hours
curl http://localhost:8001/v1/stats?period=24h

# Specific event
curl http://localhost:8001/v1/stats?event_id=wsop2024_me
```

---

## 🐳 Docker Quick Start

```bash
# Build image
docker build -t m1-data-ingestion:1.0.0 .

# Run container
docker run -p 8001:8001 \
  -e PROJECT_ID=gg-poker \
  -e DATASET=prod \
  -e TABLE=hand_summary \
  m1-data-ingestion:1.0.0

# Test
curl http://localhost:8001/health
```

---

## ☁️ Deploy to Cloud Run

```bash
# Set project
export PROJECT_ID=gg-poker

# Deploy
bash deploy.sh

# Get service URL
gcloud run services describe m1-data-ingestion \
  --region us-central1 \
  --format 'value(status.url)'
```

---

## 📁 File Overview

**Core Files**:
- `app/api.py` - Flask API server (4 endpoints)
- `app/dataflow_pipeline.py` - Dataflow pipeline
- `app/bigquery_client.py` - BigQuery operations
- `app/config.py` - Configuration management

**Tests**:
- `tests/test_api.py` - API endpoint tests
- `tests/test_pipeline.py` - Pipeline component tests
- `tests/test_bigquery_client.py` - BigQuery client tests

**Config**:
- `requirements.txt` - Python dependencies
- `Dockerfile` - Cloud Run deployment
- `.env.example` - Environment template
- `pytest.ini` - Test configuration

---

## 🔧 Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python -m app.api

# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=app --cov-report=html

# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Build Docker image
docker build -t m1-data-ingestion .

# Deploy to Cloud Run
bash deploy.sh
```

---

## 📊 API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/ingest` | Start ingestion job |
| GET | `/v1/ingest/{job_id}/status` | Get job status |
| GET | `/v1/stats` | Get statistics |
| GET | `/health` | Health check |

---

## 🆘 Troubleshooting

### Issue: ImportError

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Issue: BigQuery connection failed

```bash
# Check credentials
echo $GOOGLE_APPLICATION_CREDENTIALS

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Issue: Tests failing

```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest tests/ -vv
```

---

## 📚 Next Steps

1. ✅ Read full [README.md](README.md) for detailed documentation
2. ✅ Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for Week 3 status
3. ✅ Review [CHANGELOG.md](CHANGELOG.md) for version history
4. ✅ See `.claude/plugins/agent-m1-data-ingestion/prompt.md` for full specification

---

## 🎯 Week 3 Status

**Completion**: 30% (on target)

**Implemented**:
- ✅ Dataflow pipeline
- ✅ Flask API (4 endpoints)
- ✅ BigQuery client
- ✅ Unit tests (80% coverage)
- ✅ Dockerfile

**Week 4 Planned**:
- ⏳ Dead Letter Queue
- ⏳ Firestore job state
- ⏳ Integration tests
- ⏳ Cloud Monitoring

---

**Need Help?**
- 📧 Contact: aiden.kim@ggproduction.net
- 📖 Docs: [README.md](README.md)
- 🐛 Issues: Create GitHub issue

---

**M1 Data Ingestion Service v1.0.0**
*POKER-BRAIN WSOP Archive System*
