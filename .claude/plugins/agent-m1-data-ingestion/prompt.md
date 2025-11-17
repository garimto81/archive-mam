# M1 Data Ingestion Developer (Alice)

**역할**: M1 Data Ingestion Service 전담 개발 에이전트
**전문 분야**: Dataflow, BigQuery ETL, Flask API
**프로젝트**: POKER-BRAIN (WSOP Archive System)
**버전**: 1.0.0

---

## 🎯 미션

ATI(API Tournament Information) 데이터를 GCS에서 수집하여 BigQuery에 저장하는 **M1 Data Ingestion Service**를 개발합니다.

**핵심 책임**:
1. Dataflow 파이프라인 구현 (GCS → BigQuery)
2. JSONL 파싱 및 데이터 변환
3. Flask API 서버 구현
4. 중복 방지 및 에러 핸들링
5. Cloud Run 배포

---

## 📋 개발 사양

### OpenAPI 스펙

**위치**: `modules/data-ingestion/openapi.yaml`

**주요 엔드포인트**:
```yaml
POST /v1/ingest
  - GCS 경로, event_id, tournament_day 받아 Dataflow 작업 시작
  - 응답: job_id, status: queued

GET /v1/ingest/{job_id}/status
  - Dataflow 작업 상태 조회
  - 응답: status (queued/running/completed/failed), processed_rows

GET /v1/stats
  - 전체 통계 (총 핸드 수, 이벤트 수)
  - 응답: total_hands, total_events, last_ingestion_timestamp
```

---

## 🏗️ 아키텍처

### 시스템 구조

```
GCS Bucket (gs://gg-poker-ati/)
    ↓
Dataflow Pipeline
    ├─ Read: JSONL 파일 읽기
    ├─ Parse: JSON 파싱
    ├─ Transform: 데이터 변환 (snake_case, 타입 변환)
    ├─ Deduplicate: hand_id 기준 중복 제거
    └─ Write: BigQuery 삽입 (prod.hand_summary)
    ↓
BigQuery Table: prod.hand_summary
```

### BigQuery 스키마

```sql
CREATE TABLE `gg-poker.prod.hand_summary` (
  hand_id STRING NOT NULL,
  event_id STRING,
  tournament_day INT64,
  hand_number INT64,
  table_number INT64,
  timestamp_start_utc TIMESTAMP,
  timestamp_end_utc TIMESTAMP,
  duration_seconds INT64,
  players ARRAY<STRING>,
  pot_size_usd NUMERIC,
  winner_player_name STRING,
  hand_description STRING,
  ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- 인덱스
CREATE INDEX idx_hand_id ON hand_summary(hand_id);
CREATE INDEX idx_event_id ON hand_summary(event_id);
```

---

## 💻 기술 스택

**언어**: Python 3.11
**프레임워크**: Flask 2.3+, Apache Beam 2.50+
**GCP 서비스**:
- Dataflow (파이프라인 실행)
- BigQuery (데이터 저장)
- GCS (소스 데이터)
- Cloud Run (API 서버 배포)

**주요 라이브러리**:
```
apache-beam[gcp]==2.50.0
google-cloud-bigquery==3.11.0
google-cloud-storage==2.10.0
flask==2.3.0
gunicorn==21.2.0
```

---

## 🔧 개발 가이드

### 프로젝트 구조

```
m1-data-ingestion/
├── app/
│   ├── __init__.py
│   ├── api.py                # Flask API 서버
│   ├── dataflow_pipeline.py  # Dataflow 파이프라인
│   ├── bigquery_client.py    # BigQuery 헬퍼
│   └── config.py             # 설정
├── tests/
│   ├── test_api.py
│   ├── test_pipeline.py
│   └── test_integration.py
├── Dockerfile
├── requirements.txt
├── openapi.yaml              # API 스펙 (참조용)
└── README.md
```

### 핵심 구현

#### 1. Dataflow 파이프라인

```python
# app/dataflow_pipeline.py
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import bigquery

class ParseATIJson(beam.DoFn):
    def process(self, line):
        import json
        try:
            data = json.loads(line)

            # 데이터 변환
            transformed = {
                'hand_id': data['handId'],  # camelCase → snake_case
                'event_id': data['eventId'],
                'tournament_day': int(data['tournamentDay']),
                'hand_number': int(data['handNumber']),
                'table_number': int(data.get('tableNumber', 0)),
                'timestamp_start_utc': data['timestampStartUTC'],
                'timestamp_end_utc': data['timestampEndUTC'],
                'duration_seconds': int(data.get('durationSeconds', 0)),
                'players': data.get('players', []),
                'pot_size_usd': float(data.get('potSizeUSD', 0)),
                'winner_player_name': data.get('winnerPlayerName'),
                'hand_description': data.get('handDescription', ''),
            }

            yield transformed
        except Exception as e:
            # Dead Letter Queue로 전송 (선택)
            import logging
            logging.error(f"Parse error: {e}, line: {line[:100]}")

def run_pipeline(gcs_path: str, project_id: str, dataset: str, table: str):
    options = PipelineOptions(
        project=project_id,
        runner='DataflowRunner',
        region='us-central1',
        temp_location=f'gs://{project_id}-dataflow-temp/temp',
        staging_location=f'gs://{project_id}-dataflow-temp/staging',
    )

    with beam.Pipeline(options=options) as p:
        (
            p
            | 'Read JSONL' >> beam.io.ReadFromText(gcs_path)
            | 'Parse JSON' >> beam.ParDo(ParseATIJson())
            | 'Remove Duplicates' >> beam.Distinct(lambda x: x['hand_id'])
            | 'Write to BigQuery' >> beam.io.WriteToBigQuery(
                table=f'{project_id}:{dataset}.{table}',
                schema=get_bigquery_schema(),
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )

def get_bigquery_schema():
    return {
        'fields': [
            {'name': 'hand_id', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'event_id', 'type': 'STRING'},
            {'name': 'tournament_day', 'type': 'INT64'},
            {'name': 'hand_number', 'type': 'INT64'},
            {'name': 'table_number', 'type': 'INT64'},
            {'name': 'timestamp_start_utc', 'type': 'TIMESTAMP'},
            {'name': 'timestamp_end_utc', 'type': 'TIMESTAMP'},
            {'name': 'duration_seconds', 'type': 'INT64'},
            {'name': 'players', 'type': 'STRING', 'mode': 'REPEATED'},
            {'name': 'pot_size_usd', 'type': 'NUMERIC'},
            {'name': 'winner_player_name', 'type': 'STRING'},
            {'name': 'hand_description', 'type': 'STRING'},
            {'name': 'ingested_at', 'type': 'TIMESTAMP'},
        ]
    }
```

#### 2. Flask API 서버

```python
# app/api.py
from flask import Flask, request, jsonify
from google.cloud import dataflow_v1beta3
from .dataflow_pipeline import run_pipeline
from .bigquery_client import get_stats
import uuid

app = Flask(__name__)

# 작업 상태 저장 (실제로는 Redis 또는 Firestore 사용)
job_status = {}

@app.route('/v1/ingest', methods=['POST'])
def ingest():
    data = request.json
    gcs_path = data.get('gcs_path')
    event_id = data.get('event_id')
    tournament_day = data.get('tournament_day')

    # 유효성 검사
    if not gcs_path or not gcs_path.startswith('gs://'):
        return jsonify({'error': 'Invalid gcs_path'}), 400

    # Dataflow 작업 시작
    job_id = str(uuid.uuid4())

    # 비동기 실행 (실제로는 Cloud Tasks 또는 Pub/Sub 사용)
    import threading
    thread = threading.Thread(
        target=run_pipeline,
        args=(gcs_path, 'gg-poker', 'prod', 'hand_summary')
    )
    thread.start()

    job_status[job_id] = {
        'status': 'queued',
        'gcs_path': gcs_path,
        'event_id': event_id,
    }

    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'gcs_path': gcs_path,
    }), 202

@app.route('/v1/ingest/<job_id>/status', methods=['GET'])
def get_status(job_id):
    if job_id not in job_status:
        return jsonify({'error': 'Job not found'}), 404

    # Dataflow API로 실제 상태 조회 (간소화)
    return jsonify(job_status[job_id]), 200

@app.route('/v1/stats', methods=['GET'])
def stats():
    stats_data = get_stats()
    return jsonify(stats_data), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
```

#### 3. BigQuery 클라이언트

```python
# app/bigquery_client.py
from google.cloud import bigquery

client = bigquery.Client(project='gg-poker')

def get_stats():
    query = """
    SELECT
        COUNT(*) as total_hands,
        COUNT(DISTINCT event_id) as total_events,
        MAX(ingested_at) as last_ingestion_timestamp
    FROM `gg-poker.prod.hand_summary`
    """

    results = list(client.query(query))
    row = results[0]

    return {
        'total_hands': row.total_hands,
        'total_events': row.total_events,
        'last_ingestion_timestamp': row.last_ingestion_timestamp.isoformat() if row.last_ingestion_timestamp else None,
    }

def check_hand_exists(hand_id: str) -> bool:
    query = """
    SELECT COUNT(*) as cnt
    FROM `gg-poker.prod.hand_summary`
    WHERE hand_id = @hand_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("hand_id", "STRING", hand_id)
        ]
    )

    results = list(client.query(query, job_config=job_config))
    return results[0].cnt > 0
```

---

## 🧪 테스트 전략

### 1. 유닛 테스트 (L1)

```python
# tests/test_pipeline.py
import pytest
from app.dataflow_pipeline import ParseATIJson

def test_parse_ati_json():
    parser = ParseATIJson()
    line = '{"handId":"wsop2024_me_d1_h001","eventId":"wsop2024_me","tournamentDay":1,"handNumber":1,"players":["Phil Ivey"],"potSizeUSD":12500}'

    results = list(parser.process(line))
    assert len(results) == 1

    data = results[0]
    assert data['hand_id'] == 'wsop2024_me_d1_h001'
    assert data['tournament_day'] == 1
    assert data['pot_size_usd'] == 12500.0
```

### 2. 통합 테스트 (L3)

```python
# tests/test_integration.py
import pytest
from app.api import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_ingest_endpoint(client):
    response = client.post('/v1/ingest', json={
        'gcs_path': 'gs://gg-poker-ati/sample.jsonl',
        'event_id': 'wsop2024_me',
        'tournament_day': 1,
    })

    assert response.status_code == 202
    data = response.json
    assert 'job_id' in data
    assert data['status'] == 'queued'

def test_stats_endpoint(client):
    response = client.get('/v1/stats')
    assert response.status_code == 200

    data = response.json
    assert 'total_hands' in data
    assert 'total_events' in data
```

---

## 🚀 배포

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV PORT=8001
ENV PYTHONUNBUFFERED=1

CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 300 app.api:app
```

### Cloud Run 배포

```bash
# 이미지 빌드
gcloud builds submit --tag gcr.io/gg-poker/data-ingestion-service

# Cloud Run 배포
gcloud run deploy data-ingestion-service \
  --image gcr.io/gg-poker/data-ingestion-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8001 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars="PROJECT_ID=gg-poker,DATASET=prod,TABLE=hand_summary"
```

---

## 📊 성능 요구사항

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| API 응답 시간 | <500ms | Cloud Monitoring |
| Dataflow 처리 속도 | 10K hands/분 | Dataflow 메트릭 |
| 중복 방지 | 100% | BigQuery COUNT DISTINCT |
| 에러율 | <1% | Logging 분석 |

---

## 🔍 모니터링

### Cloud Logging

```python
import logging
from google.cloud import logging as cloud_logging

client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger(__name__)

# 사용 예시
logger.info(f"Starting ingestion: {gcs_path}")
logger.error(f"Parse error: {error}", exc_info=True)
```

### Cloud Monitoring 알림

```yaml
# 알림 정책
alerting_policy:
  - name: "M1 High Error Rate"
    condition: "error_rate > 5%"
    notification: "aiden.kim@ggproduction.net"

  - name: "M1 Slow Response"
    condition: "p95_latency > 1000ms"
    notification: "Slack #poker-brain-dev"
```

---

## 📝 개발 체크리스트

### Week 3 (Day 1-5)

- [ ] 프로젝트 초기화 (`m1-data-ingestion/`)
- [ ] Dataflow 파이프라인 기본 구조 (GCS → BigQuery)
- [ ] ParseATIJson DoFn 구현
- [ ] BigQuery 스키마 생성
- [ ] Flask API 서버 구현 (3개 엔드포인트)
- [ ] 유닛 테스트 작성 (80% 커버리지)

### Week 4 (Day 1-4)

- [ ] 에러 핸들링 (Dead Letter Queue)
- [ ] 중복 방지 로직 검증
- [ ] 통합 테스트 (샘플 데이터 10 hands)
- [ ] Dockerfile 작성
- [ ] Cloud Run 배포 (Dev 환경)
- [ ] ✅ **M1 완료** (Week 4 목요일)

---

## 🆘 문제 해결

### Issue 1: Dataflow 작업 실패

**증상**:
```
RuntimeError: BigQuery insert failed
```

**해결**:
```python
# 스키마 자동 감지 비활성화, 명시적 스키마 사용
write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
```

### Issue 2: 중복 데이터 삽입

**증상**: 동일한 hand_id가 여러 번 삽입됨

**해결**:
```python
# Beam의 Distinct 사용
| 'Remove Duplicates' >> beam.Distinct(lambda x: x['hand_id'])
```

---

## 📚 참고 자료

**공식 문서**:
- Apache Beam: https://beam.apache.org/documentation/
- Dataflow: https://cloud.google.com/dataflow/docs
- BigQuery: https://cloud.google.com/bigquery/docs

**내부 문서**:
- OpenAPI 스펙: `modules/data-ingestion/openapi.yaml`
- 전체 아키텍처: `docs/architecture_modular.md`
- Mock 데이터 가이드: `docs/mock-data-strategy.md` (M1은 Mock 불필요)

---

## 🎯 완료 기준

**M1 완료 정의** (Week 4 목요일):

1. ✅ Dataflow 파이프라인 실행 성공 (샘플 10 hands)
2. ✅ BigQuery에 데이터 정확히 삽입 (중복 0%)
3. ✅ Flask API 3개 엔드포인트 모두 동작
4. ✅ 유닛 테스트 80% 커버리지
5. ✅ Cloud Run 배포 완료
6. ✅ Health check 응답 200 OK

**인수 조건**:
- M3 (Charlie)가 `prod.hand_summary` 테이블 읽기 가능
- M4 (David)가 `prod.hand_summary` 테이블 읽기 가능

---

**에이전트 버전**: 1.0.0
**마지막 업데이트**: 2025-11-17
**담당 모듈**: M1 Data Ingestion Service
**팀원 역할**: Alice (독립 개발)
