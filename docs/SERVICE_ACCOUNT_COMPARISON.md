# 서비스 계정 비교 및 권장사항

## 현재 상황

### 옵션 A: App Engine 기본 서비스 계정 (현재 사용 중)
- **이메일**: `gg-poker-prod@appspot.gserviceaccount.com`
- **타입**: App Engine 기본 서비스 계정
- **사용처**: qwen_hand_analysis, archive-mam (현재)

### 옵션 B: poker-video-analyzer 서비스 계정
- **이메일**: `poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com`
- **타입**: 사용자 정의 서비스 계정
- **목적**: 포커 비디오 분석 전용

---

## 비교 분석

| 항목 | App Engine 기본 SA | poker-video-analyzer SA |
|------|-------------------|------------------------|
| **보안** | ⚠️ 광범위한 권한 (Editor 수준) | ✅ 최소 권한 원칙 가능 |
| **관리** | ❌ GCP 자동 관리 (변경 불가) | ✅ 사용자가 직접 관리 |
| **권한 제어** | ❌ 세밀한 제어 어려움 | ✅ 필요한 권한만 부여 |
| **키 로테이션** | ❌ 제한적 | ✅ 자유롭게 가능 |
| **프로덕션 사용** | ⚠️ 권장하지 않음 | ✅ 권장 |
| **비용** | 무료 | 무료 |

---

## ⭐ 권장사항: poker-video-analyzer 서비스 계정 사용

### 이유:

1. **보안 모범 사례**
   - App Engine 기본 서비스 계정은 `roles/editor` 권한을 가지고 있어 과도한 권한
   - 최소 권한 원칙 위반

2. **목적 적합성**
   - `poker-video-analyzer`는 포커 비디오 관련 작업을 위해 만들어진 계정
   - archive-mam도 포커 아카이브 관리 목적이므로 용도가 일치

3. **유지보수**
   - 권한을 세밀하게 조정 가능
   - 키 교체 및 로테이션 자유

---

## 실행 단계

### 1. poker-video-analyzer 키 파일 생성

```bash
# 새 키 파일 생성
gcloud iam service-accounts keys create \
  backend/config/gcp-service-account-poker-analyzer.json \
  --iam-account=poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com \
  --project=gg-poker-prod
```

### 2. 필요한 IAM 권한 확인 및 추가

```bash
# 현재 권한 확인
gcloud projects get-iam-policy gg-poker-prod \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com"

# 필요한 권한 추가 (없으면)
# Firestore
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# GCS (읽기)
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# BigQuery (읽기)
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

# Vertex AI
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:poker-video-analyzer@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### 3. 환경 변수 업데이트

```bash
# backend/.env.poc
GOOGLE_APPLICATION_CREDENTIALS=config/gcp-service-account-poker-analyzer.json
```

### 4. 기존 키 파일 백업 및 교체

```bash
# 백업
mv backend/config/gcp-service-account.json \
   backend/config/gcp-service-account.appengine.json.bak

# 새 키 파일로 교체
mv backend/config/gcp-service-account-poker-analyzer.json \
   backend/config/gcp-service-account.json
```

### 5. 테스트

```bash
cd backend
python test_firestore_connection.py
```

---

## 검증 체크리스트

- [ ] poker-video-analyzer 키 파일 생성 완료
- [ ] Firestore 접근 테스트 성공
- [ ] GCS 버킷 접근 테스트 성공
- [ ] BigQuery 접근 테스트 성공
- [ ] Vertex AI 접근 테스트 성공
- [ ] FastAPI `/api/sync/status` 엔드포인트 작동 확인
- [ ] 기존 App Engine 키 파일 백업 완료

---

## 롤백 절차 (문제 발생 시)

```bash
# 기존 App Engine 키 파일로 복원
mv backend/config/gcp-service-account.appengine.json.bak \
   backend/config/gcp-service-account.json

# 환경 변수 원복
# backend/.env.poc
GOOGLE_APPLICATION_CREDENTIALS=config/gcp-service-account.json
```

---

## 추가 고려사항

### Q: qwen_hand_analysis도 변경해야 하나요?
**A**: 선택사항입니다. 하지만 일관성을 위해 동일하게 변경하는 것을 권장합니다.

### Q: App Engine 기본 서비스 계정을 완전히 제거해야 하나요?
**A**: 아니요. App Engine 앱을 실행 중이라면 제거하면 안 됩니다. 단지 archive-mam에서 사용하지 않는 것입니다.

### Q: poker-video-analyzer에 너무 많은 권한을 부여하면 안 되나요?
**A**: 맞습니다. 위에서 제시한 권한은 최소 권한입니다. 필요한 경우에만 추가하세요.

---

## 참고: GCP 서비스 계정 모범 사례

1. **용도별 서비스 계정 분리**
   - 프로덕션 / 개발 환경 분리
   - 서비스별 전용 계정 사용

2. **권한 최소화**
   - `roles/owner`, `roles/editor` 사용 금지
   - 필요한 최소 권한만 부여

3. **키 관리**
   - 90일마다 키 로테이션
   - Secret Manager 사용 (프로덕션)
   - 키 파일 절대 커밋 금지

4. **감사 로깅**
   - Cloud Audit Logs 활성화
   - 서비스 계정 활동 모니터링
