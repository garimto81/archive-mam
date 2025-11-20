# 서비스 계정 통합 가이드

## 옵션 1: 통합 서비스 계정 사용 (추천)

### 1. 새 통합 서비스 계정 생성

```bash
# 서비스 계정 생성
gcloud iam service-accounts create archive-mam-unified \
  --display-name="Archive MAM Unified Service Account" \
  --project=gg-poker-prod

# 서비스 계정 이메일
# archive-mam-unified@gg-poker-prod.iam.gserviceaccount.com
```

### 2. 필요한 모든 IAM 역할 부여

```bash
# Firestore 접근
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:archive-mam-unified@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# GCS 버킷 접근
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:archive-mam-unified@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# BigQuery 접근
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:archive-mam-unified@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

# Vertex AI 접근
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:archive-mam-unified@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### 3. 키 파일 생성 및 다운로드

```bash
gcloud iam service-accounts keys create backend/config/gcp-service-account.json \
  --iam-account=archive-mam-unified@gg-poker-prod.iam.gserviceaccount.com \
  --project=gg-poker-prod
```

### 4. 환경 변수 업데이트

```bash
# backend/.env.poc
GOOGLE_APPLICATION_CREDENTIALS=config/gcp-service-account.json
```

---

## 옵션 2: 기존 서비스 계정에 권한 추가

### poker-video-analyzer 서비스 계정에 권한 추가

```bash
# 현재: Firestore 접근 권한만 있음
# 추가 필요: GCS, BigQuery, Vertex AI

# GCS 버킷 접근
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# BigQuery 접근
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

# Vertex AI 접근
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### 키 파일 다운로드

```bash
# qwen_hand_analysis 프로젝트에서 복사
cp d:/AI/claude01/qwen_hand_analysis/config/gcp-service-account.json \
   backend/config/gcp-service-account.json
```

---

## 옵션 3: 서비스별 다중 키 파일 사용

### 파일 구조

```
backend/config/
├── gcp-firestore.json          # Firestore 접근용
├── gcp-storage.json             # GCS 접근용
├── gcp-bigquery.json            # BigQuery 접근용
└── gcp-vertex-ai.json           # Vertex AI 접근용
```

### 코드 수정 (각 서비스별 credentials)

```python
# backend/app/services/firestore.py
credentials = service_account.Credentials.from_service_account_file(
    "config/gcp-firestore.json"
)

# backend/app/services/vertex_search.py
credentials = service_account.Credentials.from_service_account_file(
    "config/gcp-vertex-ai.json"
)
```

**단점**: 관리 복잡도 증가, 보안 위험 증가

---

## 추천 방안

### ⭐ 옵션 2 (기존 poker-video-analyzer 사용)

**이유**:
1. qwen_hand_analysis와 동일한 서비스 계정 사용 → 일관성
2. 이미 Firestore 접근 권한 있음
3. 추가 권한만 부여하면 됨

### 실행 단계:

1. **권한 추가** (위의 명령어 실행)
2. **키 파일 확인**
   ```bash
   # qwen_hand_analysis의 키 파일이 poker-video-analyzer 계정인지 확인
   cat d:/AI/claude01/qwen_hand_analysis/config/gcp-service-account.json | grep client_email
   ```
3. **archive-mam에 복사** (이미 완료)
4. **테스트**
   ```bash
   cd backend
   python test_firestore_connection.py
   ```

---

## 검증 방법

### 1. 서비스 계정 권한 확인

```bash
# 현재 서비스 계정의 IAM 권한 확인
gcloud projects get-iam-policy gg-poker-prod \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com"
```

### 2. 각 서비스 접근 테스트

```python
# backend/test_all_services.py
from google.cloud import firestore, storage, bigquery
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    "config/gcp-service-account.json"
)

# Test Firestore
db = firestore.Client(project="gg-poker-prod", credentials=credentials)
print(f"✓ Firestore: {len(list(db.collection('hands').limit(1).stream()))} hands")

# Test GCS
storage_client = storage.Client(project="gg-poker-prod", credentials=credentials)
buckets = list(storage_client.list_buckets(max_results=1))
print(f"✓ GCS: {len(buckets)} buckets accessible")

# Test BigQuery
bq_client = bigquery.Client(project="gg-poker-prod", credentials=credentials)
datasets = list(bq_client.list_datasets(max_results=1))
print(f"✓ BigQuery: {len(datasets)} datasets accessible")
```

---

## 보안 모범 사례

1. **최소 권한 원칙**
   - 필요한 권한만 부여
   - `roles/owner`나 `roles/editor` 사용 금지

2. **키 파일 관리**
   - `.gitignore`에 `*.json` 추가 (이미 완료)
   - 프로덕션 배포 시 Secret Manager 사용

3. **키 로테이션**
   - 90일마다 키 교체 권장
   - 오래된 키 비활성화

---

## 참고 자료

- [GCP IAM Roles](https://cloud.google.com/iam/docs/understanding-roles)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)
