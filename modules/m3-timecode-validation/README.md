# M3 Timecode Validation Service

**Version**: 1.0.0 (100% Complete)
**Agent**: Charlie
**Project**: POKER-BRAIN WSOP Archive System
**Status**: Production Ready

---

## Overview

M3 Timecode Validation Service는 ATI 타임스탬프와 NAS 영상 타임코드의 동기화를 검증하는 서비스입니다. Google Cloud Vision API를 활용하여 포커 장면을 감지하고, 자동으로 sync_score를 계산하여 타임코드 매칭의 정확도를 평가합니다.

### Core Features

1. **Vision API Integration**: 포커 장면 감지 (카드, 칩, 플레이어)
2. **sync_score Algorithm**: 3가지 요소 기반 점수 계산 (0-100)
3. **Offset Calculation**: 동기화 불일치 시 자동 보정값 계산
4. **FFmpeg Frame Extraction**: 영상에서 특정 시점 프레임 추출
5. **BigQuery Integration**: M1/M2 데이터 읽기, 검증 결과 저장
6. **Flask API Server**: 8개 REST API 엔드포인트
7. **Mock Support**: 개발 환경에서 Mock 데이터 사용

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   M3 Timecode Validation                    │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   BigQuery          Vision API           FFmpeg
  (M1 + M2)      (Poker Detection)   (Frame Extract)
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                   sync_score Calculator
                   (vision*50 + duration*30 + player*20)
                            │
                            ▼
                  Offset Calculator
                  (Auto-correction)
                            │
                            ▼
                   BigQuery Write
              (prod.timecode_validation)
```

---

## sync_score Algorithm

### Formula

```python
sync_score = (
    vision_confidence * 50 +    # Vision API 감지 신뢰도 (50% 가중치)
    duration_match * 30 +       # 핸드/영상 길이 일치도 (30% 가중치)
    player_count_match * 20     # 플레이어 수 일치도 (20% 가중치)
)
```

### Score Interpretation

| Score Range | Status | Action |
|------------|--------|--------|
| 90-100 | Perfect Sync | 완벽 동기화 - 프로덕션 사용 가능 |
| 80-90 | Good Sync | 양호 - 사용 가능 |
| 60-80 | Needs Offset | Offset 계산 필요 - 자동 보정 권장 |
| < 60 | Manual Match | 수동 매칭 필요 - 사용자 확인 필요 |

### Example Calculation

```python
# Case 1: Perfect Match
vision_confidence = 0.95    # Vision API가 포커 장면으로 95% 확신
duration_match = 1.0        # 핸드 150s, 영상 150s (100% 일치)
player_count = 1.0          # 핸드 6명, 영상 6명 (100% 일치)

sync_score = 0.95*50 + 1.0*30 + 1.0*20 = 97.5 ✅

# Case 2: Needs Offset
vision_confidence = 0.75    # 포커 장면 75% 확신
duration_match = 0.65       # 핸드 150s, 영상 180s (20% 차이)
player_count = 0.5          # 핸드 6명, 영상 8명 (2명 차이)

sync_score = 0.75*50 + 0.65*30 + 0.5*20 = 67.0 ⚠️ (Offset 필요)
```

---

## API Endpoints

### 1. POST /v1/validate

단일 핸드 타임코드 검증

**Request**:
```json
{
  "hand_id": "wsop2024_me_d3_h154",
  "timestamp_start_utc": "2024-07-15T15:24:15Z",
  "timestamp_end_utc": "2024-07-15T15:26:45Z",
  "nas_video_path": "/nas/poker/2024/wsop/main_event_day3.mp4",
  "use_vision_api": true
}
```

**Response** (200):
```json
{
  "validation_id": "val-20241117-001",
  "hand_id": "wsop2024_me_d3_h154",
  "status": "processing",
  "estimated_duration_sec": 10,
  "created_at": "2024-11-17T10:30:00Z"
}
```

### 2. GET /v1/validate/{validation_id}/result

검증 결과 조회

**Response** (200):
```json
{
  "validation_id": "val-20241117-001",
  "hand_id": "wsop2024_me_d3_h154",
  "status": "completed",
  "sync_score": 94.5,
  "is_synced": true,
  "validation_method": "vision_api",
  "vision_confidence": 0.95,
  "detected_objects": ["poker_table", "playing_cards", "poker_chips", "person"],
  "calculated_offset_seconds": 0,
  "frame_sample_gcs": "gs://validation-frames/val-001.jpg",
  "completed_at": "2024-11-17T10:30:08Z"
}
```

### 3. POST /v1/validate/batch

배치 검증 (최대 1000개 핸드)

**Request**:
```json
{
  "hand_ids": ["hand1", "hand2", "hand3"],
  "use_vision_api": true,
  "auto_apply_offset": false
}
```

### 4. POST /v1/manual/match

수동 매칭 (사용자가 직접 타임코드 입력)

**Request**:
```json
{
  "hand_id": "wsop2024_me_d3_h154",
  "matched_video_timecode": "03:24:15",
  "matched_by_user": "charlie@ggproduction.net",
  "confidence": "high"
}
```

### 5. GET /v1/sync-scores

sync_score 목록 조회 (필터링 가능)

**Query Params**:
- `event_id`: 이벤트로 필터링
- `min_score`: 최소 점수 필터

### 6. GET /v1/offsets

계산된 Offset 목록 조회

**Query Params**:
- `needs_offset`: `true`이면 Offset 필요한 것만 조회

### 7. GET /v1/stats

검증 통계 조회

**Response**:
```json
{
  "total_hands": 125000,
  "validated_hands": 98500,
  "validation_rate": 0.788,
  "avg_sync_score": 89.3,
  "perfect_sync_count": 75000,
  "offset_needed_count": 18500,
  "manual_needed_count": 5000,
  "score_distribution": {
    "90-100": 75000,
    "80-90": 18500,
    "60-80": 4500,
    "<60": 500
  }
}
```

### 8. GET /health

헬스 체크

**Response**:
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "1.0.0",
  "dependencies": {
    "vision_api": "ok",
    "bigquery": "ok",
    "ffmpeg": "ok"
  }
}
```

---

## Installation & Setup

### Prerequisites

- Python 3.11+
- FFmpeg (for frame extraction)
- Google Cloud credentials
- BigQuery access to M1 (hand_summary) and M2 (video_files) tables

### Local Development Setup

```bash
# 1. Clone repository
cd modules/m3-timecode-validation

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export POKER_ENV=development
export VISION_API_ENABLED=false  # Use mock for development
export BIGQUERY_MOCK_DATA=../../mock_data/bigquery/hand_summary_mock.json
export VIDEO_MOCK_DATA=../../mock_data/bigquery/video_files_mock.json

# 5. Run server
python -m app.api
# Server starts on http://localhost:8003
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_sync_scorer.py -v

# Target: 80% coverage
```

**Expected Output**:
```
tests/test_sync_scorer.py ................ PASSED [100%]
tests/test_offset_calculator.py ......... PASSED [100%]
tests/test_api.py .................... PASSED [100%]
tests/test_vision_detector.py .... PASSED [100%]

Coverage: 85%
```

---

## Docker Deployment

### Build Image

```bash
# Build for Cloud Run
docker build -t gcr.io/gg-poker/m3-timecode-validation:1.0.0 .

# Test locally
docker run -p 8003:8003 \
  -e POKER_ENV=development \
  -e VISION_API_ENABLED=false \
  gcr.io/gg-poker/m3-timecode-validation:1.0.0
```

### Cloud Run Deployment

```bash
# Push to Google Container Registry
docker push gcr.io/gg-poker/m3-timecode-validation:1.0.0

# Deploy to Cloud Run (Development)
gcloud run deploy m3-timecode-validation-dev \
  --image gcr.io/gg-poker/m3-timecode-validation:1.0.0 \
  --region us-central1 \
  --platform managed \
  --set-env-vars="POKER_ENV=development,VISION_API_ENABLED=false" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 120s \
  --max-instances 10 \
  --allow-unauthenticated

# Deploy to Cloud Run (Production)
gcloud run deploy m3-timecode-validation \
  --image gcr.io/gg-poker/m3-timecode-validation:1.0.0 \
  --region us-central1 \
  --platform managed \
  --set-env-vars="POKER_ENV=production,VISION_API_ENABLED=true" \
  --memory 4Gi \
  --cpu 4 \
  --timeout 120s \
  --max-instances 50 \
  --service-account timecode-validation-sa@gg-poker.iam.gserviceaccount.com
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POKER_ENV` | `development` | `development` or `production` |
| `VISION_API_ENABLED` | `true` | Enable Vision API (false for mock) |
| `VISION_CONFIDENCE_THRESHOLD` | `0.5` | Minimum confidence for poker detection |
| `FFMPEG_PATH` | `/usr/bin/ffmpeg` | Path to FFmpeg binary |
| `PORT` | `8003` | Flask server port |
| `LOG_LEVEL` | `INFO` | Logging level |

### BigQuery Tables

**Input** (from M1 and M2):
- `gg-poker.prod.hand_summary` - Hand metadata
- `gg-poker.prod.video_files` - Video metadata

**Output**:
- `gg-poker.prod.timecode_validation` - Validation results

**Schema** (timecode_validation):
```sql
CREATE TABLE `gg-poker.prod.timecode_validation` (
  validation_id STRING NOT NULL,
  hand_id STRING,
  video_id STRING,
  sync_score NUMERIC,              -- 0-100
  offset_seconds INT64,            -- 오프셋 (초)
  vision_confidence NUMERIC,       -- Vision API 신뢰도
  duration_match NUMERIC,          -- 길이 일치도
  player_count NUMERIC,            -- 플레이어 수 일치도
  status STRING,                   -- pending/validated/failed
  validation_method STRING,        -- vision_api/manual/duration_only
  detected_objects ARRAY<STRING>,  -- 감지된 객체
  offset_reason STRING,            -- Offset 사유
  frame_sample_gcs STRING,         -- 추출 프레임 GCS 경로
  validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

---

## Development Workflow

### Week 3-4: Mock Development ⭐

```bash
# Use mock BigQuery data
export POKER_ENV=development
export BIGQUERY_MOCK_DATA=../../mock_data/bigquery/hand_summary_mock.json

# Run with mock Vision API
export VISION_API_ENABLED=false

# Start development server
python -m app.api
```

### Week 5: Production Switch ⭐

```bash
# Switch to production BigQuery
export POKER_ENV=production

# Enable real Vision API
export VISION_API_ENABLED=true

# Test with real data
curl -X POST http://localhost:8003/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "hand_id": "wsop2024_me_d1_h001",
    "timestamp_start_utc": "2024-07-15T15:24:15Z",
    "timestamp_end_utc": "2024-07-15T15:26:45Z",
    "nas_video_path": "/nas/poker/2024/wsop/me_d1.mp4",
    "use_vision_api": true
  }'
```

---

## Project Structure

```
m3-timecode-validation/
├── app/
│   ├── __init__.py              # Package initializer
│   ├── config.py                # Configuration (env vars, constants)
│   ├── api.py                   # Flask API server (8 endpoints)
│   ├── bigquery_client.py       # BigQuery client (Mock/Real switch)
│   ├── vision_detector.py       # Vision API integration
│   ├── frame_extractor.py       # FFmpeg frame extraction
│   ├── sync_scorer.py           # sync_score algorithm
│   └── offset_calculator.py     # Offset calculation
├── tests/
│   ├── __init__.py
│   ├── test_sync_scorer.py      # sync_score tests
│   ├── test_offset_calculator.py # Offset calculation tests
│   ├── test_api.py              # API endpoint tests
│   └── test_vision_detector.py  # Vision API tests (mocked)
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Cloud Run deployment
├── .dockerignore               # Docker ignore file
└── README.md                    # This file
```

---

## Performance Benchmarks

| Operation | Expected Duration | Notes |
|-----------|-------------------|-------|
| Single validation (no Vision) | ~2s | Duration + player count only |
| Single validation (with Vision) | ~10s | Includes frame extraction + Vision API |
| Batch 100 hands (parallel) | ~20min | With Vision API enabled |
| BigQuery insert | ~500ms | Per validation result |
| Frame extraction | ~3s | 720p video, FFmpeg |
| Vision API call | ~3-5s | Label + face detection |

---

## Troubleshooting

### Issue 1: Vision API quota exceeded

**Symptom**: 429 errors from Vision API

**Solution**:
```bash
# Temporarily disable Vision API
export VISION_API_ENABLED=false

# Use duration-only validation
# Contact PM to increase quota
```

### Issue 2: FFmpeg not found

**Symptom**: `RuntimeError: FFmpeg extraction failed`

**Solution**:
```bash
# Install FFmpeg
apt-get install ffmpeg  # Linux
brew install ffmpeg     # macOS

# Set custom path
export FFMPEG_PATH=/custom/path/to/ffmpeg
```

### Issue 3: Mock data not found

**Symptom**: `FileNotFoundError: mock_data/bigquery/hand_summary_mock.json`

**Solution**:
```bash
# Ensure you're in the correct directory
cd modules/m3-timecode-validation

# Check mock data exists
ls ../../mock_data/bigquery/

# Set correct path
export BIGQUERY_MOCK_DATA=../../mock_data/bigquery/hand_summary_mock.json
```

---

## Dependencies

### Input Dependencies

- **M1 (Data Ingestion)**: Requires `prod.hand_summary` table
- **M2 (Video Metadata)**: Requires `prod.video_files` table

### External Services

- **Google Cloud Vision API**: Poker scene detection
- **Google Cloud BigQuery**: Data storage
- **Google Cloud Storage**: Frame storage
- **FFmpeg**: Frame extraction

---

## Metrics & Monitoring

### Key Metrics

- **Validation Success Rate**: 95%+ target
- **Average sync_score**: 85+ target
- **Vision API Error Rate**: < 5%
- **API Response Time**: < 2s (no Vision), < 15s (with Vision)

### Logging

Logs are sent to Google Cloud Logging:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Validation started: hand_id=wsop2024_me_d1_h001")
logger.error("Vision API failed: quota exceeded")
```

---

## Contributing

### Code Quality Standards

```bash
# Format code
black app/ tests/

# Lint code
pylint app/

# Type checking
flake8 app/
```

### Testing Requirements

- **Unit tests**: 80%+ code coverage
- **Integration tests**: All API endpoints
- **Mock tests**: Vision API, BigQuery

---

## License

Internal GG Production project - Confidential

---

## Contact

**Agent**: Charlie (M3 Timecode Validation Developer)
**Team**: GG Production Data Team
**Email**: aiden.kim@ggproduction.net
**Project**: POKER-BRAIN WSOP Archive System
**Version**: 1.0.0 (100% Complete)
**Last Updated**: 2025-01-17
