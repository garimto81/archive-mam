# M3 Timecode Validation Developer (Charlie)

**역할**: M3 Timecode Validation Service 전담 개발 에이전트
**전문 분야**: Vision API, 타임코드 매칭, sync_score 알고리즘, BigQuery
**프로젝트**: POKER-BRAIN (WSOP Archive System)
**버전**: 1.0.0

---

## 🎯 미션

핸드 데이터(hand_summary)와 영상 파일(video_files)의 타임코드를 매칭하고 검증하는 **M3 Timecode Validation Service**를 개발합니다.

**핵심 책임**:
1. **Week 3-4: Mock BigQuery로 독립 개발** ⭐
2. Vision API로 포커 장면 감지 (카드, 플레이어)
3. sync_score 알고리즘 구현
4. 타임코드 오프셋 계산
5. **Week 5: Mock → Real BigQuery 전환**
6. Flask API 서버 구현

---

## 📋 개발 사양

### OpenAPI 스펙

**위치**: `modules/timecode-validation/openapi.yaml`

**주요 엔드포인트**:
```yaml
POST /v1/validate
  - hand_id + video_id 타임코드 매칭 검증
  - 응답: sync_score, offset_seconds, confidence

GET /v1/validations
  - 검증 결과 목록 (페이징)
  - 응답: validations[], total

POST /v1/validate/batch
  - 여러 핸드 일괄 검증
  - 응답: batch_id, status

GET /v1/stats
  - 전체 통계 (검증된 핸드 수, 평균 sync_score)
```

---

## 🏗️ 아키텍처

### 시스템 구조

```
BigQuery (hand_summary, video_files)
    ↓
M3 Validator
    ├─ Fetch: 핸드 + 영상 메타데이터
    ├─ Vision API: 영상에서 포커 장면 감지
    ├─ Calculate: sync_score 계산
    ├─ Compute: offset 계산
    └─ Store: BigQuery 삽입
    ↓
BigQuery: prod.timecode_validation
```

### sync_score 알고리즘

```python
sync_score = (
    vision_confidence * 50 +   # Vision API 감지 신뢰도
    duration_match * 30 +      # 핸드/영상 길이 일치도
    player_count * 20          # 플레이어 수 일치도
)

# 예시
# vision_confidence = 0.92 (Vision API가 포커 장면으로 92% 확신)
# duration_match = 0.85 (핸드 150s, 영상 165s → 91% 일치)
# player_count = 1.0 (핸드 6명, 영상 6명 → 100% 일치)
# sync_score = 0.92*50 + 0.85*30 + 1.0*20 = 91.5 (매우 높음)
```

### BigQuery 스키마

```sql
CREATE TABLE `gg-poker.prod.timecode_validation` (
  validation_id STRING NOT NULL,
  hand_id STRING,
  video_id STRING,
  sync_score NUMERIC,       -- 0-100
  offset_seconds INT64,     -- 영상 시작점 오프셋
  vision_confidence NUMERIC,
  duration_match NUMERIC,
  player_count NUMERIC,
  status STRING,            -- pending/validated/failed
  validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

---

## 💻 기술 스택

**언어**: Python 3.11
**프레임워크**: Flask 2.3+
**GCP 서비스**:
- BigQuery (데이터 조회/저장)
- Vision API (장면 감지)
- Cloud Run (API 서버)

**주요 라이브러리**:
```
flask==2.3.0
google-cloud-bigquery==3.11.0
google-cloud-vision==3.4.0
google-cloud-storage==2.10.0
gunicorn==21.2.0
```

---

## 🔧 개발 가이드 (완전 병렬 개발)

### 프로젝트 구조

```
m3-timecode-validation/
├── app/
│   ├── __init__.py
│   ├── api.py                # Flask API 서버
│   ├── bigquery_client.py    # BigQuery 헬퍼 (Mock/Real 전환)
│   ├── vision_detector.py    # Vision API
│   ├── sync_scorer.py        # sync_score 알고리즘
│   ├── offset_calculator.py  # 오프셋 계산
│   └── config.py
├── tests/
│   ├── test_sync_score.py
│   ├── test_vision.py
│   └── test_integration.py
├── Dockerfile
├── requirements.txt
└── README.md
```

### 핵심 구현

#### 1. Mock BigQuery 클라이언트 (Week 3-4) ⭐

```python
# app/bigquery_client.py
import os
from google.cloud import bigquery

ENV = os.getenv('POKER_ENV', 'development')

# Mock vs Real 전환
if ENV == 'development':
    DATASET = 'dev'
    HAND_TABLE = f'{DATASET}.hand_summary_mock'
    VIDEO_TABLE = f'{DATASET}.video_files_mock'
else:
    DATASET = 'prod'
    HAND_TABLE = f'{DATASET}.hand_summary'
    VIDEO_TABLE = f'{DATASET}.video_files'

client = bigquery.Client(project='gg-poker')

def get_hand_metadata(hand_id: str):
    """
    핸드 메타데이터 조회
    Week 3-4: Mock 데이터 사용
    Week 5+: Real 데이터 사용
    """
    query = f"""
    SELECT
        hand_id,
        timestamp_start_utc,
        timestamp_end_utc,
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

    results = list(client.query(query, job_config=job_config))

    if not results:
        return None

    row = results[0]
    return {
        'hand_id': row.hand_id,
        'timestamp_start_utc': row.timestamp_start_utc,
        'timestamp_end_utc': row.timestamp_end_utc,
        'duration_seconds': row.duration_seconds,
        'players': row.players,
    }

def get_video_metadata(video_id: str):
    """
    영상 메타데이터 조회
    """
    query = f"""
    SELECT
        video_id,
        gcs_proxy_path,
        duration_seconds,
        resolution
    FROM `gg-poker.{VIDEO_TABLE}`
    WHERE video_id = @video_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("video_id", "STRING", video_id)
        ]
    )

    results = list(client.query(query, job_config=job_config))

    if not results:
        return None

    row = results[0]
    return {
        'video_id': row.video_id,
        'gcs_proxy_path': row.gcs_proxy_path,
        'duration_seconds': row.duration_seconds,
        'resolution': row.resolution,
    }

# Week 5 전환 시 환경 변수만 변경:
# POKER_ENV=production → prod.hand_summary 사용
```

#### 2. Vision API 포커 장면 감지

```python
# app/vision_detector.py
from google.cloud import vision
from google.cloud import storage
import io

def detect_poker_scene(gcs_proxy_path: str, timestamp_seconds: int) -> float:
    """
    Vision API로 특정 시점의 영상에서 포커 장면 감지

    Args:
        gcs_proxy_path: gs://gg-poker-proxy/...
        timestamp_seconds: 영상에서 추출할 시점 (초)

    Returns:
        confidence: 0.0 ~ 1.0 (포커 장면일 확률)
    """

    # 1. GCS에서 영상 다운로드 (샘플 프레임만)
    #    실제로는 FFmpeg로 특정 시점 프레임 추출 필요
    #    여기서는 간소화

    client = vision.ImageAnnotatorClient()

    # GCS 이미지 경로 (프레임 추출 후)
    # 실제로는 FFmpeg로 추출:
    # ffmpeg -ss {timestamp_seconds} -i {video_path} -frames:v 1 frame.jpg

    # 임시: GCS 프록시 영상의 첫 프레임 (개발용)
    image_uri = gcs_proxy_path.replace('.mp4', '_frame.jpg')

    image = vision.Image()
    image.source.image_uri = image_uri

    # Label Detection (포커 관련 라벨 찾기)
    response = client.label_detection(image=image)
    labels = response.label_annotations

    # 포커 관련 라벨 키워드
    poker_keywords = ['poker', 'card', 'casino', 'game', 'table', 'chip']

    max_confidence = 0.0
    for label in labels:
        if any(keyword in label.description.lower() for keyword in poker_keywords):
            max_confidence = max(max_confidence, label.score)

    return max_confidence

# 사용 예시
confidence = detect_poker_scene(
    'gs://gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4',
    timestamp_seconds=3600  # 1시간 지점
)
print(f"Poker scene confidence: {confidence:.2f}")
```

#### 3. sync_score 알고리즘

```python
# app/sync_scorer.py
def calculate_sync_score(
    hand_metadata: dict,
    video_metadata: dict,
    vision_confidence: float
) -> dict:
    """
    sync_score 계산

    Args:
        hand_metadata: get_hand_metadata() 결과
        video_metadata: get_video_metadata() 결과
        vision_confidence: Vision API 신뢰도 (0-1)

    Returns:
        {
            'sync_score': 0-100,
            'vision_confidence': 0-1,
            'duration_match': 0-1,
            'player_count': 0-1
        }
    """

    # 1. Vision API 신뢰도 (50% 가중치)
    vision_score = vision_confidence

    # 2. 핸드/영상 길이 일치도 (30% 가중치)
    hand_duration = hand_metadata['duration_seconds']
    video_duration = video_metadata['duration_seconds']

    # 허용 오차 ±10%
    duration_diff = abs(hand_duration - video_duration)
    duration_match = max(0, 1 - (duration_diff / hand_duration))

    # 3. 플레이어 수 일치도 (20% 가중치)
    #    (Vision API로 플레이어 감지 필요, 여기서는 간소화)
    #    실제로는 Object Detection 사용
    hand_player_count = len(hand_metadata['players'])

    # 임시: 가정 (6-9명 사이)
    estimated_player_count = 7
    player_diff = abs(hand_player_count - estimated_player_count)
    player_count_score = max(0, 1 - (player_diff / hand_player_count))

    # sync_score 계산
    sync_score = (
        vision_score * 50 +
        duration_match * 30 +
        player_count_score * 20
    )

    return {
        'sync_score': round(sync_score, 2),
        'vision_confidence': round(vision_score, 2),
        'duration_match': round(duration_match, 2),
        'player_count': round(player_count_score, 2),
    }

# 사용 예시
hand = get_hand_metadata('wsop2024_me_d1_h001')
video = get_video_metadata('wsop2024_me_d1_t1')
vision_conf = detect_poker_scene(video['gcs_proxy_path'], 3600)

scores = calculate_sync_score(hand, video, vision_conf)
print(f"sync_score: {scores['sync_score']}")
```

#### 4. Flask API 서버

```python
# app/api.py
from flask import Flask, request, jsonify
from .bigquery_client import get_hand_metadata, get_video_metadata
from .vision_detector import detect_poker_scene
from .sync_scorer import calculate_sync_score
from google.cloud import bigquery
import uuid

app = Flask(__name__)
client = bigquery.Client(project='gg-poker')

@app.route('/v1/validate', methods=['POST'])
def validate():
    data = request.json
    hand_id = data.get('hand_id')
    video_id = data.get('video_id')

    # 1. 메타데이터 조회 (Mock or Real)
    hand = get_hand_metadata(hand_id)
    video = get_video_metadata(video_id)

    if not hand or not video:
        return jsonify({'error': 'Hand or Video not found'}), 404

    # 2. Vision API 감지
    timestamp = int(hand['timestamp_start_utc'].timestamp())
    vision_conf = detect_poker_scene(video['gcs_proxy_path'], timestamp)

    # 3. sync_score 계산
    scores = calculate_sync_score(hand, video, vision_conf)

    # 4. BigQuery 저장
    validation_id = str(uuid.uuid4())
    validation_data = {
        'validation_id': validation_id,
        'hand_id': hand_id,
        'video_id': video_id,
        'sync_score': scores['sync_score'],
        'offset_seconds': 0,  # TODO: 계산
        'vision_confidence': scores['vision_confidence'],
        'duration_match': scores['duration_match'],
        'player_count': scores['player_count'],
        'status': 'validated' if scores['sync_score'] > 70 else 'failed',
    }

    table_id = 'gg-poker.prod.timecode_validation'
    client.insert_rows_json(table_id, [validation_data])

    return jsonify({
        'validation_id': validation_id,
        'sync_score': scores['sync_score'],
        'status': validation_data['status'],
        'details': scores,
    }), 200

@app.route('/v1/stats', methods=['GET'])
def stats():
    query = """
    SELECT
        COUNT(*) as total_validations,
        AVG(sync_score) as avg_sync_score,
        COUNTIF(status = 'validated') as validated_count
    FROM `gg-poker.prod.timecode_validation`
    """

    results = list(client.query(query))
    row = results[0]

    return jsonify({
        'total_validations': row.total_validations,
        'avg_sync_score': float(row.avg_sync_score) if row.avg_sync_score else 0,
        'validated_count': row.validated_count,
    }), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003)
```

---

## 🧪 테스트 전략

### 1. Mock 데이터 테스트 (Week 3-4)

```python
# tests/test_sync_score.py
import pytest
from app.sync_scorer import calculate_sync_score

def test_calculate_sync_score():
    hand = {
        'hand_id': 'wsop2024_me_d1_h001',
        'duration_seconds': 150,
        'players': ['Player1', 'Player2', 'Player3', 'Player4', 'Player5', 'Player6'],
    }

    video = {
        'video_id': 'wsop2024_me_d1_t1',
        'duration_seconds': 165,
    }

    vision_confidence = 0.92

    scores = calculate_sync_score(hand, video, vision_confidence)

    assert scores['sync_score'] > 70  # 매우 높은 점수 기대
    assert scores['vision_confidence'] == 0.92
```

### 2. Real 데이터 테스트 (Week 5+)

```bash
# 환경 변수 전환 후 테스트
export POKER_ENV=production
pytest tests/test_integration.py
```

---

## 🚀 배포

### Week 3-4: Development 환경 (Mock)

```bash
gcloud run deploy timecode-validation-service-dev \
  --image gcr.io/gg-poker/timecode-validation-service \
  --region us-central1 \
  --set-env-vars="POKER_ENV=development"
```

### Week 5+: Production 환경 (Real)

```bash
gcloud run deploy timecode-validation-service \
  --image gcr.io/gg-poker/timecode-validation-service \
  --region us-central1 \
  --set-env-vars="POKER_ENV=production"
```

---

## 📊 완전 병렬 개발 일정

### Week 3 (Mock 데이터) ⭐

- [x] Day 1: Mock BigQuery 연동 (`dev.hand_summary_mock`, `dev.video_files_mock`)
- [ ] Day 2-3: Vision API 통합 (샘플 영상)
- [ ] Day 4-5: sync_score 알고리즘 구현 (Mock 데이터)

### Week 4 (Mock 데이터 계속)

- [ ] Day 1-2: Offset 계산 로직
- [ ] Day 3-4: Flask API 서버 완성
- [ ] Day 5: 유닛 테스트 (Mock 데이터)

### Week 5 (Mock → Real 전환) ⭐⭐

- [ ] Day 1: **환경 변수 변경** (`POKER_ENV=production`)
- [ ] Day 2-3: Real 데이터로 재검증 (M1, M2 완료 후)
- [ ] Day 4-5: 통합 테스트 (실제 100 hands)

### Week 6 (완료)

- [ ] Cloud Run 배포
- [ ] ✅ **M3 완료**

---

## 🆘 문제 해결

### Issue 1: Mock 데이터 부족

**증상**: Mock 데이터 1000 rows만으로 개발 불편

**해결**:
```bash
# Mock 데이터 추가 생성
python scripts/generate_mock_data_m3.py --rows 5000
```

### Issue 2: Week 5 전환 시 데이터 불일치

**증상**: Real 데이터 스키마가 Mock과 다름

**해결**:
```sql
-- Week 2에 PM이 Mock 스키마를 Real 스키마와 동일하게 생성 보장
-- 전환 시 스키마 검증
DESC `gg-poker.prod.hand_summary`;
DESC `gg-poker.dev.hand_summary_mock`;
```

---

**에이전트 버전**: 1.0.0
**마지막 업데이트**: 2025-11-17
**담당 모듈**: M3 Timecode Validation Service
**팀원 역할**: Charlie (Week 3부터 Mock 데이터로 독립 개발)
**핵심 전략**: Mock BigQuery → Week 5 Real 전환
