# 서비스 계정 키 통합 - 빠른 해결 가이드

## TL;DR

**현재 문제**:
- 현재 사용 중: `gg-poker-prod@appspot.gserviceaccount.com` (App Engine 기본, 과도한 권한)
- 권장 사용: `poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com` (전용 계정)

**해결 방법**: poker-video-analyzer 서비스 계정으로 전환 (5분 소요)

---

## 실행 명령어 (복사해서 실행)

### 1단계: 현재 권한 확인
```bash
gcloud projects get-iam-policy gg-poker-prod \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

### 2단계: 필요한 권한 추가 (한 번만 실행)
```bash
# Firestore 접근
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# GCS 읽기
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# BigQuery 읽기
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

# Vertex AI
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### 3단계: 새 키 파일 생성
```bash
cd d:/AI/claude01/archive-mam

gcloud iam service-accounts keys create \
  backend/config/gcp-service-account-new.json \
  --iam-account=poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com \
  --project=gg-poker-prod
```

### 4단계: 기존 키 백업 및 교체
```bash
# 백업
mv backend/config/gcp-service-account.json \
   backend/config/gcp-service-account.appengine.bak

# 새 키로 교체
mv backend/config/gcp-service-account-new.json \
   backend/config/gcp-service-account.json
```

### 5단계: 테스트
```bash
cd backend
./venv/Scripts/python test_firestore_connection.py
```

**예상 결과**:
```
Connecting to Firestore in project: gg-poker-prod
Credentials: D:\AI\claude01\archive-mam\backend\config\gcp-service-account.json

Available collections:
   ['hands', 'videos']

Querying 'hands' collection...
SUCCESS: Found 5 hands (showing first 5):
   ...
```

---

## 검증 명령어

### 사용 중인 서비스 계정 확인
```bash
cat backend/config/gcp-service-account.json | grep client_email
```

**예상 출력**:
```
"client_email": "poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com",
```

### 권한 확인
```bash
gcloud projects get-iam-policy gg-poker-prod \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

**예상 출력**:
```
ROLE
roles/aiplatform.user
roles/bigquery.dataViewer
roles/datastore.user
roles/storage.objectViewer
```

---

## 롤백 (문제 발생 시)

```bash
# 기존 키로 복원
mv backend/config/gcp-service-account.appengine.bak \
   backend/config/gcp-service-account.json
```

---

## 다음 단계

1. ✅ 키 파일 교체 완료
2. ✅ Firestore 연결 테스트 성공
3. 🔄 FastAPI 서버 재시작
4. 🔄 `/api/sync/status` 엔드포인트 테스트

---

## 추가 참고자료

- 상세 가이드: `docs/SERVICE_ACCOUNT_SETUP.md`
- 서비스 계정 비교: `docs/SERVICE_ACCOUNT_COMPARISON.md`
