# M1: Data Ingestion Service

**담당**: Data Engineer (Alice)
**버전**: 1.0.0
**배포**: Cloud Run (us-central1)

---

## 개요

NSUS ATI 로우 데이터를 GCS에서 읽어 BigQuery `hand_summary` 테이블로 ETL 처리하는 서비스입니다.

### 주요 기능

- ✅ GCS JSON Lines 파일 수집
- ✅ Apache Beam/Dataflow 파이프라인
- ✅ 데이터 검증 및 변환
- ✅ BigQuery 적재
- ✅ 작업 상태 모니터링
- ✅ 에러 리포팅

---

## 아키텍처

```
GCS Bucket (gs://ati-raw-data/)
    ↓
POST /v1/ingest
    ↓
Apache Beam Pipeline (Dataflow)
    ├─ 데이터 검증
    ├─ 변환 (JSON → Row)
    └─ BigQuery 적재
    ↓
BigQuery (prod.hand_summary)
    ↓
Pub/Sub (data-ingestion-complete) ← 알림
```

---

## API 스펙

**OpenAPI 3.0**: `openapi.yaml`

### 주요 엔드포인트

#### 1. POST /v1/ingest

수집 작업 시작:

```bash
curl -X POST https://data-ingestion-service-prod.run.app/v1/ingest \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "gcs_path": "gs://ati-raw-data/2024-11-17/wsop_me_day3.jsonl",
    "event_id": "wsop2024_me",
    "tournament_day": 3
  }'
```

응답:
```json
{
  "job_id": "ingest-20241117-001",
  "status": "processing",
  "estimated_rows": 1500,
  "estimated_duration_sec": 120
}
```

#### 2. GET /v1/ingest/{job_id}/status

작업 상태 조회:

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://data-ingestion-service-prod.run.app/v1/ingest/ingest-20241117-001/status
```

응답:
```json
{
  "job_id": "ingest-20241117-001",
  "status": "completed",
  "rows_processed": 1482,
  "rows_failed": 18,
  "duration_sec": 95,
  "errors": [...]
}
```

#### 3. GET /v1/stats

전체 수집 통계:

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "https://data-ingestion-service-prod.run.app/v1/stats?period=24h"
```

---

## BigQuery 스키마

### prod.hand_summary

```sql
CREATE TABLE prod.hand_summary (
  hand_id STRING NOT NULL,
  event_id STRING,
  event_name STRING,
  timestamp_start_utc TIMESTAMP,
  timestamp_end_utc TIMESTAMP,
  searchable_summary_text STRING,  -- Gemini 생성
  embedding ARRAY<FLOAT64>,  -- M4에서 업데이트
  players ARRAY<STRING>,
  pot_size_usd NUMERIC,
  ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

**권한**:
- M1: 읽기/쓰기
- M2-M6: 읽기 전용

---

## 로컬 개발

### 1. 환경 설정

```bash
# Python 3.11 가상환경
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 샘플 데이터 준비

```bash
# 샘플 JSON Lines 파일 생성
cat > sample.jsonl << 'EOF'
{"hand_id":"test_001","event_id":"test_event","players":["Alice","Bob"],"pot_size_usd":1000}
{"hand_id":"test_002","event_id":"test_event","players":["Charlie","David"],"pot_size_usd":2500}
EOF
```

### 3. 로컬 실행 (DirectRunner)

```bash
python src/ingest_pipeline.py \
  --input sample.jsonl \
  --output test_dataset.test_table \
  --runner DirectRunner
```

### 4. 유닛 테스트

```bash
pytest tests/test_ingest_pipeline.py -v
```

---

## 배포

### Cloud Run 배포

```bash
gcloud run deploy data-ingestion-service \
  --source . \
  --region us-central1 \
  --service-account data-ingestion-sa@gg-poker.iam.gserviceaccount.com \
  --set-env-vars "BIGQUERY_DATASET=prod" \
  --allow-unauthenticated=false  # IAP 필수
```

### Dataflow 작업 모니터링

```bash
# 실행 중인 작업 목록
gcloud dataflow jobs list --region us-central1 --status active

# 특정 작업 상세
gcloud dataflow jobs describe JOB_ID --region us-central1
```

---

## 모니터링

### Cloud Logging

```bash
# 에러 로그 조회
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=data-ingestion-service \
  AND severity>=ERROR" \
  --limit 50 \
  --format json
```

### Cloud Monitoring

**주요 지표**:
- `ingestion_rows_per_sec`: 처리 속도
- `ingestion_error_rate`: 에러율
- `dataflow_job_duration`: Dataflow 작업 소요 시간

**알림 설정**:
```yaml
Alert: rows_failed > 100
  → Slack 채널 #data-engineering 알림
  → PagerDuty (Production)
```

---

## 트러블슈팅

### 1. "Permission denied" 에러

**원인**: Service Account 권한 부족

**해결**:
```bash
gcloud projects add-iam-policy-binding gg-poker \
  --member="serviceAccount:data-ingestion-sa@gg-poker.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

### 2. Dataflow 작업 실패

**원인**: Quota 초과

**해결**:
```bash
# Quota 확인
gcloud compute project-info describe --project gg-poker

# Quota 증가 요청
# https://console.cloud.google.com/iam-admin/quotas
```

### 3. "Invalid timestamp format" 에러

**원인**: ATI 데이터 포맷 변경

**해결**:
- `src/validators.py`에서 타임스탬프 파싱 로직 수정
- 재배포 후 실패한 작업 재시작

---

## 개발 체크리스트

### Phase 0: 설계
- [x] OpenAPI 스펙 작성
- [ ] BigQuery 스키마 확정
- [ ] 샘플 데이터 준비
- [ ] Mock API 서버 구축

### Phase 1: 구현
- [ ] Dataflow 파이프라인 구현
- [ ] `/v1/ingest` API 구현
- [ ] `/v1/ingest/{job_id}/status` API 구현
- [ ] `/v1/stats` API 구현
- [ ] 에러 핸들링 구현

### Phase 2: 테스트
- [ ] 유닛 테스트 작성 (pytest)
- [ ] 통합 테스트 작성
- [ ] 1,000 rows 처리 테스트
- [ ] 에러 케이스 테스트

### Phase 3: 배포
- [ ] Cloud Run 배포
- [ ] IAP 설정
- [ ] 모니터링 대시보드 생성
- [ ] 알림 설정

---

## 다음 단계

1. **BigQuery 테이블 생성**
   ```sql
   -- GCP Console 또는 bq CLI 사용
   bq mk --table prod.hand_summary schema.json
   ```

2. **Dataflow 파이프라인 구현**
   - `src/ingest_pipeline.py` 작성
   - Apache Beam 변환 로직 구현

3. **Cloud Run 서비스 구현**
   - `src/main.py` (Flask/FastAPI)
   - `/v1/ingest` 엔드포인트 구현

4. **통합 테스트**
   - 샘플 데이터로 E2E 테스트
   - M3 (Timecode Validation)과 연동 확인

---

**담당자**: aiden.kim@ggproduction.net
**최종 업데이트**: 2025-11-17
**관련 문서**:
- [아키텍처 설계](../../docs/architecture_modular.md)
- [에이전트 가이드](../../.claude/plugins/README.md)
