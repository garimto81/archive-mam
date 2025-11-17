# M5 Clipping Service - Quick Start Guide

Get the M5 Clipping Service running in 5 minutes.

## Prerequisites

- Python 3.11+
- Git

## Installation (3 minutes)

```bash
# 1. Navigate to module directory
cd modules/m5-clipping

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env
# Edit .env if needed (defaults work for development)
```

## Running the Service (2 minutes)

### Option 1: Development Mode (Mock - No Emulator Needed)

**Terminal 1 - API Server**:
```bash
# Set development mode
export POKER_ENV=development  # On Windows: set POKER_ENV=development

# Run API
python app/api.py

# API running at: http://localhost:8005
```

**Terminal 2 - Local Agent**:
```bash
# Set development mode
export POKER_ENV=development  # On Windows: set POKER_ENV=development

# Run agent
python -m local_agent.subscriber

# Agent running and listening for requests
```

### Option 2: With Pub/Sub Emulator (More Realistic)

**Terminal 1 - Pub/Sub Emulator**:
```bash
# Install gcloud SDK if not already installed
# https://cloud.google.com/sdk/docs/install

# Start emulator
gcloud beta emulators pubsub start --port=8085

# Emulator running at: localhost:8085
```

**Terminal 2 - API Server**:
```bash
export POKER_ENV=development
export PUBSUB_EMULATOR_HOST=localhost:8085

python app/api.py
```

**Terminal 3 - Local Agent**:
```bash
export POKER_ENV=development
export PUBSUB_EMULATOR_HOST=localhost:8085

python -m local_agent.subscriber
```

## Test the Service (1 minute)

### 1. Health Check

```bash
curl http://localhost:8005/health
```

Expected response:
```json
{
  "status": "healthy",
  "api_status": "ok",
  "agents": {
    "primary": "active",
    "standby": "down"
  },
  "queue_depth": 0
}
```

### 2. Submit Clipping Request

```bash
curl -X POST http://localhost:8005/v1/clip/request \
  -H "Content-Type: application/json" \
  -d '{
    "hand_id": "test_hand_001",
    "nas_video_path": "/nas/poker/test.mp4",
    "start_seconds": 10,
    "end_seconds": 60,
    "output_quality": "high"
  }'
```

Expected response:
```json
{
  "request_id": "clip-20241117-001",
  "hand_id": "test_hand_001",
  "status": "queued",
  "estimated_duration_sec": 45,
  "queue_position": 1,
  "created_at": "2024-11-17T14:00:00Z"
}
```

### 3. Check Status

```bash
curl http://localhost:8005/v1/clip/clip-20241117-001/status
```

After a few seconds, status should be `completed`:
```json
{
  "request_id": "clip-20241117-001",
  "hand_id": "test_hand_001",
  "status": "completed",
  "output_gcs_path": "gs://gg-subclips/test_hand_001.mp4",
  "file_size_bytes": 112,
  "created_at": "2024-11-17T14:00:00Z",
  "completed_at": "2024-11-17T14:00:05Z"
}
```

### 4. Get Download URL

```bash
curl http://localhost:8005/v1/clip/clip-20241117-001/download
```

Response:
```json
{
  "request_id": "clip-20241117-001",
  "hand_id": "test_hand_001",
  "download_url": "http://localhost:8005/mock-download/test_hand_001.mp4?expires=168h",
  "expires_at": "2024-11-24T14:00:00Z",
  "file_size_bytes": 112
}
```

## Run Tests

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-flask pytest-cov pytest-mock

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov=local_agent --cov-report=term-missing

# Expected: 80+ tests, 85%+ coverage
```

## What's Happening in Development Mode?

1. **API Server** receives your clipping request
2. **Pub/Sub Publisher** publishes message (to emulator or mock)
3. **Local Agent** receives message via subscriber
4. **FFmpeg Clipper** creates a **mock MP4 file** (no actual clipping)
5. **GCS Client** saves to `/tmp/mock-clips/` (no cloud upload)
6. **Completion message** published
7. **Download URL** generated (mock local URL)

## Common Issues

### Issue: Port 8005 already in use
```bash
# Solution: Kill existing process or use different port
# Find process
lsof -i :8005  # macOS/Linux
netstat -ano | findstr :8005  # Windows

# Kill process (macOS/Linux)
kill -9 <PID>

# Or change port in app/api.py (line: app.run(..., port=8006))
```

### Issue: Module not found
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall if needed
pip install -r requirements.txt
```

### Issue: Pub/Sub emulator not starting
```bash
# Solution: Install gcloud SDK and emulator
gcloud components install pubsub-emulator

# Or skip emulator - development mode works without it
```

## Next Steps

1. Read full documentation: [`README.md`](README.md)
2. Review API specification: [`../clipping/openapi.yaml`](../clipping/openapi.yaml)
3. Check test examples: [`tests/test_api.py`](tests/test_api.py)
4. Deploy to production: See README.md "Production Setup"

## Production Checklist

When ready for production:

- [ ] Set `POKER_ENV=production`
- [ ] Configure real GCP project ID
- [ ] Create Pub/Sub topics and subscriptions
- [ ] Set up GCS bucket with lifecycle policy
- [ ] Install FFmpeg on agent server
- [ ] Configure systemd service
- [ ] Set up authentication (JWT/OAuth)
- [ ] Enable rate limiting
- [ ] Configure monitoring and alerts

## Support

- Documentation: [`README.md`](README.md)
- Issues: Contact Eve (M5 Clipping Service Agent)
- Email: aiden.kim@ggproduction.net

---

**Happy Clipping!** 🎬✂️
