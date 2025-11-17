# Mock 데이터 전략 (완전 병렬 개발)

**목적**: 6명 팀원이 Week 3부터 동시에 독립 개발 가능하도록 Mock 데이터 제공
**작성일**: 2025-11-17
**버전**: 2.0.0 (Full Parallel 지원)

---

## 1. 전략 개요

### 1.1 왜 Mock 데이터가 필요한가?

**문제**: 의존성으로 인한 개발 블로킹

```
Charlie (M3) → M1, M2 완료 필요
David (M4) → M1 완료 필요
    ↓
Week 3에 시작 불가 (M1, M2는 Week 4 완료)
```

**해결**: Mock 데이터로 완전 독립 개발

```
Charlie (M3) → Mock BigQuery (hand_summary, video_files)
David (M4) → Mock BigQuery (hand_summary) + Mock Embeddings
Eve (M5) → Pub/Sub Emulator
Frank (M6) → Prism Mock Servers (M3, M4, M5)
    ↓
Week 3부터 6명 전원 동시 시작 ✅
```

---

## 2. Mock 데이터 아키텍처

### 2.1 데이터 레이어

```
┌─────────────────────────────────────────────┐
│          Production Data (Real)              │
│  ├─ prod.hand_summary (M1 생성)             │
│  ├─ prod.video_files (M2 생성)              │
│  └─ prod.timecode_validation (M3 생성)      │
└─────────────────────────────────────────────┘
                     ↑
                     │ Week 7 전환
                     ↓
┌─────────────────────────────────────────────┐
│          Mock Data (Development)             │
│  ├─ dev.hand_summary_mock (PM 생성)        │
│  ├─ dev.video_files_mock (PM 생성)         │
│  ├─ Pub/Sub Emulator (로컬)                │
│  └─ Prism Mock Servers (로컬)              │
└─────────────────────────────────────────────┘
```

### 2.2 환경 분리

```python
# 모든 모듈 공통 패턴
import os

ENV = os.getenv('POKER_ENV', 'development')  # development | production

if ENV == 'development':
    BIGQUERY_DATASET = 'dev'
    USE_MOCK_DATA = True
else:
    BIGQUERY_DATASET = 'prod'
    USE_MOCK_DATA = False
```

---

## 3. 모듈별 Mock 데이터 사양

### 3.1 M1 (Data Ingestion) - Mock 불필요

**이유**: M1은 독립 모듈이며, GCS 샘플 파일로 개발 가능

```bash
# Week 2: PM이 샘플 JSONL 파일 준비
gsutil cp sample-data/ati-sample.jsonl gs://gg-poker-dev/ati/sample.jsonl
```

**샘플 데이터** (10 hands):
```jsonl
{"hand_id": "wsop2024_me_d1_h001", "event_id": "wsop2024_me", "tournament_day": 1, "hand_number": 1, "table_number": 1, "timestamp_start_utc": "2024-07-05T12:00:00Z", "timestamp_end_utc": "2024-07-05T12:02:30Z", "players": ["Phil Ivey", "Daniel Negreanu"], "pot_size_usd": 12500}
{"hand_id": "wsop2024_me_d1_h002", "event_id": "wsop2024_me", "tournament_day": 1, "hand_number": 2, "table_number": 1, "timestamp_start_utc": "2024-07-05T12:03:00Z", "timestamp_end_utc": "2024-07-05T12:05:45Z", "players": ["Tom Dwan", "Phil Hellmuth"], "pot_size_usd": 8750}
...
```

---

### 3.2 M2 (Video Metadata) - Mock 불필요

**이유**: M2도 독립 모듈이며, 샘플 영상 파일로 개발 가능

```bash
# Week 2: PM이 샘플 영상 준비 (NAS 또는 로컬)
/nas/poker/sample/wsop2024_me_d1_table1.mp4  # 10분 샘플 영상
```

**FFmpeg 메타데이터 추출 예시**:
```bash
ffmpeg -i /nas/poker/sample/wsop2024_me_d1_table1.mp4 -hide_banner
# → duration: 600s, resolution: 1920x1080, codec: h264
```

---

### 3.3 M3 (Timecode Validation) - Mock 필요 ⭐

**의존성**: M1 (hand_summary), M2 (video_files)

#### Mock BigQuery 테이블

```sql
-- Week 2: PM 실행
CREATE TABLE `gg-poker.dev.hand_summary_mock` (
  hand_id STRING NOT NULL,
  event_id STRING,
  tournament_day INT64,
  hand_number INT64,
  table_number INT64,
  timestamp_start_utc TIMESTAMP,
  timestamp_end_utc TIMESTAMP,
  duration_seconds INT64,
  players ARRAY<STRING>,
  pot_size_usd NUMERIC
);

CREATE TABLE `gg-poker.dev.video_files_mock` (
  video_id STRING NOT NULL,
  event_id STRING,
  tournament_day INT64,
  table_number INT64,
  nas_file_path STRING,
  gcs_proxy_path STRING,
  duration_seconds INT64,
  resolution STRING,
  codec STRING,
  file_size_bytes INT64,
  indexed_at TIMESTAMP
);
```

#### Mock 데이터 생성 스크립트

```python
# scripts/generate_mock_data_m3.py
import random
from datetime import datetime, timedelta
from google.cloud import bigquery

client = bigquery.Client(project='gg-poker')

# 1000개 hand_summary Mock 데이터 생성
hands = []
players_pool = ["Phil Ivey", "Daniel Negreanu", "Tom Dwan", "Phil Hellmuth",
                "Doyle Brunson", "Johnny Chan", "Vanessa Selbst"]

base_time = datetime(2024, 7, 5, 12, 0, 0)
for i in range(1, 1001):
    hand = {
        'hand_id': f'wsop2024_me_d{(i-1)//100 + 1}_h{i:04d}',
        'event_id': 'wsop2024_me',
        'tournament_day': (i - 1) // 100 + 1,
        'hand_number': i,
        'table_number': (i - 1) % 10 + 1,
        'timestamp_start_utc': (base_time + timedelta(minutes=i*3)).isoformat(),
        'timestamp_end_utc': (base_time + timedelta(minutes=i*3 + 2)).isoformat(),
        'duration_seconds': random.randint(90, 180),
        'players': random.sample(players_pool, k=random.randint(2, 6)),
        'pot_size_usd': random.randint(500, 50000)
    }
    hands.append(hand)

# BigQuery 삽입
table_ref = client.dataset('dev').table('hand_summary_mock')
errors = client.insert_rows_json(table_ref, hands)
print(f"Inserted {len(hands)} hands, errors: {errors}")

# 100개 video_files Mock 데이터 생성
videos = []
for day in range(1, 11):
    for table in range(1, 11):
        video = {
            'video_id': f'wsop2024_me_d{day}_t{table}',
            'event_id': 'wsop2024_me',
            'tournament_day': day,
            'table_number': table,
            'nas_file_path': f'/nas/poker/wsop2024/me/day{day}/table{table}.mp4',
            'gcs_proxy_path': f'gs://gg-poker-proxy/wsop2024/me/d{day}_t{table}_720p.mp4',
            'duration_seconds': random.randint(18000, 36000),  # 5-10시간
            'resolution': '1920x1080',
            'codec': 'h264',
            'file_size_bytes': random.randint(5_000_000_000, 15_000_000_000),
            'indexed_at': datetime.utcnow().isoformat()
        }
        videos.append(video)

table_ref = client.dataset('dev').table('video_files_mock')
errors = client.insert_rows_json(table_ref, videos)
print(f"Inserted {len(videos)} videos, errors: {errors}")
```

#### M3 코드 예시 (Mock 연동)

```python
# m3-timecode-validation/app/bigquery_client.py
import os
from google.cloud import bigquery

ENV = os.getenv('POKER_ENV', 'development')
DATASET = 'dev' if ENV == 'development' else 'prod'
HAND_TABLE = f'{DATASET}.hand_summary_mock' if ENV == 'development' else f'{DATASET}.hand_summary'
VIDEO_TABLE = f'{DATASET}.video_files_mock' if ENV == 'development' else f'{DATASET}.video_files'

client = bigquery.Client(project='gg-poker')

def get_hand_metadata(hand_id: str):
    query = f"""
    SELECT
        hand_id,
        timestamp_start_utc,
        duration_seconds,
        players
    FROM `gg-poker.{HAND_TABLE}`
    WHERE hand_id = @hand_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("hand_id", "STRING", hand_id)
        ]
    )
    return list(client.query(query, job_config=job_config))[0]
```

---

### 3.4 M4 (RAG Search) - Mock 필요 ⭐

**의존성**: M1 (hand_summary)

#### Mock BigQuery + Mock Embeddings

```sql
-- Week 2: PM 실행 (M3과 동일한 hand_summary_mock 재사용)
-- 추가로 embeddings 테이블 생성

CREATE TABLE `gg-poker.dev.hand_embeddings_mock` (
  hand_id STRING NOT NULL,
  summary_text STRING,
  embedding ARRAY<FLOAT64>  -- 768-dim vector (TextEmbedding-004)
);
```

#### Mock Embedding 생성 스크립트

```python
# scripts/generate_mock_embeddings_m4.py
import random
from google.cloud import bigquery

client = bigquery.Client(project='gg-poker')

# Mock embedding (실제로는 Vertex AI로 생성하지만, 개발 중에는 랜덤)
embeddings = []
for i in range(1, 1001):
    hand_id = f'wsop2024_me_d{(i-1)//100 + 1}_h{i:04d}'
    summary = f"Hand {i}: Tom Dwan raises pre-flop, Phil Ivey calls"

    # 768-dim random vector (개발용)
    mock_vector = [random.gauss(0, 0.1) for _ in range(768)]

    embeddings.append({
        'hand_id': hand_id,
        'summary_text': summary,
        'embedding': mock_vector
    })

table_ref = client.dataset('dev').table('hand_embeddings_mock')
errors = client.insert_rows_json(table_ref, embeddings)
print(f"Inserted {len(embeddings)} embeddings")
```

#### M4 코드 예시 (Mock 연동)

```python
# m4-rag-search/app/search_engine.py
import os
import numpy as np
from google.cloud import bigquery

ENV = os.getenv('POKER_ENV', 'development')
USE_MOCK_EMBEDDINGS = ENV == 'development'

client = bigquery.Client(project='gg-poker')

def search_hands(query_text: str, top_k: int = 10):
    if USE_MOCK_EMBEDDINGS:
        # Mock: 단순 텍스트 매칭 (개발 중)
        query = f"""
        SELECT hand_id, summary_text, 0.8 as relevance_score
        FROM `gg-poker.dev.hand_embeddings_mock`
        WHERE LOWER(summary_text) LIKE LOWER(@query)
        LIMIT @top_k
        """
    else:
        # Real: Vertex AI Vector Search
        query_embedding = get_vertex_ai_embedding(query_text)
        query = f"""
        SELECT hand_id, summary_text,
            (SELECT SUM(a*b) FROM UNNEST(embedding) a WITH OFFSET
             JOIN UNNEST(@query_embedding) b WITH OFFSET
             USING(OFFSET)) as relevance_score
        FROM `gg-poker.prod.hand_embeddings`
        ORDER BY relevance_score DESC
        LIMIT @top_k
        """

    # 쿼리 실행 (나머지 동일)
    ...
```

---

### 3.5 M5 (Clipping) - Mock 필요 ⭐

**의존성**: Pub/Sub

#### Pub/Sub Emulator 설정

```bash
# Week 2: PM 실행
gcloud beta emulators pubsub start --project=gg-poker-dev --host-port=localhost:8085

# 별도 터미널에서 토픽/서브스크립션 생성
export PUBSUB_EMULATOR_HOST=localhost:8085

python scripts/setup_pubsub_emulator.py
```

```python
# scripts/setup_pubsub_emulator.py
from google.cloud import pubsub_v1

project_id = 'gg-poker-dev'
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

# 토픽 생성
topic_path = publisher.topic_path(project_id, 'clipping-requests')
publisher.create_topic(request={"name": topic_path})
print(f"Created topic: {topic_path}")

# 서브스크립션 생성
subscription_path = subscriber.subscription_path(project_id, 'clipping-requests-sub')
subscriber.create_subscription(
    request={"name": subscription_path, "topic": topic_path}
)
print(f"Created subscription: {subscription_path}")

# 완료 토픽
complete_topic = publisher.topic_path(project_id, 'clipping-complete')
publisher.create_topic(request={"name": complete_topic})
```

#### M5 코드 예시 (Mock 연동)

```python
# m5-clipping/local-agent/main.py
import os
from google.cloud import pubsub_v1

ENV = os.getenv('POKER_ENV', 'development')

# Emulator 자동 감지
if ENV == 'development':
    os.environ['PUBSUB_EMULATOR_HOST'] = 'localhost:8085'

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    'gg-poker-dev',
    'clipping-requests-sub'
)

def callback(message):
    data = json.loads(message.data.decode('utf-8'))
    hand_id = data['hand_id']

    # Mock: 실제 클리핑 대신 즉시 완료 처리
    if ENV == 'development':
        print(f"[MOCK] Clipping {hand_id} (skipped FFmpeg)")
        output_path = f'/tmp/mock-clips/{hand_id}.mp4'
    else:
        # Real: FFmpeg 실행
        output_path = clip_video(data)

    # 완료 메시지 발행
    publish_complete(data['request_id'], output_path)
    message.ack()

# 구독 시작
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
```

---

### 3.6 M6 (Web UI) - Mock 필요 ⭐

**의존성**: M3, M4, M5 API

#### Prism Mock Servers

```bash
# Week 2: PM 실행
npm install -g @stoplight/prism-cli

# 3개 Mock 서버 동시 실행 (docker-compose)
docker-compose -f docker-compose.mock.yml up
```

```yaml
# docker-compose.mock.yml
version: '3.8'

services:
  mock-m3:
    image: stoplight/prism:latest
    command: mock -h 0.0.0.0 /openapi.yaml
    volumes:
      - ./modules/timecode-validation/openapi.yaml:/openapi.yaml
    ports:
      - "8003:4010"
    environment:
      - PRISM_DYNAMIC=true

  mock-m4:
    image: stoplight/prism:latest
    command: mock -h 0.0.0.0 /openapi.yaml
    volumes:
      - ./modules/rag-search/openapi.yaml:/openapi.yaml
    ports:
      - "8004:4010"

  mock-m5:
    image: stoplight/prism:latest
    command: mock -h 0.0.0.0 /openapi.yaml
    volumes:
      - ./modules/clipping/openapi.yaml:/openapi.yaml
    ports:
      - "8005:4010"
```

#### M6 코드 예시 (Mock 연동)

```tsx
// m6-web-ui/lib/api-client.ts
const ENV = process.env.NEXT_PUBLIC_POKER_ENV || 'development';

export const API_ENDPOINTS = {
  M3_VALIDATION: ENV === 'development'
    ? 'http://localhost:8003/v1'
    : process.env.NEXT_PUBLIC_M3_API_URL,

  M4_SEARCH: ENV === 'development'
    ? 'http://localhost:8004/v1'
    : process.env.NEXT_PUBLIC_M4_API_URL,

  M5_CLIPPING: ENV === 'development'
    ? 'http://localhost:8005/v1'
    : process.env.NEXT_PUBLIC_M5_API_URL,
};

// BFF API Route 예시
// app/api/search/route.ts
export async function POST(req: NextRequest) {
  const body = await req.json();

  const response = await fetch(`${API_ENDPOINTS.M4_SEARCH}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  return NextResponse.json(await response.json());
}
```

---

## 4. Mock 데이터 준비 타임라인

### Week 2 (월-금)

#### Day 1-2 (월-화): Mock Infrastructure

**PM 작업**:
```bash
# BigQuery Mock 테이블 생성
python scripts/setup_mock_bigquery.py

# Pub/Sub Emulator 설정
bash scripts/setup_pubsub_emulator.sh

# Prism Mock 서버 시작
docker-compose -f docker-compose.mock.yml up -d
```

#### Day 3 (수): Mock Data Generation

**Alice (M1) 지원**:
```bash
# Mock BigQuery 데이터 생성
python scripts/generate_mock_data_m3.py  # → 1000 hands, 100 videos
python scripts/generate_mock_data_m4.py  # → 1000 embeddings
```

#### Day 4 (목): Validation

**전체 팀원**:
```bash
# M3 (Charlie): BigQuery Mock 연동 테스트
python -c "from app.bigquery_client import get_hand_metadata; print(get_hand_metadata('wsop2024_me_d1_h0001'))"

# M4 (David): Embedding Mock 테스트
python -c "from app.search_engine import search_hands; print(search_hands('Tom Dwan bluff'))"

# M5 (Eve): Pub/Sub Emulator 테스트
python scripts/test_pubsub_emulator.py

# M6 (Frank): Prism Mock 서버 테스트
curl http://localhost:8004/v1/search -X POST -d '{"query":"bluff"}'
```

#### Day 5 (금): Freeze & Document

**PM**:
- Mock 데이터 Freeze (변경 금지)
- `.env.development` 파일 전체 배포
- Week 3 개발 시작 선언 🚀

---

## 5. Mock → Real 전환 (Week 7)

### 5.1 전환 체크리스트

```markdown
## M3 Timecode Validation

- [ ] M1 (hand_summary) Production 데이터 검증
- [ ] M2 (video_files) Production 데이터 검증
- [ ] 환경 변수 변경: `POKER_ENV=production`
- [ ] BigQuery 테이블 변경: `dev.hand_summary_mock` → `prod.hand_summary`
- [ ] 통합 테스트 (실제 데이터 100 hands)
- [ ] 성능 테스트 (응답 시간 <2초)

## M4 RAG Search

- [ ] M1 (hand_summary) Production 데이터 검증
- [ ] Vertex AI Vector Search 인덱스 생성 완료
- [ ] 환경 변수 변경: `POKER_ENV=production`
- [ ] Embedding 파이프라인 실행 (125K hands)
- [ ] 검색 정확도 테스트 (Precision@10 > 0.8)

## M5 Clipping

- [ ] Pub/Sub 토픽 Production 생성
- [ ] 환경 변수 제거: `PUBSUB_EMULATOR_HOST` 삭제
- [ ] Local Agent Production 배포 (Primary + Standby)
- [ ] NAS 마운트 확인
- [ ] 클리핑 테스트 (1 hand → GCS 업로드)

## M6 Web UI

- [ ] M3, M4, M5 Production API URL 확인
- [ ] 환경 변수 변경: `NEXT_PUBLIC_POKER_ENV=production`
- [ ] API 엔드포인트 업데이트 (.env.production)
- [ ] E2E 테스트 (Playwright, 5개 시나리오)
- [ ] 인증 테스트 (IAP 통합)
```

### 5.2 전환 스크립트

```bash
# scripts/switch_to_production.sh
#!/bin/bash

echo "🚀 Switching to Production..."

# 환경 변수 업데이트
export POKER_ENV=production
unset PUBSUB_EMULATOR_HOST

# M3, M4: BigQuery 테이블 확인
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM `gg-poker.prod.hand_summary`'
# → Expected: 125,000 rows

# M5: Pub/Sub 토픽 확인
gcloud pubsub topics list --project=gg-poker --filter="name:clipping"
# → clipping-requests, clipping-complete

# M6: API 엔드포인트 확인
curl https://rag-search-service-prod.run.app/v1/health
# → {"status": "healthy"}

echo "✅ Production environment ready!"
```

---

## 6. Mock 데이터 품질 기준

### 6.1 데이터 품질 체크리스트

**BigQuery Mock**:
- [ ] 최소 1000 rows (통계적 유의성)
- [ ] NULL 값 10% 이하 (현실적 분포)
- [ ] Timestamp 범위: 2020-2024 (최근 5년)
- [ ] Player 이름: 실제 프로 20명 이상
- [ ] Pot size: $500 ~ $100,000 (현실적 범위)

**Pub/Sub Mock**:
- [ ] Emulator 안정성 (24시간 연속 실행)
- [ ] 메시지 처리 속도 <100ms
- [ ] 메시지 손실 0%

**Prism Mock**:
- [ ] OpenAPI 스펙 100% 준수
- [ ] 응답 시간 <50ms
- [ ] Example 데이터 3개 이상 (다양성)

### 6.2 Mock 데이터 Refresh 전략

```bash
# Week 3, 5: Mock 데이터 부분 업데이트 (선택)
python scripts/refresh_mock_data.py --mode partial --rows 100

# Week 6: 완전 리셋 (통합 테스트 준비)
python scripts/refresh_mock_data.py --mode full --rows 1000
```

---

## 7. 비용 분석

### 7.1 Mock 환경 비용

**BigQuery** (dev 데이터셋):
- 저장: 1000 rows × 2 tables ≈ 10 MB → $0.00 (무시 가능)
- 쿼리: 개발 중 ~1000 쿼리/week × 4 weeks ≈ $0.50

**Pub/Sub Emulator**:
- 로컬 실행 → $0.00

**Prism Mock Servers**:
- Docker 로컬 실행 → $0.00

**총 Mock 비용**: ~$0.50 (4주, 매우 저렴) ✅

### 7.2 ROI

**시간 절약**:
- Charlie, David: 2주 일찍 시작 (Week 3 vs Week 5)
- 2명 × 2주 × $100/hr × 40hr = $16,000 절약

**ROI**: $16,000 / $0.50 = **32,000배** 🎉

---

## 8. 문제 해결 가이드

### 8.1 BigQuery Mock 데이터 접근 실패

**증상**:
```
google.api_core.exceptions.NotFound: Table gg-poker:dev.hand_summary_mock not found
```

**해결**:
```bash
# 테이블 존재 확인
bq ls gg-poker:dev

# 없으면 재생성
python scripts/generate_mock_data_m3.py
```

### 8.2 Pub/Sub Emulator 연결 실패

**증상**:
```
grpc._channel._InactiveRpcError: failed to connect to all addresses
```

**해결**:
```bash
# Emulator 실행 확인
ps aux | grep pubsub-emulator

# 재시작
pkill -f pubsub-emulator
gcloud beta emulators pubsub start --host-port=localhost:8085 &

# 환경 변수 확인
echo $PUBSUB_EMULATOR_HOST
# → localhost:8085
```

### 8.3 Prism Mock 응답 불일치

**증상**:
```
Expected field 'proxy_url' but got null
```

**해결**:
```yaml
# OpenAPI 스펙에 example 추가
responses:
  '200':
    content:
      application/json:
        examples:
          success:
            value:
              hand_id: "wsop2024_me_d1_h001"
              proxy_url: "https://storage.googleapis.com/..."
              sync_score: 0.87
```

---

## 9. 참고 자료

- **Prism 공식 문서**: https://stoplight.io/open-source/prism
- **Pub/Sub Emulator**: https://cloud.google.com/pubsub/docs/emulator
- **BigQuery Mock 패턴**: `docs/mock-api-guide.md`

---

**작성자**: microservices-pm (AI Agent)
**최종 업데이트**: 2025-11-17
**승인 필요**: aiden.kim@ggproduction.net

---

**✅ Week 2 완료 기준**:
- [ ] BigQuery Mock 테이블 생성 (2개)
- [ ] Mock 데이터 1000 rows 삽입
- [ ] Pub/Sub Emulator 실행
- [ ] Prism Mock 서버 3개 실행
- [ ] 전체 팀원 로컬 환경 검증
- [ ] `.env.development` 배포

**→ Week 3부터 6명 전원 동시 개발 시작 가능** 🚀
