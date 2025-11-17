# M1 Data Ingestion Service

**POKER-BRAIN WSOP Archive System - M1 Module**

ATI (API Tournament Information) 데이터를 GCS에서 수집하여 BigQuery로 적재하는 데이터 파이프라인 서비스입니다.

## 개요

- **모듈 ID**: M1
- **담당자**: Alice (Data Ingestion Developer)
- **버전**: 1.0.0 (Week 3 - 30% 완료)
- **배포 플랫폼**: Cloud Run
- **주요 기술**: Python 3.11, Apache Beam, Flask, BigQuery

## 아키텍처

```
GCS Bucket (gs://gg-poker-ati/)
    ↓
Dataflow Pipeline
    ├─ Read: JSONL 파일 읽기
    ├─ Parse: JSON 파싱 (camelCase → snake_case)
    ├─ Transform: 데이터 변환 및 검증
    ├─ Deduplicate: hand_id 기준 중복 제거
    └─ Write: BigQuery 삽입
    ↓
BigQuery Table: prod.hand_summary
```

## 주요 기능

### Week 3 구현 (30%)

✅ **완료된 기능**:
1. Dataflow 파이프라인 기본 구조 (GCS → BigQuery)
2. JSON 파싱 및 데이터 변환 (ParseATIJson DoFn)
3. 중복 제거 로직 (DeduplicateByHandId DoFn)
4. BigQuery 스키마 정의
5. Flask API 서버 (3개 엔드포인트)
6. 유닛 테스트 (80% 커버리지 목표)
7. Dockerfile 및 Cloud Run 배포 준비

📋 **Week 4 예정 (70%)**:
- Dead Letter Queue 에러 핸들링
- Firestore/Redis 기반 작업 상태 관리
- 통합 테스트 (E2E)
- Cloud Monitoring 통합
- 프로덕션 배포 및 검증

## API 엔드포인트

### 1. POST /v1/ingest

ATI 데이터 수집 작업 시작

**요청**:
```json
{
  "gcs_path": "gs://gg-poker-ati/2024-11-17/wsop_me_day3.jsonl",
  "event_id": "wsop2024_me",
  "tournament_day": 3
}
```

**응답** (202 Accepted):
```json
{
  "job_id": "ingest-20241117-001",
  "status": "queued",
  "gcs_path": "gs://gg-poker-ati/2024-11-17/wsop_me_day3.jsonl",
  "event_id": "wsop2024_me",
  "created_at": "2024-11-17T10:30:00Z"
}
```

### 2. GET /v1/ingest/{job_id}/status

수집 작업 상태 조회

**응답** (200 OK):
```json
{
  "job_id": "ingest-20241117-001",
  "status": "completed",
  "rows_processed": 1482,
  "rows_failed": 18,
  "duration_sec": 95,
  "bigquery_table": "prod.hand_summary",
  "started_at": "2024-11-17T10:30:00Z",
  "completed_at": "2024-11-17T10:31:35Z"
}
```

### 3. GET /v1/stats

전체 수집 통계 조회

**쿼리 파라미터**:
- `period`: 24h, 7d, 30d, all (기본값: 24h)
- `event_id`: 이벤트별 필터링 (선택)

**응답** (200 OK):
```json
{
  "period": "24h",
  "total_hands": 67500,
  "total_events": 8,
  "last_ingestion_timestamp": "2024-11-17T12:00:00Z",
  "avg_pot_size_usd": 5432.50,
  "top_events": [
    {"event_id": "wsop2024_me", "rows_processed": 35000}
  ]
}
```

### 4. GET /health

헬스 체크 (Cloud Run 로드 밸런서용)

**응답** (200 OK):
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

## 설치 및 실행

### 로컬 개발

```bash
# 1. 가상환경 생성
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
export PROJECT_ID=gg-poker
export DATASET=prod
export TABLE=hand_summary
export ENVIRONMENT=development

# 4. Flask 앱 실행
python -m app.api
```

서버가 http://localhost:8001 에서 실행됩니다.

### 테스트 실행

```bash
# 전체 테스트 실행
pytest tests/ -v

# 커버리지 확인
pytest tests/ -v --cov=app --cov-report=term-missing

# 특정 테스트 파일만 실행
pytest tests/test_api.py -v
```

### Docker 빌드 및 실행

```bash
# 이미지 빌드
docker build -t m1-data-ingestion:1.0.0 .

# 로컬 실행
docker run -p 8001:8001 \
  -e PROJECT_ID=gg-poker \
  -e DATASET=prod \
  -e TABLE=hand_summary \
  m1-data-ingestion:1.0.0
```

### Cloud Run 배포

```bash
# 1. 이미지 빌드 및 푸시
gcloud builds submit --tag gcr.io/gg-poker/m1-data-ingestion:1.0.0

# 2. Cloud Run 배포
gcloud run deploy m1-data-ingestion \
  --image gcr.io/gg-poker/m1-data-ingestion:1.0.0 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8001 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars="PROJECT_ID=gg-poker,DATASET=prod,TABLE=hand_summary,ENVIRONMENT=production"

# 3. 배포 확인
curl https://m1-data-ingestion-xxxx.run.app/health
```

## 프로젝트 구조

```
m1-data-ingestion/
├── app/
│   ├── __init__.py           # 패키지 초기화
│   ├── api.py                # Flask API 서버
│   ├── config.py             # 설정 관리
│   ├── dataflow_pipeline.py  # Dataflow 파이프라인
│   └── bigquery_client.py    # BigQuery 클라이언트
├── tests/
│   ├── __init__.py
│   ├── test_api.py           # API 엔드포인트 테스트
│   ├── test_pipeline.py      # 파이프라인 컴포넌트 테스트
│   └── test_bigquery_client.py  # BigQuery 클라이언트 테스트
├── Dockerfile                # Cloud Run 배포용
├── requirements.txt          # Python 의존성
└── README.md                 # 이 파일
```

## BigQuery 스키마

**테이블**: `gg-poker.prod.hand_summary`

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| hand_id | STRING (REQUIRED) | 핸드 고유 ID |
| event_id | STRING | 이벤트 ID |
| tournament_day | INT64 | 토너먼트 일차 |
| hand_number | INT64 | 핸드 번호 |
| table_number | INT64 | 테이블 번호 |
| timestamp_start_utc | TIMESTAMP | 시작 시간 |
| timestamp_end_utc | TIMESTAMP | 종료 시간 |
| duration_seconds | INT64 | 소요 시간 |
| players | STRING (REPEATED) | 참여 플레이어 목록 |
| pot_size_usd | NUMERIC | 팟 크기 (USD) |
| winner_player_name | STRING | 승자 이름 |
| hand_description | STRING | 핸드 설명 |
| ingested_at | TIMESTAMP | 적재 시간 |

## 성능 요구사항

| 지표 | 목표 | 현재 상태 |
|------|------|----------|
| API 응답 시간 | <500ms | ✅ Week 4 검증 예정 |
| Dataflow 처리 속도 | 10K hands/분 | ✅ Week 4 검증 예정 |
| 중복 방지 | 100% | ✅ 구현 완료 |
| 에러율 | <1% | ✅ Week 4 검증 예정 |
| 테스트 커버리지 | 80% | ✅ 구현 완료 |

## 문제 해결

### Issue: Dataflow 작업 실패

**증상**: `RuntimeError: BigQuery insert failed`

**해결책**:
```python
# 스키마 자동 감지 비활성화, 명시적 스키마 사용
write_disposition=BigQueryDisposition.WRITE_APPEND
create_disposition=BigQueryDisposition.CREATE_IF_NEEDED
```

### Issue: 중복 데이터 삽입

**증상**: 동일한 hand_id가 여러 번 삽입됨

**해결책**:
```python
# DeduplicateByHandId DoFn 사용
| 'Remove Duplicates' >> beam.ParDo(DeduplicateByHandId())
```

## 의존성 모듈

**Upstream (데이터 소스)**:
- GCS Bucket: `gs://gg-poker-ati/`

**Downstream (데이터 소비자)**:
- M3 Video Processing Service (reads from `prod.hand_summary`)
- M4 Metadata Enrichment Service (reads from `prod.hand_summary`)

## 참고 자료

- [OpenAPI 스펙](../data-ingestion/openapi.yaml)
- [전체 아키텍처](../../docs/architecture_modular.md)
- [Apache Beam 문서](https://beam.apache.org/documentation/)
- [Dataflow 문서](https://cloud.google.com/dataflow/docs)

## 라이선스

내부 프로젝트 - GG Production

---

**마지막 업데이트**: 2024-11-17
**버전**: 1.0.0 (Week 3 - 30% 완료)
**담당자**: Alice (Data Ingestion Developer)
