---
name: Google Cloud Platform Setup
about: Production 배포를 위한 GCP 환경 설정
title: '[Setup] GCP Production Environment Configuration'
labels: infrastructure, setup, phase-0
assignees: ''
---

## 📋 Overview

POKER-BRAIN WSOP Archive System의 Production 배포를 위한 Google Cloud Platform 초기 설정 작업입니다.

**Related**: PRODUCTION_ROADMAP.md Phase 0
**Milestone**: v2.0.0 Production Launch
**Estimated Time**: 1 week
**Priority**: High

---

## 🎯 Objectives

- [ ] GCP 프로젝트 생성 및 기본 설정
- [ ] 필요한 API 15개 활성화
- [ ] 서비스 계정 및 IAM 권한 설정
- [ ] BigQuery 데이터셋 및 테이블 생성
- [ ] GCS 버킷 생성 (source, proxies, clips)
- [ ] 예산 및 알림 설정
- [ ] 샘플 데이터 업로드

---

## 📝 Detailed Tasks

### 1. GCP 프로젝트 생성 (Day 1)

**Commands**:
```bash
# 프로젝트 생성
gcloud projects create gg-poker-prod --name="POKER-BRAIN Production"

# Billing 연결
gcloud beta billing projects link gg-poker-prod \
  --billing-account=XXXXXX-YYYYYY-ZZZZZZ

# 기본 프로젝트 설정
gcloud config set project gg-poker-prod
```

**Verification**:
```bash
gcloud projects describe gg-poker-prod
```

---

### 2. API 활성화 (Day 1)

**Required APIs** (15개):
```bash
gcloud services enable \
  run.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  dataflow.googleapis.com \
  vision.googleapis.com \
  aiplatform.googleapis.com \
  pubsub.googleapis.com \
  compute.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  secretmanager.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --project=gg-poker-prod
```

**Verification**:
```bash
gcloud services list --enabled --project=gg-poker-prod
```

---

### 3. 서비스 계정 생성 (Day 2)

**M1-M5 서비스 계정**:
```bash
# M1 Dataflow
gcloud iam service-accounts create m1-dataflow-sa \
  --display-name="M1 Dataflow Service Account" \
  --project=gg-poker-prod

# M2 Video Metadata
gcloud iam service-accounts create m2-video-metadata-sa \
  --display-name="M2 Video Metadata Service Account" \
  --project=gg-poker-prod

# M3 Timecode Validation
gcloud iam service-accounts create m3-timecode-validation-sa \
  --display-name="M3 Timecode Validation Service Account" \
  --project=gg-poker-prod

# M4 RAG Search
gcloud iam service-accounts create m4-rag-search-sa \
  --display-name="M4 RAG Search Service Account" \
  --project=gg-poker-prod

# M5 Clipping
gcloud iam service-accounts create m5-clipping-sa \
  --display-name="M5 Clipping Service Account" \
  --project=gg-poker-prod
```

**IAM 권한 부여**:
```bash
# M1: BigQuery + GCS
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m1-dataflow-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m1-dataflow-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# M2: GCS + BigQuery
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m2-video-metadata-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# M3: Vision API + BigQuery
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m3-timecode-validation-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/visionai.user"

# M4: Vertex AI + BigQuery
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m4-rag-search-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# M5: Pub/Sub + GCS
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m5-clipping-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/pubsub.editor"
```

---

### 4. BigQuery 설정 (Day 3)

**데이터셋 생성**:
```bash
bq mk -d \
  --project_id=gg-poker-prod \
  --location=us-central1 \
  --description="POKER-BRAIN Production Dataset" \
  prod
```

**테이블 생성**:
```bash
# M1: hand_summary
bq mk -t gg-poker-prod:prod.hand_summary \
  hand_id:STRING,event_id:STRING,tournament_id:STRING,table_id:STRING,\
  hand_number:INTEGER,timestamp:TIMESTAMP,summary_text:STRING,\
  player_names:STRING,pot_size_usd:FLOAT,created_at:TIMESTAMP

# M2: video_files
bq mk -t gg-poker-prod:prod.video_files \
  file_id:STRING,video_path:STRING,proxy_path:STRING,duration_seconds:FLOAT,\
  resolution:STRING,codec:STRING,file_size_bytes:INTEGER,created_at:TIMESTAMP

# M3: timecode_validation
bq mk -t gg-poker-prod:prod.timecode_validation \
  validation_id:STRING,hand_id:STRING,video_path:STRING,sync_score:FLOAT,\
  vision_confidence:FLOAT,suggested_offset:INTEGER,status:STRING,created_at:TIMESTAMP

# M4: hand_embeddings
bq mk -t gg-poker-prod:prod.hand_embeddings \
  hand_id:STRING,summary_text:STRING,embedding:ARRAY<FLOAT64>,created_at:TIMESTAMP

# M5: clipping_requests
bq mk -t gg-poker-prod:prod.clipping_requests \
  request_id:STRING,hand_id:STRING,status:STRING,output_gcs_path:STRING,\
  download_url:STRING,created_at:TIMESTAMP,completed_at:TIMESTAMP
```

**Verification**:
```bash
bq ls -d gg-poker-prod
bq ls gg-poker-prod:prod
```

---

### 5. GCS 버킷 생성 (Day 4)

```bash
# Source 데이터 버킷
gsutil mb -p gg-poker-prod -c STANDARD -l us-central1 gs://gg-poker-source

# Proxy 비디오 버킷
gsutil mb -p gg-poker-prod -c STANDARD -l us-central1 gs://gg-poker-proxies

# Clipping 출력 버킷
gsutil mb -p gg-poker-prod -c STANDARD -l us-central1 gs://gg-subclips

# Lifecycle 정책 (clips 30일 후 삭제)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://gg-subclips
```

**Verification**:
```bash
gsutil ls -p gg-poker-prod
```

---

### 6. 예산 및 알림 설정 (Day 5)

```bash
# $200 월간 예산 설정
gcloud billing budgets create \
  --billing-account=XXXXXX-YYYYYY-ZZZZZZ \
  --display-name="POKER-BRAIN Monthly Budget" \
  --budget-amount=200USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

**Notification Email**: aiden.kim@ggproduction.net

---

### 7. 샘플 데이터 업로드 (Day 6-7)

```bash
# 실제 핸드 데이터 업로드 (22 hands)
bq load --source_format=NEWLINE_DELIMITED_JSON \
  gg-poker-prod:prod.hand_summary \
  mock_data/bigquery/hand_summary_real.json

# 검증
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as total_hands FROM `gg-poker-prod.prod.hand_summary`'

# 예상: 23 hands
```

---

## 💰 Cost Estimation

**Initial Setup**: $0 (free tier)
**Monthly Cost** (after deployment):
- Development/Testing: ~$140/month
- Production (100 users): ~$435/month

See `PRODUCTION_ROADMAP.md` for detailed breakdown.

---

## ✅ Acceptance Criteria

- [ ] GCP 프로젝트 `gg-poker-prod` 생성됨
- [ ] 15개 API 모두 활성화됨
- [ ] 5개 서비스 계정 생성 및 권한 부여됨
- [ ] BigQuery 데이터셋 `prod` 및 5개 테이블 생성됨
- [ ] 3개 GCS 버킷 생성됨
- [ ] 예산 알림 설정됨 (50%, 90%, 100%)
- [ ] 샘플 데이터 23개 핸드 업로드됨
- [ ] 모든 리소스 상태 정상 확인됨

---

## 📚 References

- `PRODUCTION_ROADMAP.md` - Phase 0 상세 가이드
- `docs/architecture_modular.md` - 시스템 아키텍처
- GCP Documentation: https://cloud.google.com/docs

---

## 🔗 Related Issues

- #2 - M1 Dataflow Deployment
- #3 - M2 Video Metadata Deployment
- #4 - M3 Timecode Validation Deployment
- #5 - M4 RAG Search Deployment
- #6 - M5 Clipping Deployment
- #7 - M6 Web UI Deployment

---

## 📝 Notes

**Prerequisites**:
- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated
- Project owner or editor permissions

**Security**:
- All service accounts follow principle of least privilege
- No hardcoded credentials in code
- Secrets managed via Secret Manager (to be configured in Phase 1)

**Support**:
- Contact: aiden.kim@ggproduction.net
- Slack: #poker-brain-infra
