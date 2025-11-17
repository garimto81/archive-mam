# POKER-BRAIN: 모듈형 아키텍처 설계

**문서 버전**: 1.0
**작성일**: 2025-11-17
**목적**: 팀 협업을 위한 완전 독립형 모듈 분리

---

## 목차

1. [아키텍처 개요](#1-아키텍처-개요)
2. [모듈 분리 원칙](#2-모듈-분리-원칙)
3. [모듈 상세 스펙](#3-모듈-상세-스펙)
4. [API 명세](#4-api-명세)
5. [팀 할당 및 개발 가이드](#5-팀-할당-및-개발-가이드)
6. [통합 테스트](#6-통합-테스트)

---

## 1. 아키텍처 개요

### 1.1 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (Optional)                   │
│              Cloud Endpoints / Kong / None                   │
└────────────────────────┬────────────────────────────────────┘
                         ↓
        ┌────────────────┴────────────────┐
        ↓                                 ↓
┌───────────────┐                ┌───────────────┐
│   Module 1    │                │   Module 6    │
│ Data Ingestion│                │    Web UI     │
│   Service     │                │   Service     │
└───────┬───────┘                └───────┬───────┘
        ↓                                ↓
┌───────────────┐                ┌───────────────┐
│   Module 2    │                │   Module 5    │
│ Video Metadata│←──────────────→│   Clipping    │
│   Service     │                │   Service     │
└───────┬───────┘                └───────┬───────┘
        ↓                                ↓
┌───────────────┐                ┌───────────────┐
│   Module 3    │                │   Module 4    │
│  Timecode     │←──────────────→│  RAG Search   │
│  Validation   │                │   Service     │
└───────────────┘                └───────────────┘

        ↓                                ↓
┌─────────────────────────────────────────────┐
│         Shared Data Layer (BigQuery)        │
│  - hand_summary                             │
│  - video_files                              │
│  - timecode_validation                      │
│  - search_logs                              │
└─────────────────────────────────────────────┘
```

**핵심 원칙**: 각 모듈은 **독립적으로 배포**되며, **REST API**로만 통신

---

### 1.2 모듈 목록

| 모듈 ID | 모듈 이름 | 책임 | 언어/프레임워크 | 배포 |
|---------|----------|------|----------------|------|
| **M1** | Data Ingestion Service | ATI 데이터 → BigQuery ETL | Python/Dataflow | Cloud Run |
| **M2** | Video Metadata Service | NAS 스캔 → 메타데이터 추출 | Python/Flask | Cloud Run |
| **M3** | Timecode Validation Service | 타임코드 동기화 검증 (Phase 0) | Python/Flask | Cloud Run |
| **M4** | RAG Search Service | Vertex AI 검색 엔진 | Python/FastAPI | Cloud Run |
| **M5** | Clipping Service | FFmpeg 서브클립 생성 | Python/Celery | Local Agent |
| **M6** | Web UI Service | 검색 UI + 미리보기 | React/Next.js | Cloud Run |

---

## 2. 모듈 분리 원칙

### 2.1 독립성 (Independence)

각 모듈은:
- ✅ **독립 배포**: 다른 모듈 영향 없이 배포 가능
- ✅ **독립 테스트**: 모듈 내부 로직만으로 유닛 테스트
- ✅ **독립 스케일링**: 부하에 따라 개별 확장
- ✅ **독립 개발**: 팀원 간 병렬 작업 가능

### 2.2 통신 (Communication)

- **동기 통신**: REST API (HTTP/JSON)
- **비동기 통신**: Pub/Sub (이벤트 기반)
- **데이터 공유**: BigQuery (Read-only, 각자 테이블 소유)

### 2.3 인터페이스 계약 (Contract)

```yaml
API Contract:
  - OpenAPI 3.0 스펙 필수
  - 버전 관리: /v1/*, /v2/*
  - 에러 응답: 표준 JSON 포맷
  - 인증: Bearer Token (IAP)
```

---

## 3. 모듈 상세 스펙

### Module 1: Data Ingestion Service

**책임**: NSUS ATI 로우 데이터를 BigQuery로 ETL

#### 3.1.1 Input/Output

```yaml
Input:
  - Source: GCS Bucket (gs://ati-raw-data/)
  - Format: JSON Lines (.jsonl)
  - Trigger: Cloud Storage 이벤트 (파일 업로드 시)

Output:
  - Destination: BigQuery Table (prod.hand_summary)
  - Format: Structured rows
  - Notification: Pub/Sub Topic (data-ingestion-complete)
```

#### 3.1.2 API 엔드포인트

```http
POST /v1/ingest
Content-Type: application/json

Request:
{
  "gcs_path": "gs://ati-raw-data/2024-11-17/wsop_me_day3.jsonl",
  "event_id": "wsop2024_me",
  "tournament_day": 3
}

Response:
{
  "job_id": "ingest-20241117-001",
  "status": "processing",
  "estimated_rows": 1500,
  "estimated_duration_sec": 120
}

GET /v1/ingest/{job_id}/status

Response:
{
  "job_id": "ingest-20241117-001",
  "status": "completed",
  "rows_processed": 1482,
  "rows_failed": 18,
  "duration_sec": 95,
  "bigquery_table": "prod.hand_summary",
  "errors": [
    {
      "row_number": 154,
      "error": "Invalid timestamp format"
    }
  ]
}
```

#### 3.1.3 BigQuery 테이블 (소유)

```sql
CREATE TABLE prod.hand_summary (
  hand_id STRING NOT NULL,
  event_id STRING,
  event_name STRING,
  timestamp_start_utc TIMESTAMP,
  timestamp_end_utc TIMESTAMP,
  searchable_summary_text STRING,  -- Gemini 생성 (별도 프로세스)
  embedding ARRAY<FLOAT64>,  -- 나중에 M4에서 업데이트
  players ARRAY<STRING>,
  pot_size_usd NUMERIC,
  -- M1이 쓰기 권한, 나머지는 읽기만
  ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

#### 3.1.4 개발 가이드

**Tech Stack**:
- Python 3.11
- Apache Beam (Dataflow)
- `google-cloud-bigquery`

**로컬 개발**:
```bash
# 1. 샘플 데이터 준비
echo '{"hand_id": "test_001", ...}' > sample.jsonl

# 2. 로컬 실행 (DirectRunner)
python src/ingest_pipeline.py \
  --input sample.jsonl \
  --output test_dataset.test_table \
  --runner DirectRunner

# 3. 유닛 테스트
pytest tests/test_ingest_pipeline.py
```

**배포**:
```bash
gcloud run deploy data-ingestion-service \
  --source . \
  --region us-central1 \
  --service-account data-ingestion-sa@project.iam
```

**담당 팀**: Data Engineer

---

### Module 2: Video Metadata Service

**책임**: NAS 영상 파일 스캔 → 메타데이터 추출 → BigQuery

#### 3.2.1 Input/Output

```yaml
Input:
  - Source: NAS Mount Point (/nas/poker/)
  - Trigger: Cron (일 1회) 또는 수동 API 호출

Output:
  - Destination: BigQuery Table (prod.video_files)
  - Side Effect: Proxy 영상 생성 (GCS)
```

#### 3.2.2 API 엔드포인트

```http
POST /v1/scan
Content-Type: application/json

Request:
{
  "nas_path": "/nas/poker/2024/wsop/",
  "recursive": true,
  "generate_proxy": true,  -- GCS 프록시 생성 여부
  "proxy_resolution": "720p"
}

Response:
{
  "scan_id": "scan-20241117-001",
  "status": "running",
  "total_files": 150,
  "processed_files": 0
}

GET /v1/scan/{scan_id}/status

Response:
{
  "scan_id": "scan-20241117-001",
  "status": "completed",
  "total_files": 150,
  "processed_files": 148,
  "failed_files": 2,
  "duration_sec": 3600,
  "proxy_generated": 145
}

GET /v1/files/{file_id}

Response:
{
  "file_id": "vid_wsop2024_me_d3",
  "nas_path": "/nas/poker/2024/wsop/main_event_day3.mp4",
  "file_size_bytes": 52428800000,  // 50GB
  "duration_seconds": 36000,  // 10 hours
  "resolution": "1920x1080",
  "codec": "h264",
  "proxy_gcs_path": "gs://gg-proxy/wsop2024_me_d3_720p.mp4",
  "created_at": "2024-07-15T10:00:00Z"
}
```

#### 3.2.3 BigQuery 테이블 (소유)

```sql
CREATE TABLE prod.video_files (
  file_id STRING NOT NULL,
  nas_path STRING,
  file_name STRING,
  event_id STRING,
  duration_seconds FLOAT64,
  file_size_bytes INT64,
  resolution STRING,
  codec STRING,
  proxy_gcs_path STRING,  -- 720p 프록시
  is_archived BOOL DEFAULT FALSE,
  created_at TIMESTAMP,
  scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

#### 3.2.4 Proxy 생성 로직

```python
# src/proxy_generator.py
import ffmpeg

def generate_proxy(nas_path: str, output_gcs_path: str):
    """NAS 원본 → 720p H.264 프록시"""

    # FFmpeg 커맨드
    stream = ffmpeg.input(nas_path)
    stream = ffmpeg.filter(stream, 'scale', 1280, 720)
    stream = ffmpeg.output(
        stream,
        '/tmp/proxy.mp4',
        vcodec='libx264',
        crf=23,
        preset='medium',
        acodec='aac',
        audio_bitrate='128k'
    )
    ffmpeg.run(stream)

    # GCS 업로드
    upload_to_gcs('/tmp/proxy.mp4', output_gcs_path)
```

**담당 팀**: Backend Engineer

---

### Module 3: Timecode Validation Service

**책임**: ATI 타임스탬프 ↔ NAS 영상 타임코드 동기화 검증 (Phase 0)

#### 3.3.1 Input/Output

```yaml
Input:
  - hand_id (from BigQuery)
  - Expected: timestamp_start, timestamp_end
  - Video: nas_path (from M2)

Output:
  - Validation Result: sync_score (0-100)
  - Offset: calculated_offset_seconds (if needed)
  - Destination: BigQuery (prod.timecode_validation)
```

#### 3.3.2 API 엔드포인트

```http
POST /v1/validate
Content-Type: application/json

Request:
{
  "hand_id": "wsop2024_me_d3_h154",
  "timestamp_start_utc": "2024-07-15T15:24:15Z",
  "timestamp_end_utc": "2024-07-15T15:26:45Z",
  "nas_video_path": "/nas/poker/2024/wsop/.../day3.mp4",
  "use_vision_api": true
}

Response:
{
  "validation_id": "val-20241117-001",
  "status": "processing",
  "estimated_duration_sec": 30
}

GET /v1/validate/{validation_id}/result

Response:
{
  "validation_id": "val-20241117-001",
  "hand_id": "wsop2024_me_d3_h154",
  "sync_score": 94.5,  // 0-100
  "is_synced": true,   // score > 80
  "validation_method": "vision_api",
  "vision_confidence": 0.95,
  "detected_objects": ["poker_table", "playing_cards", "chips"],
  "calculated_offset_seconds": 0,  // 동기화 완벽
  "frame_sample_gcs": "gs://validation-frames/val-001.jpg"
}

POST /v1/validate/batch
Content-Type: application/json

Request:
{
  "hand_ids": ["hand_001", "hand_002", ...],  // 최대 100개
  "use_vision_api": true
}

Response:
{
  "batch_id": "batch-20241117-001",
  "total_hands": 100,
  "status": "queued"
}
```

#### 3.3.3 검증 알고리즘

```python
# src/validator.py
from google.cloud import vision

def validate_timecode(hand, video_path) -> dict:
    """
    타임코드 검증 + Vision AI

    Returns:
        {
            "sync_score": float (0-100),
            "is_synced": bool,
            "vision_confidence": float,
            "calculated_offset": float
        }
    """

    # 1. 예상 타임코드로 프레임 추출
    start_sec = hand.timestamp_start.timestamp()
    frame_jpg = extract_frame(video_path, start_sec)

    # 2. Vision API 호출
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=frame_jpg)

    # Object Detection
    objects = client.object_localization(image=image).localized_object_annotations

    # 포커 관련 객체 확인
    poker_objects = ["table", "playing card", "poker chip", "person"]
    detected = [obj.name for obj in objects if obj.score > 0.7]

    confidence = sum([obj.score for obj in objects if obj.name in poker_objects]) / len(poker_objects)

    # 3. 동기화 점수 계산
    score = 0.0

    # Vision confidence (50점)
    if confidence > 0.8:
        score += 50

    # Duration match (30점)
    expected_duration = (hand.timestamp_end - hand.timestamp_start).total_seconds()
    # ... 추가 검증

    # 4. Offset 계산 (필요 시)
    offset = 0
    if score < 80:
        offset = calculate_offset(hand, video_path)

    return {
        "sync_score": score,
        "is_synced": score > 80,
        "vision_confidence": confidence,
        "calculated_offset": offset
    }
```

#### 3.3.4 BigQuery 테이블 (소유)

```sql
CREATE TABLE prod.timecode_validation (
  validation_id STRING NOT NULL,
  hand_id STRING,
  sync_score FLOAT64,
  is_synced BOOL,
  vision_confidence FLOAT64,
  detected_objects ARRAY<STRING>,
  calculated_offset_seconds FLOAT64,
  validation_method STRING,  -- "vision_api", "manual"
  validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

**담당 팀**: Backend Engineer (Vision API 경험 필요)

---

### Module 4: RAG Search Service

**책임**: Vertex AI 기반 자연어 검색

#### 3.4.1 Input/Output

```yaml
Input:
  - User Query: "Tom Dwan 2008 블러프"
  - Filters: {players: ["Tom Dwan"], year: 2008}

Output:
  - Search Results: 관련 핸드 리스트 (relevance 순)
```

#### 3.4.2 API 엔드포인트

```http
POST /v1/search
Content-Type: application/json
Authorization: Bearer {token}

Request:
{
  "query": "Tom Dwan의 2008년 메인 이벤트 블러프 장면",
  "limit": 20,
  "filters": {
    "players": ["Tom Dwan"],
    "event_name_contains": "WSOP",
    "year_range": [2008, 2008],
    "pot_size_min": 100000
  },
  "include_proxy": true  -- Proxy URL 포함 여부
}

Response:
{
  "query_id": "search-20241117-001",
  "total_results": 156,
  "results": [
    {
      "hand_id": "wsop2008_me_d3_h154",
      "relevance_score": 0.94,
      "summary": "Tom Dwan, J4o, river all-in bluff vs Phil Hellmuth, won $450K pot",
      "event_name": "2008 WSOP Main Event",
      "timestamp_start": "2024-07-15T15:24:15Z",
      "timestamp_end": "2024-07-15T15:26:45Z",
      "nas_path": "/nas/poker/2008/.../day3.mp4",
      "timecode_offset": "03:24:15",
      "proxy_url": "https://storage.googleapis.com/gg-proxy/...",
      "players": ["Tom Dwan", "Phil Hellmuth"],
      "pot_size_usd": 450000
    },
    ...
  ],
  "processing_time_ms": 245
}

POST /v1/search/feedback
Content-Type: application/json

Request:
{
  "query_id": "search-20241117-001",
  "hand_id": "wsop2008_me_d3_h154",
  "feedback": "relevant"  // "relevant" | "not_relevant" | "favorite"
}

Response:
{
  "status": "ok",
  "message": "Feedback recorded"
}
```

#### 3.4.3 Vertex AI 통합

```python
# src/rag_engine.py
from google.cloud import aiplatform
from vertexai.preview import rag

def search_hands(query: str, filters: dict) -> list:
    """
    Vertex AI RAG 검색

    Process:
    1. 쿼리 → Embedding (textembedding-004)
    2. Vector Search (Vertex AI)
    3. BigQuery 메타데이터 조인
    4. Re-ranking (feedback 기반)
    """

    # 1. Embedding
    embedding_model = aiplatform.TextEmbeddingModel.from_pretrained(
        "textembedding-004"
    )
    query_embedding = embedding_model.get_embeddings([query])[0].values

    # 2. Vector Search
    index = aiplatform.MatchingEngineIndex(index_name="hand-embeddings")
    neighbors = index.find_neighbors(
        deployed_index_id="hand-embeddings-deployed",
        queries=[query_embedding],
        num_neighbors=100
    )

    # 3. BigQuery 조인 (메타데이터)
    hand_ids = [n.id for n in neighbors[0]]
    bq_query = f"""
    SELECT * FROM prod.hand_summary
    WHERE hand_id IN UNNEST(@hand_ids)
      AND 'Tom Dwan' IN UNNEST(players)  -- Filter
    ORDER BY ARRAY_POSITION(@hand_ids, hand_id)
    LIMIT 20
    """

    results = bigquery_client.query(bq_query,
        job_config=QueryJobConfig(
            query_parameters=[
                ArrayQueryParameter("hand_ids", "STRING", hand_ids)
            ]
        )
    ).result()

    return list(results)
```

#### 3.4.4 BigQuery 테이블 (읽기 전용)

- `prod.hand_summary` (M1이 관리)
- `prod.search_logs` (M4가 쓰기)

```sql
CREATE TABLE prod.search_logs (
  query_id STRING NOT NULL,
  user_email STRING,
  query_text STRING,
  filters JSON,
  total_results INT64,
  processing_time_ms INT64,
  searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE prod.search_feedback (
  query_id STRING,
  hand_id STRING,
  feedback STRING,  -- "relevant", "not_relevant", "favorite"
  user_email STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

**담당 팀**: ML Engineer 또는 Backend Engineer

---

### Module 5: Clipping Service

**책임**: FFmpeg 서브클립 생성 + GCS 업로드

#### 3.5.1 Input/Output

```yaml
Input:
  - Trigger: Pub/Sub Message (user downloads clip)
  - Data: hand_id, nas_path, timecode

Output:
  - Subclip: GCS (gs://gg-subclips/{hand_id}.mp4)
  - Notification: Pub/Sub (clipping-complete)
```

#### 3.5.2 Pub/Sub 메시지 스펙

```json
// Topic: projects/gg-poker/topics/clipping-requests

{
  "request_id": "clip-20241117-001",
  "hand_id": "wsop2024_me_d3_h154",
  "nas_video_path": "/nas/poker/2024/wsop/.../day3.mp4",
  "start_seconds": 12255,
  "end_seconds": 12405,
  "user_email": "han.pd@gg.com",
  "output_quality": "high",  // "high" | "medium"
  "requested_at": "2024-11-17T10:30:00Z"
}

// Topic: projects/gg-poker/topics/clipping-complete

{
  "request_id": "clip-20241117-001",
  "hand_id": "wsop2024_me_d3_h154",
  "status": "completed",  // "completed" | "failed"
  "output_gcs_path": "gs://gg-subclips/wsop2024_me_d3_h154.mp4",
  "file_size_bytes": 52428800,
  "duration_seconds": 150,
  "download_url": "https://storage.googleapis.com/...",  // Signed URL
  "processing_time_seconds": 45,
  "completed_at": "2024-11-17T10:31:00Z",
  "error_message": null
}
```

#### 3.5.3 Local Agent 구현

```python
# src/clipping_agent.py
import os
import ffmpeg
from google.cloud import pubsub_v1, storage

class ClippingAgent:
    def __init__(self):
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = "projects/gg-poker/subscriptions/clipping-worker"

    def callback(self, message):
        """Pub/Sub 메시지 처리"""
        data = json.loads(message.data)

        try:
            # 1. FFmpeg 클리핑
            output_path = self.create_subclip(
                nas_path=data['nas_video_path'],
                start=data['start_seconds'],
                end=data['end_seconds'],
                hand_id=data['hand_id']
            )

            # 2. GCS 업로드
            gcs_path = self.upload_to_gcs(output_path, data['hand_id'])

            # 3. Signed URL 생성
            download_url = self.generate_signed_url(gcs_path)

            # 4. 완료 알림
            self.publish_complete(data['request_id'], gcs_path, download_url)

            message.ack()

        except Exception as e:
            self.publish_failed(data['request_id'], str(e))
            message.nack()

    def create_subclip(self, nas_path, start, end, hand_id) -> str:
        """FFmpeg 서브클립 생성"""
        output = f"/tmp/{hand_id}.mp4"

        stream = ffmpeg.input(nas_path, ss=start, to=end)
        stream = ffmpeg.output(stream, output,
            vcodec='copy',  # Re-encoding 없이 빠른 복사
            acodec='copy',
            avoid_negative_ts='make_zero'
        )
        ffmpeg.run(stream, overwrite_output=True)

        return output

    def upload_to_gcs(self, local_path, hand_id) -> str:
        """GCS 업로드"""
        bucket_name = "gg-subclips"
        blob_name = f"{hand_id}.mp4"

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)

        return f"gs://{bucket_name}/{blob_name}"

    def run(self):
        """메인 루프"""
        print("Clipping Agent started...")
        self.subscriber.subscribe(self.subscription_path, callback=self.callback)

        # Keep alive
        while True:
            time.sleep(60)

if __name__ == "__main__":
    agent = ClippingAgent()
    agent.run()
```

#### 3.5.4 High Availability

```yaml
Primary Agent:
  - Host: nas-server-01
  - Status: Active

Standby Agent:
  - Host: nas-server-02
  - Status: Standby
  - Health Check: 매 1분마다 Primary 확인
  - Failover: Primary 3회 연속 실패 시 자동 전환
```

**담당 팀**: DevOps Engineer 또는 Backend Engineer

---

### Module 6: Web UI Service

**책임**: 사용자 인터페이스 (검색, 미리보기, 다운로드)

#### 3.6.1 기술 스택

```yaml
Frontend:
  - Framework: Next.js 14 (App Router)
  - UI Library: shadcn/ui (Tailwind CSS)
  - State: React Query (Server State)
  - Auth: Google IAP (Automatic)

Backend for Frontend (BFF):
  - API Routes: Next.js API Routes
  - Purpose: M4, M5와 통신하는 중간 계층
```

#### 3.6.2 주요 페이지

```
/                    → 검색 페이지
/search?q=Tom+Dwan   → 검색 결과
/hand/{hand_id}      → 핸드 상세 + 미리보기
/downloads           → 내가 다운로드한 클립 목록
/admin               → 관리자 대시보드 (Phase 0 진행률)
```

#### 3.6.3 API 통합

```typescript
// src/app/api/search/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { query, filters } = await req.json();

  // M4 (RAG Search Service) 호출
  const response = await fetch('https://rag-search-service-xxx.run.app/v1/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${await getServiceToken()}`
    },
    body: JSON.stringify({ query, filters, limit: 20 })
  });

  const results = await response.json();

  return NextResponse.json(results);
}

// src/app/api/download/route.ts
export async function POST(req: NextRequest) {
  const { hand_id } = await req.json();

  // BigQuery에서 핸드 정보 조회
  const hand = await getHandInfo(hand_id);

  // Pub/Sub에 클리핑 요청 발행
  await publishClippingRequest({
    hand_id,
    nas_path: hand.nas_path,
    start_seconds: hand.timecode_start,
    end_seconds: hand.timecode_end,
    user_email: req.headers.get('x-goog-authenticated-user-email')
  });

  return NextResponse.json({
    status: 'queued',
    message: '클립 생성 중입니다. 5분 내 완료됩니다.'
  });
}
```

#### 3.6.4 UI 컴포넌트

```typescript
// src/components/SearchResults.tsx
'use client';

import { useQuery } from '@tanstack/react-query';

export function SearchResults({ query }) {
  const { data, isLoading } = useQuery({
    queryKey: ['search', query],
    queryFn: async () => {
      const res = await fetch('/api/search', {
        method: 'POST',
        body: JSON.stringify({ query })
      });
      return res.json();
    }
  });

  if (isLoading) return <div>검색 중...</div>;

  return (
    <div className="grid gap-4">
      {data.results.map(hand => (
        <HandCard key={hand.hand_id} hand={hand} />
      ))}
    </div>
  );
}

// src/components/VideoPreview.tsx
export function VideoPreview({ proxyUrl }) {
  return (
    <video controls className="w-full rounded-lg">
      <source src={proxyUrl} type="video/mp4" />
    </video>
  );
}
```

**담당 팀**: Frontend Engineer

---

## 4. API 명세

### 4.1 인증 (Authentication)

모든 API는 **Google IAP (Identity-Aware Proxy)**로 보호됩니다.

```http
Authorization: Bearer {IAP_JWT_TOKEN}
```

**로컬 개발 시**:
```bash
# Service Account 키 사용
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"

# API 호출
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
     https://api.example.com/v1/search
```

### 4.2 에러 응답 표준

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "hand_id is required",
    "details": {
      "field": "hand_id",
      "reason": "missing"
    }
  },
  "request_id": "req-20241117-001",
  "timestamp": "2024-11-17T10:30:00Z"
}
```

**에러 코드**:
```yaml
INVALID_REQUEST: 400 Bad Request
UNAUTHORIZED: 401 Unauthorized
FORBIDDEN: 403 Forbidden
NOT_FOUND: 404 Not Found
INTERNAL_ERROR: 500 Internal Server Error
SERVICE_UNAVAILABLE: 503 Service Unavailable
```

### 4.3 OpenAPI 스펙

각 모듈은 `/openapi.json` 엔드포인트를 제공합니다.

```bash
# M4 (RAG Search Service)
curl https://rag-search-service-xxx.run.app/openapi.json

# 자동 문서 생성
swagger-ui-watcher openapi.json
```

---

## 5. 팀 할당 및 개발 가이드

### 5.1 팀 구성

| 팀원 | 담당 모듈 | 주요 역할 |
|------|----------|----------|
| **Alice** | M1 (Data Ingestion) | Data Engineer, ETL 파이프라인 |
| **Bob** | M2 (Video Metadata) | Backend Engineer, NAS/FFmpeg |
| **Charlie** | M3 (Timecode Validation) | Backend Engineer, Vision API |
| **David** | M4 (RAG Search) | ML Engineer, Vertex AI |
| **Eve** | M5 (Clipping Service) | DevOps/Backend, Local Agent |
| **Frank** | M6 (Web UI) | Frontend Engineer, React |

### 5.2 개발 워크플로우

```
Week 1-2: 모듈 스펙 확정 + API 설계
├─ 각 팀원이 담당 모듈의 OpenAPI 스펙 작성
├─ API Contract Review (전체 팀)
└─ Mock API 서버 구축 (협업용)

Week 3-6: 독립 개발
├─ 각자 모듈 구현 (유닛 테스트 포함)
├─ Mock API로 다른 모듈과 통신 테스트
└─ 주간 Sync-up (진행 상황 공유)

Week 7-8: 통합 테스트
├─ 모든 모듈 배포 (Staging 환경)
├─ E2E 테스트 작성 및 실행
└─ 버그 수정

Week 9: Production 배포
```

### 5.3 로컬 개발 환경

각 모듈은 **Docker Compose**로 로컬 실행 가능:

```yaml
# docker-compose.yml
version: '3.8'

services:
  # M1: Data Ingestion
  data-ingestion:
    build: ./modules/data-ingestion
    ports:
      - "8001:8080"
    environment:
      - GOOGLE_CLOUD_PROJECT=dev-project
      - BIGQUERY_DATASET=dev

  # M2: Video Metadata
  video-metadata:
    build: ./modules/video-metadata
    ports:
      - "8002:8080"
    volumes:
      - /path/to/nas:/nas:ro

  # M4: RAG Search
  rag-search:
    build: ./modules/rag-search
    ports:
      - "8004:8080"
    environment:
      - VERTEX_AI_LOCATION=us-central1

  # M6: Web UI
  web-ui:
    build: ./modules/web-ui
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE=http://localhost:8004
```

**실행**:
```bash
docker-compose up
```

**각 모듈 접근**:
- M1: http://localhost:8001
- M2: http://localhost:8002
- M4: http://localhost:8004
- M6: http://localhost:3000

---

## 6. 통합 테스트

### 6.1 E2E 테스트 시나리오

```yaml
Test Case 1: 검색 → 미리보기 → 다운로드 (전체 플로우)

Steps:
  1. M6 (Web UI): 사용자가 "Tom Dwan 블러프" 검색
  2. M6 → M4 (RAG Search): API 호출
  3. M4 → BigQuery: 검색 실행
  4. M4 → M6: 결과 반환
  5. M6: 프록시 영상 미리보기 (GCS)
  6. M6: [다운로드] 버튼 클릭
  7. M6 → Pub/Sub: 클리핑 요청 발행
  8. M5 (Local Agent): Pub/Sub 수신
  9. M5: FFmpeg 클리핑 실행
  10. M5 → GCS: 업로드
  11. M5 → Pub/Sub: 완료 알림
  12. M6: 다운로드 링크 표시

Expected:
  - 총 소요 시간 < 5분
  - 클립 파일 크기: 예상 범위 내
  - 사용자에게 Signed URL 제공
```

### 6.2 테스트 자동화

```python
# tests/e2e/test_full_workflow.py
import pytest
import requests
import time

@pytest.mark.e2e
def test_search_to_download():
    """검색 → 다운로드 전체 플로우"""

    # 1. 검색
    response = requests.post(
        "https://web-ui-xxx.run.app/api/search",
        json={"query": "Tom Dwan bluff"},
        headers={"Authorization": f"Bearer {get_token()}"}
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results['results']) > 0

    hand_id = results['results'][0]['hand_id']

    # 2. 다운로드 요청
    response = requests.post(
        "https://web-ui-xxx.run.app/api/download",
        json={"hand_id": hand_id}
    )
    assert response.status_code == 200

    # 3. 완료 대기 (최대 5분)
    for i in range(60):  # 5분 = 60 × 5초
        time.sleep(5)

        # 완료 확인 (Pub/Sub 또는 DB 확인)
        status = check_clipping_status(hand_id)
        if status == "completed":
            break

    assert status == "completed"

    # 4. 다운로드 URL 확인
    download_url = get_download_url(hand_id)
    assert download_url.startswith("https://storage.googleapis.com/")

    # 5. 파일 다운로드 테스트
    file_response = requests.get(download_url)
    assert file_response.status_code == 200
    assert len(file_response.content) > 1024 * 1024  # > 1MB
```

---

## 7. 배포 전략

### 7.1 CI/CD Pipeline

```yaml
# .github/workflows/deploy-module.yml
name: Deploy Module

on:
  push:
    branches: [main]
    paths:
      - 'modules/*/src/**'

jobs:
  detect-changed-modules:
    runs-on: ubuntu-latest
    outputs:
      modules: ${{ steps.changes.outputs.modules }}
    steps:
      - uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            data-ingestion:
              - 'modules/data-ingestion/**'
            video-metadata:
              - 'modules/video-metadata/**'
            rag-search:
              - 'modules/rag-search/**'

  deploy:
    needs: detect-changed-modules
    strategy:
      matrix:
        module: ${{ fromJSON(needs.detect-changed-modules.outputs.modules) }}
    steps:
      - uses: actions/checkout@v3

      - name: Deploy ${{ matrix.module }}
        run: |
          cd modules/${{ matrix.module }}
          gcloud run deploy ${{ matrix.module }}-service \
            --source . \
            --region us-central1
```

**장점**: 변경된 모듈만 자동 배포 → 빠른 배포

---

## 8. 모니터링 및 로깅

### 8.1 표준 로깅 포맷

```json
{
  "severity": "INFO",
  "timestamp": "2024-11-17T10:30:00Z",
  "module": "rag-search-service",
  "trace_id": "trace-001",
  "message": "Search completed",
  "metadata": {
    "query": "Tom Dwan bluff",
    "results_count": 12,
    "processing_time_ms": 245
  }
}
```

### 8.2 Cloud Monitoring Dashboards

각 모듈별 대시보드:

```yaml
M1 (Data Ingestion):
  - Metric: ingestion_rows_per_sec
  - Alert: rows_failed > 100

M4 (RAG Search):
  - Metric: search_latency_p95
  - Alert: p95 > 10 seconds

M5 (Clipping):
  - Metric: clipping_queue_depth
  - Alert: queue > 50
```

---

## 부록 A: 의존성 그래프

```
M1 (Data Ingestion)
  └─> BigQuery (hand_summary)

M2 (Video Metadata)
  └─> BigQuery (video_files)
  └─> GCS (Proxy 업로드)

M3 (Timecode Validation)
  ├─> M1 (hand_summary 읽기)
  ├─> M2 (video_files 읽기)
  ├─> Vision API
  └─> BigQuery (timecode_validation)

M4 (RAG Search)
  ├─> M1 (hand_summary 읽기)
  ├─> Vertex AI
  └─> BigQuery (search_logs)

M5 (Clipping)
  ├─> Pub/Sub (구독)
  ├─> NAS (읽기)
  ├─> GCS (업로드)
  └─> Pub/Sub (발행)

M6 (Web UI)
  ├─> M4 (검색 API)
  ├─> M5 (클리핑 요청)
  └─> GCS (Proxy 재생)
```

**핵심**: M1, M2는 의존성 없음 → **가장 먼저 개발 시작**

---

## 부록 B: 개발 체크리스트

### M1 (Data Ingestion) - Alice

- [ ] BigQuery 테이블 생성 (`hand_summary`)
- [ ] Dataflow 파이프라인 구현
- [ ] OpenAPI 스펙 작성
- [ ] `/v1/ingest` API 구현
- [ ] 유닛 테스트 작성 (pytest)
- [ ] Cloud Run 배포
- [ ] 샘플 데이터로 E2E 테스트

### M2 (Video Metadata) - Bob

- [ ] NAS 마운트 설정
- [ ] FFmpeg 메타데이터 추출 로직
- [ ] Proxy 생성 로직 (720p H.264)
- [ ] BigQuery 테이블 (`video_files`)
- [ ] `/v1/scan` API 구현
- [ ] GCS 업로드 구현
- [ ] 유닛 테스트
- [ ] Cloud Run 배포

### M3 (Timecode Validation) - Charlie

- [ ] Vision API 통합
- [ ] 동기화 점수 알고리즘 구현
- [ ] Offset 계산 로직
- [ ] `/v1/validate` API 구현
- [ ] BigQuery 테이블 (`timecode_validation`)
- [ ] 유닛 테스트
- [ ] 샘플 10개로 정확도 검증

### M4 (RAG Search) - David

- [ ] Vertex AI Vector Search 설정
- [ ] TextEmbedding-004 통합
- [ ] `/v1/search` API 구현
- [ ] Feedback 시스템 구현
- [ ] BigQuery 테이블 (`search_logs`)
- [ ] 유닛 테스트
- [ ] 검색 정확도 측정

### M5 (Clipping) - Eve

- [ ] Pub/Sub 토픽/구독 생성
- [ ] Local Agent 구현 (Python Daemon)
- [ ] FFmpeg 클리핑 로직
- [ ] GCS 업로드 로직
- [ ] Signed URL 생성
- [ ] HA 설정 (Primary + Standby)
- [ ] systemd 서비스 등록

### M6 (Web UI) - Frank

- [ ] Next.js 프로젝트 초기화
- [ ] 검색 UI 구현
- [ ] 미리보기 플레이어 구현
- [ ] 다운로드 UI 구현
- [ ] M4 API 통합
- [ ] IAP 인증 테스트
- [ ] Vercel 또는 Cloud Run 배포

---

**문서 작성자**: Claude (GG Production AI Assistant)
**최종 검토**: aiden.kim@ggproduction.net
**버전**: 1.0
**다음 단계**: 각 팀원에게 모듈 할당 후 Week 1 킥오프 미팅
