# Cloud Functions - ATI 메타데이터 인덱싱

**버전**: v4.0.0
**런타임**: Python 3.11
**트리거**: GCS Pub/Sub (ati-metadata-prod 버킷)

---

## 개요

ATI가 GCS에 JSON 메타데이터를 저장하면 자동으로 트리거되어 BigQuery에 인덱싱하는 Cloud Function입니다.

**데이터 플로우**:
```
[ATI] → [GCS JSON 저장]
    ↓ Pub/Sub 트리거 (자동, <1초)
[Cloud Functions]
  - JSON 파싱
  - 스키마 검증
  - BigQuery 삽입
    ↓
[BigQuery poker_archive.hands]
```

---

## 파일 구조

```
cloud_functions/index_metadata/
├── main.py              # 메인 로직
├── requirements.txt     # 의존성
├── deploy.sh           # 배포 스크립트
└── README.md           # 이 파일
```

---

## 로컬 테스트

### 1. 환경 설정

```bash
# GCP 프로젝트 설정
export GCP_PROJECT=gg-poker-prod

# 인증
gcloud auth application-default login

# 가상환경 (선택)
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 테스트 데이터 준비

```bash
# 프로젝트 루트로 이동
cd ../../

# GCS에 테스트 데이터 업로드
gsutil cp mock_data/synthetic_ati/ati_metadata_001.json \
  gs://ati-metadata-prod/test/

# 또는 로컬 파일로 테스트 (Functions Framework 사용)
```

### 3. 로컬 실행 (Functions Framework)

```bash
# Cloud Functions 디렉토리에서
cd cloud_functions/index_metadata

# Functions Framework로 로컬 서버 실행
functions-framework --target=process_ati_metadata --debug

# 다른 터미널에서 테스트 요청 전송
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "bucket": "ati-metadata-prod",
      "name": "test/ati_metadata_001.json"
    }
  }'
```

### 4. Python 직접 실행

```python
# Python 인터프리터에서
from main import ATIMetadataProcessor

processor = ATIMetadataProcessor("gg-poker-prod")
success = processor.process_gcs_file(
    bucket_name="ati-metadata-prod",
    file_name="test/ati_metadata_001.json"
)

print("Success:", success)
```

---

## 배포

### 1. 사전 준비

```bash
# GCS 버킷 생성 (아직 없는 경우)
gsutil mb -p $GCP_PROJECT -c STANDARD -l us-central1 gs://ati-metadata-prod

# BigQuery 테이블 생성 (아직 없는 경우)
cd ../../
bash create_bigquery_table.sh
```

### 2. Cloud Functions 배포

```bash
cd cloud_functions/index_metadata

# 배포 스크립트 실행
bash deploy.sh

# 또는 수동 배포
gcloud functions deploy index-ati-metadata \
  --gen2 \
  --runtime python311 \
  --region us-central1 \
  --source . \
  --entry-point process_ati_metadata \
  --trigger-bucket ati-metadata-prod \
  --set-env-vars GCP_PROJECT=$GCP_PROJECT
```

### 3. 배포 확인

```bash
# 함수 정보 확인
gcloud functions describe index-ati-metadata \
  --region us-central1 \
  --gen2

# 함수 목록
gcloud functions list --gen2
```

---

## 테스트

### 1. 테스트 데이터 업로드

```bash
# 단일 파일
gsutil cp ../../mock_data/synthetic_ati/ati_metadata_001.json \
  gs://ati-metadata-prod/test/

# 전체 파일 (100개)
gsutil -m cp ../../mock_data/synthetic_ati/*.json \
  gs://ati-metadata-prod/test/
```

### 2. 로그 확인

```bash
# 최근 50개 로그
gcloud functions logs read index-ati-metadata \
  --region us-central1 \
  --gen2 \
  --limit 50

# 실시간 로그 스트리밍
gcloud functions logs tail index-ati-metadata \
  --region us-central1 \
  --gen2
```

### 3. BigQuery 데이터 확인

```bash
# 최근 삽입된 데이터
bq query --use_legacy_sql=false \
  'SELECT hand_id, hero_name, pot_bb, created_at
   FROM poker_archive.hands
   ORDER BY created_at DESC
   LIMIT 10'

# 전체 행 수
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as total_hands FROM poker_archive.hands'
```

---

## 주요 기능

### 1. 스키마 검증

```python
required_fields = [
    "hand_id", "tournament_id", "timestamp",
    "description", "hero_name", "pot_bb", "video_url"
]
```

- 필수 필드 7개 확인
- 타입 검증 (pot_bb: float, video_url: gs:// 시작)
- 검증 실패 시 로그 기록 후 스킵 (재시도 안 함)

### 2. 데이터 변환

```python
row = {
    # ATI 메타데이터 → BigQuery 타입 매핑
    "hand_id": metadata["hand_id"],
    "pot_bb": float(metadata["pot_bb"]),
    "created_date": now.date().isoformat(),  # 파티션 키
    "gcs_source_path": "gs://bucket/file.json"  # 추적용
}
```

### 3. BigQuery 삽입

- **Streaming Insert** 사용 (실시간)
- 파티셔닝: `created_date` (일별)
- 클러스터링: `tournament_id`, `hand_number`

---

## 에러 처리

### 1. 일반적인 에러

**"Missing required field"**:
```
원인: ATI JSON에 필수 필드 누락
해결: ati_metadata_schema.json 참고하여 ATI 팀에 요청
```

**"BigQuery insert errors"**:
```
원인: 스키마 불일치, 중복 hand_id
해결:
  - BigQuery 테이블 스키마 확인
  - hand_id 중복 확인 (PRIMARY KEY)
```

**"File not found"**:
```
원인: GCS 파일 삭제됨 또는 권한 없음
해결:
  - gsutil ls gs://ati-metadata-prod/file.json
  - 서비스 계정 권한 확인
```

### 2. 로그 디버깅

```bash
# 에러만 필터링
gcloud functions logs read index-ati-metadata \
  --region us-central1 \
  --gen2 \
  --filter "severity>=ERROR" \
  --limit 20

# 특정 hand_id 검색
gcloud functions logs read index-ati-metadata \
  --region us-central1 \
  --gen2 \
  --filter "jsonPayload.message=~'wsop_2024_hand_0001'" \
  --limit 10
```

---

## 성능 튜닝

### 현재 설정

- **메모리**: 512MB
- **타임아웃**: 540초 (9분)
- **최대 인스턴스**: 10개
- **동시 처리**: 파일당 1개 함수 인스턴스

### 최적화 팁

1. **대용량 배치 처리**:
   ```bash
   # 100개 파일 동시 업로드 시 자동 스케일링
   gsutil -m cp mock_data/synthetic_ati/*.json gs://ati-metadata-prod/batch/
   ```

2. **에러 재시도 방지**:
   - 스키마 에러 시 재시도 안 함 (무한 루프 방지)
   - Dead Letter Queue 설정 가능 (선택)

3. **비용 절감**:
   - 메모리 256MB로 줄이기 (단순 JSON 파싱)
   - 타임아웃 120초로 줄이기

---

## 모니터링

### Cloud Console

1. **Cloud Functions 대시보드**:
   - https://console.cloud.google.com/functions
   - 실행 횟수, 에러율, 레이턴시 확인

2. **Cloud Logging**:
   - https://console.cloud.google.com/logs
   - 필터: `resource.type="cloud_function" resource.labels.function_name="index-ati-metadata"`

3. **BigQuery 모니터링**:
   - https://console.cloud.google.com/bigquery
   - 테이블 `poker_archive.hands` 행 수, 크기 확인

### 알림 설정 (선택)

```bash
# Cloud Monitoring Alert Policy 생성
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Cloud Functions Error Alert" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05
```

---

## 다음 단계

1. **Vertex AI Embedding 추가** (Phase 1.5)
   - `main.py`의 TODO 부분 구현
   - TextEmbedding-004 모델 사용
   - Vertex AI Vector Search 인덱싱

2. **FastAPI 백엔드 개발**
   - BigQuery 쿼리 API
   - Vertex AI 검색 API

3. **통합 테스트**
   - ATI → GCS → Cloud Functions → BigQuery 전체 플로우

---

## 문제 해결

**Q: Cloud Functions가 트리거되지 않음**
```bash
# Pub/Sub 구독 확인
gcloud pubsub subscriptions list --filter="topic:ati-metadata-prod"

# 버킷 알림 설정 확인
gsutil notification list gs://ati-metadata-prod
```

**Q: BigQuery 권한 에러**
```bash
# 서비스 계정에 BigQuery Data Editor 역할 부여
gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member=serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/bigquery.dataEditor
```

**Q: 함수 삭제**
```bash
gcloud functions delete index-ati-metadata \
  --region us-central1 \
  --gen2
```

---

**관련 문서**:
- `../../bigquery_schema.json` - BigQuery 스키마
- `../../docs/bigquery-schema.md` - 스키마 상세 문서
- `../../ati_metadata_schema.json` - ATI JSON 스키마
- `../../issues/ISSUE-004-final-architecture.md` - 전체 아키텍처
