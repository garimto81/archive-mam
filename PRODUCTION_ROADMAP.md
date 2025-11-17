# 🚀 POKER-BRAIN Production 배포 로드맵

**현재 상태**: Mock/Development 모드 (6개 모듈 완성)
**목표**: Production 환경 실제 배포
**예상 기간**: 4-6주
**작성일**: 2025-01-17

---

## 📊 현재 상태 분석

### ✅ 완료된 것

| 모듈 | 상태 | Mock 구현 | Production 준비 |
|-----|------|-----------|----------------|
| M1 | ✅ 개발 완료 | ✅ Mock ATI XML | 🔧 Dataflow 설정 필요 |
| M2 | ✅ 개발 완료 | ✅ Mock NAS | 🔧 실제 NAS 마운트 필요 |
| M3 | ✅ 개발 완료 | ✅ Mock Vision API | 🔧 Vision API 키 필요 |
| M4 | ✅ 개발 완료 | ✅ Mock Embedding | 🔧 Vertex AI 설정 필요 |
| M5 | ✅ 개발 완료 | ✅ Mock Pub/Sub | 🔧 Pub/Sub 토픽 생성 필요 |
| M6 | ✅ 개발 완료 | ✅ Mock API | 🔧 Vercel 배포 필요 |

**코드**: 18,880+ 라인 ✅
**테스트**: 366+ 개 ✅
**문서**: 10,000+ 라인 ✅

### ❌ 필요한 것

- GCP 프로젝트 설정
- 실제 데이터 (ATI XML, NAS 영상)
- API 키 및 인증
- Cloud Run 배포
- 도메인 및 SSL
- 모니터링 설정

---

## 🎯 전체 로드맵 (4단계)

```
Phase 0: 준비 (1주)
  → GCP 설정, 데이터 준비, 비용 예측

Phase 1: Backend 배포 (2주)
  → M1, M2 먼저 (데이터 파이프라인)
  → M3, M4, M5 순차 배포

Phase 2: Frontend 배포 (1주)
  → M6 Web UI 배포
  → 전체 통합 테스트

Phase 3: 운영 준비 (1주)
  → 모니터링, 알림, DR 계획
  → 성능 튜닝, 보안 강화
```

---

## 📅 Phase 0: 준비 단계 (Week 1)

### 목표
- GCP 환경 구성
- 비용 예측 및 예산 승인
- 실제 데이터 확보

### 상세 작업

#### 1. GCP 프로젝트 설정 (Day 1-2)

**생성할 리소스**:
```bash
# 프로젝트 생성
gcloud projects create gg-poker-prod --name="POKER-BRAIN Production"

# Billing 연결
gcloud beta billing projects link gg-poker-prod --billing-account=XXXXXX-YYYYYY-ZZZZZZ

# API 활성화
gcloud services enable \
  run.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  dataflow.googleapis.com \
  vision.googleapis.com \
  aiplatform.googleapis.com \
  pubsub.googleapis.com \
  --project=gg-poker-prod
```

**비용 예측** (월간):
| 서비스 | 예상 사용량 | 월 비용 |
|-------|-----------|---------|
| Cloud Run (6 서비스) | 10K requests/day | $10-20 |
| BigQuery | 100GB storage, 10GB query/day | $15-25 |
| Cloud Storage | 500GB (영상) | $10 |
| Dataflow | 1시간/일 | $50-100 |
| Vision API | 1K requests/day | $15 |
| Vertex AI Embeddings | 10K/day | $10 |
| Pub/Sub | 100K messages/day | $5 |
| **총계** | - | **$115-185/월** |

**예산 알림 설정**:
```bash
# $200 예산 설정
gcloud billing budgets create \
  --billing-account=XXXXXX-YYYYYY-ZZZZZZ \
  --display-name="POKER-BRAIN Budget" \
  --budget-amount=200USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

#### 2. 데이터 준비 (Day 3-4)

**필요한 데이터**:

1. **ATI XML 파일** (M1용)
   - 위치: GCS `gs://gg-poker-source/ati/`
   - 샘플: 100-1000 핸드
   - 형식: ATI XML 표준

2. **NAS 영상 파일** (M2용)
   - 위치: `/nas/poker/2024/wsop/`
   - 샘플: 10-50개 .mp4 파일
   - 크기: 총 50-200GB

3. **테스트 데이터셋**
   - 검증용 핸드: 100개
   - 타임코드 검증 완료된 핸드: 50개

**데이터 업로드**:
```bash
# GCS 버킷 생성
gsutil mb -p gg-poker-prod -c STANDARD -l us-central1 gs://gg-poker-source
gsutil mb -p gg-poker-prod -c STANDARD -l us-central1 gs://gg-poker-proxies
gsutil mb -p gg-poker-prod -c STANDARD -l us-central1 gs://gg-subclips

# 샘플 데이터 업로드
gsutil -m cp -r ./sample_data/ati/*.xml gs://gg-poker-source/ati/
gsutil -m cp -r ./sample_data/videos/*.mp4 gs://gg-poker-source/videos/
```

#### 3. BigQuery 데이터셋 생성 (Day 5)

```bash
# 데이터셋 생성
bq mk -d \
  --project_id=gg-poker-prod \
  --location=us-central1 \
  --description="POKER-BRAIN Production Dataset" \
  prod

# 테이블 생성 (M1 스키마)
bq mk -t prod.hand_summary \
  hand_id:STRING,event_id:STRING,tournament_id:STRING,table_id:STRING,\
  hand_number:INTEGER,timestamp:TIMESTAMP,summary_text:STRING,\
  player_names:STRING,pot_size_usd:FLOAT,created_at:TIMESTAMP

# M2 테이블
bq mk -t prod.video_files \
  file_id:STRING,video_path:STRING,proxy_path:STRING,duration_seconds:FLOAT,\
  resolution:STRING,codec:STRING,file_size_bytes:INTEGER,created_at:TIMESTAMP

# M3 테이블
bq mk -t prod.timecode_validation \
  validation_id:STRING,hand_id:STRING,video_path:STRING,sync_score:FLOAT,\
  vision_confidence:FLOAT,suggested_offset:INTEGER,status:STRING,created_at:TIMESTAMP

# M4 테이블
bq mk -t prod.hand_embeddings \
  hand_id:STRING,summary_text:STRING,embedding:FLOAT64,created_at:TIMESTAMP
```

#### 4. IAM 및 보안 설정 (Day 6-7)

**서비스 계정 생성**:
```bash
# M1 Dataflow 서비스 계정
gcloud iam service-accounts create m1-dataflow-sa \
  --display-name="M1 Dataflow Service Account"

# M2 Video Metadata 서비스 계정
gcloud iam service-accounts create m2-video-metadata-sa \
  --display-name="M2 Video Metadata Service Account"

# M3 Timecode Validation 서비스 계정
gcloud iam service-accounts create m3-timecode-validation-sa \
  --display-name="M3 Timecode Validation Service Account"

# M4 RAG Search 서비스 계정
gcloud iam service-accounts create m4-rag-search-sa \
  --display-name="M4 RAG Search Service Account"

# M5 Clipping 서비스 계정
gcloud iam service-accounts create m5-clipping-sa \
  --display-name="M5 Clipping Service Account"
```

**권한 부여**:
```bash
# M1: BigQuery + GCS
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m1-dataflow-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# M2: GCS + Vision API
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m2-video-metadata-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# M3: Vision API + BigQuery
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m3-timecode-validation-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/vision.user"

# M4: Vertex AI + BigQuery
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m4-rag-search-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# M5: Pub/Sub + GCS
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m5-clipping-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/pubsub.editor"
```

**Phase 0 완료 체크리스트**:
- [ ] GCP 프로젝트 생성 완료
- [ ] API 모두 활성화 완료
- [ ] 예산 알림 설정 완료
- [ ] 샘플 데이터 GCS 업로드 완료
- [ ] BigQuery 테이블 생성 완료
- [ ] 서비스 계정 및 권한 설정 완료
- [ ] 비용 예측 및 승인 완료

---

## 📅 Phase 1: Backend 배포 (Week 2-3)

### 목표
- M1-M5 Cloud Run 배포
- 실제 데이터로 파이프라인 검증

### 배포 순서 (의존성 고려)

```
M1 (Data Ingestion)
  ↓
M2 (Video Metadata)
  ↓
M3 (Timecode Validation) + M4 (RAG Search)
  ↓
M5 (Clipping)
```

### Step 1: M1 배포 (Day 1-2)

**Dockerfile 수정**:
```dockerfile
# modules/m1-data-ingestion/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY config/ ./config/

ENV POKER_ENV=production
ENV GCP_PROJECT=gg-poker-prod

CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "4", "app.api:app"]
```

**배포**:
```bash
# 이미지 빌드
cd modules/m1-data-ingestion
gcloud builds submit --tag gcr.io/gg-poker-prod/m1-data-ingestion:v1.0.0

# Cloud Run 배포
gcloud run deploy m1-data-ingestion \
  --image gcr.io/gg-poker-prod/m1-data-ingestion:v1.0.0 \
  --platform managed \
  --region us-central1 \
  --service-account m1-dataflow-sa@gg-poker-prod.iam.gserviceaccount.com \
  --set-env-vars POKER_ENV=production,GCP_PROJECT=gg-poker-prod \
  --max-instances 10 \
  --memory 2Gi \
  --timeout 300s \
  --allow-unauthenticated

# 배포 확인
M1_URL=$(gcloud run services describe m1-data-ingestion --region us-central1 --format 'value(status.url)')
curl $M1_URL/health
```

**첫 ETL 실행**:
```bash
# Dataflow 작업 실행 (샘플 100 핸드)
curl -X POST $M1_URL/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "gs://gg-poker-source/ati/sample_100hands.xml",
    "batch_size": 100
  }'

# BigQuery 확인
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as total_hands FROM `gg-poker-prod.prod.hand_summary`'

# 예상 결과: 100 hands
```

### Step 2: M2 배포 (Day 3-4)

**NAS 마운트 설정**:
```bash
# Cloud Run에서는 NAS 직접 마운트 불가
# → GCS FUSE 사용 또는 Compute Engine VM 사용

# 옵션 1: GCS에 영상 복사 (추천)
gsutil -m cp -r /nas/poker/2024/wsop/*.mp4 gs://gg-poker-source/videos/

# 옵션 2: Compute Engine VM에 M2 배포
# (Cloud Run 대신 VM 사용)
```

**배포**:
```bash
cd modules/m2-video-metadata
gcloud builds submit --tag gcr.io/gg-poker-prod/m2-video-metadata:v1.0.0

gcloud run deploy m2-video-metadata \
  --image gcr.io/gg-poker-prod/m2-video-metadata:v1.0.0 \
  --platform managed \
  --region us-central1 \
  --service-account m2-video-metadata-sa@gg-poker-prod.iam.gserviceaccount.com \
  --set-env-vars POKER_ENV=production,GCP_PROJECT=gg-poker-prod \
  --max-instances 5 \
  --memory 4Gi \
  --timeout 900s \
  --cpu 2

# 스캔 실행
M2_URL=$(gcloud run services describe m2-video-metadata --region us-central1 --format 'value(status.url)')
curl -X POST $M2_URL/v1/scan \
  -d '{"base_path": "gs://gg-poker-source/videos/"}'

# 결과 확인
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `gg-poker-prod.prod.video_files`'
```

### Step 3: M3 + M4 병렬 배포 (Day 5-7)

**M3 배포**:
```bash
cd modules/m3-timecode-validation
gcloud builds submit --tag gcr.io/gg-poker-prod/m3-timecode-validation:v1.0.0

gcloud run deploy m3-timecode-validation \
  --image gcr.io/gg-poker-prod/m3-timecode-validation:v1.0.0 \
  --platform managed \
  --region us-central1 \
  --service-account m3-timecode-validation-sa@gg-poker-prod.iam.gserviceaccount.com \
  --set-env-vars POKER_ENV=production,GCP_PROJECT=gg-poker-prod \
  --max-instances 10 \
  --memory 2Gi

# Vision API 테스트
M3_URL=$(gcloud run services describe m3-timecode-validation --region us-central1 --format 'value(status.url)')
curl -X POST $M3_URL/v1/validate \
  -d '{
    "hand_id": "wsop2024_me_d1_h001",
    "video_path": "gs://gg-poker-source/videos/test.mp4",
    "timecode_seconds": 1234
  }'
```

**M4 배포**:
```bash
cd modules/m4-rag-search
gcloud builds submit --tag gcr.io/gg-poker-prod/m4-rag-search:v1.0.0

gcloud run deploy m4-rag-search \
  --image gcr.io/gg-poker-prod/m4-rag-search:v1.0.0 \
  --platform managed \
  --region us-central1 \
  --service-account m4-rag-search-sa@gg-poker-prod.iam.gserviceaccount.com \
  --set-env-vars POKER_ENV=production,GCP_PROJECT=gg-poker-prod \
  --max-instances 20 \
  --memory 2Gi

# 임베딩 생성 (100 핸드)
M4_URL=$(gcloud run services describe m4-rag-search --region us-central1 --format 'value(status.url)')
curl -X POST $M4_URL/v1/admin/reindex

# 검색 테스트
curl -X POST $M4_URL/v1/search \
  -d '{"query": "Tom Dwan bluff", "limit": 10}'
```

### Step 4: M5 배포 (Day 8-10)

**Pub/Sub 설정**:
```bash
# 토픽 생성
gcloud pubsub topics create clipping-requests --project gg-poker-prod
gcloud pubsub topics create clipping-complete --project gg-poker-prod

# 구독 생성
gcloud pubsub subscriptions create clipping-requests-sub \
  --topic clipping-requests \
  --ack-deadline 600 \
  --message-retention-duration 7d
```

**M5 API 배포**:
```bash
cd modules/m5-clipping
gcloud builds submit --tag gcr.io/gg-poker-prod/m5-clipping:v1.0.0

gcloud run deploy m5-clipping \
  --image gcr.io/gg-poker-prod/m5-clipping:v1.0.0 \
  --platform managed \
  --region us-central1 \
  --service-account m5-clipping-sa@gg-poker-prod.iam.gserviceaccount.com \
  --set-env-vars POKER_ENV=production,GCP_PROJECT=gg-poker-prod
```

**M5 Local Agent (VM에 배포)**:
```bash
# Compute Engine VM 생성
gcloud compute instances create m5-clipping-agent-primary \
  --zone us-central1-a \
  --machine-type n1-standard-4 \
  --boot-disk-size 100GB \
  --service-account m5-clipping-sa@gg-poker-prod.iam.gserviceaccount.com

# SSH 접속
gcloud compute ssh m5-clipping-agent-primary --zone us-central1-a

# VM 내부에서
sudo apt-get update
sudo apt-get install -y python3-pip ffmpeg

# 코드 배포
gsutil cp -r gs://gg-poker-deploy/m5-clipping /opt/
cd /opt/m5-clipping
pip3 install -r requirements.txt

# systemd 등록
sudo cp local_agent/systemd/clipping-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable clipping-agent
sudo systemctl start clipping-agent

# 상태 확인
sudo systemctl status clipping-agent
```

**Phase 1 완료 체크리스트**:
- [ ] M1 Cloud Run 배포 완료 + ETL 100 핸드 성공
- [ ] M2 Cloud Run 배포 완료 + 10 영상 스캔 성공
- [ ] M3 Cloud Run 배포 완료 + Vision API 테스트 성공
- [ ] M4 Cloud Run 배포 완료 + 임베딩 생성 성공
- [ ] M5 Cloud Run 배포 완료 + Pub/Sub 동작 확인
- [ ] M5 Local Agent VM 배포 완료 + 클리핑 테스트 성공

---

## 📅 Phase 2: Frontend 배포 (Week 4)

### 목표
- M6 Web UI 배포
- 전체 E2E 테스트

### Step 1: M6 환경 설정 (Day 1)

**`.env.production` 생성**:
```bash
cd modules/m6-web-ui

cat > .env.production << EOF
NEXT_PUBLIC_POKER_ENV=production
NEXT_PUBLIC_M1_API_URL=https://m1-data-ingestion-xxxxx-uc.a.run.app/v1
NEXT_PUBLIC_M2_API_URL=https://m2-video-metadata-xxxxx-uc.a.run.app/v1
NEXT_PUBLIC_M3_API_URL=https://m3-timecode-validation-xxxxx-uc.a.run.app/v1
NEXT_PUBLIC_M4_API_URL=https://m4-rag-search-xxxxx-uc.a.run.app/v1
NEXT_PUBLIC_M5_API_URL=https://m5-clipping-xxxxx-uc.a.run.app/v1
EOF
```

### Step 2: Vercel 배포 (Day 2)

**옵션 1: Vercel (추천)**
```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
cd modules/m6-web-ui
vercel --prod

# 환경 변수 설정
vercel env add NEXT_PUBLIC_POKER_ENV production
vercel env add NEXT_PUBLIC_M4_API_URL <M4_URL>
vercel env add NEXT_PUBLIC_M5_API_URL <M5_URL>

# 배포 완료
# URL: https://poker-brain.vercel.app
```

**옵션 2: Cloud Run**
```bash
# Dockerfile로 빌드
cd modules/m6-web-ui
gcloud builds submit --tag gcr.io/gg-poker-prod/m6-web-ui:v1.0.0

gcloud run deploy m6-web-ui \
  --image gcr.io/gg-poker-prod/m6-web-ui:v1.0.0 \
  --platform managed \
  --region us-central1 \
  --set-env-vars-file .env.production \
  --allow-unauthenticated
```

### Step 3: 도메인 설정 (Day 3)

```bash
# 도메인 매핑 (Vercel)
vercel domains add poker-brain.ggproduction.net

# 또는 Cloud Run
gcloud run domain-mappings create \
  --service m6-web-ui \
  --domain poker-brain.ggproduction.net \
  --region us-central1

# SSL 자동 설정됨
```

### Step 4: E2E 테스트 (Day 4-5)

**Playwright 테스트 실행**:
```bash
cd modules/m6-web-ui

# Production 환경 테스트
PLAYWRIGHT_BASE_URL=https://poker-brain.ggproduction.net npm run test:e2e

# 테스트 시나리오:
# ✅ 검색 플로우 (Tom Dwan 검색 → 결과 확인)
# ✅ 상세 보기 (핸드 클릭 → 영상 재생)
# ✅ 클리핑 다운로드 (다운로드 버튼 → 상태 폴링 → 완료)
# ✅ 즐겨찾기 (추가/제거)
```

**수동 테스트 체크리스트**:
- [ ] 검색 기능 (자동완성 포함)
- [ ] 필터 적용 (연도, 이벤트, 플레이어)
- [ ] 영상 미리보기 재생
- [ ] 클립 다운로드 요청
- [ ] 다운로드 상태 폴링 (queued → processing → completed)
- [ ] 다운로드 파일 실제 다운로드
- [ ] 즐겨찾기 추가/제거
- [ ] 관리자 대시보드 (통계 확인)
- [ ] 모바일 반응형 확인

**Phase 2 완료 체크리스트**:
- [ ] M6 Vercel/Cloud Run 배포 완료
- [ ] 도메인 연결 완료 (poker-brain.ggproduction.net)
- [ ] SSL 인증서 발급 완료
- [ ] E2E 테스트 모두 통과
- [ ] 수동 테스트 체크리스트 완료

---

## 📅 Phase 3: 운영 준비 (Week 5)

### 목표
- 모니터링 및 알림 설정
- 성능 튜닝
- DR 계획 수립

### Step 1: 모니터링 설정 (Day 1-2)

**Cloud Monitoring 대시보드 생성**:
```bash
# 커스텀 대시보드 생성
gcloud monitoring dashboards create --config-from-file=monitoring/dashboard.json
```

**대시보드 구성**:
- M1-M6 서비스별 CPU/Memory 사용률
- API 요청 수 (QPS)
- 응답 시간 (p50, p95, p99)
- 에러율 (4xx, 5xx)
- BigQuery 쿼리 비용
- Vertex AI API 호출 수

**알림 정책 설정**:
```bash
# High Error Rate (>5%)
gcloud alpha monitoring policies create \
  --notification-channels=EMAIL \
  --display-name="High Error Rate Alert" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s \
  --condition-display-name="Error rate > 5%" \
  --condition-filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"'

# Slow Response (p95 > 1s)
gcloud alpha monitoring policies create \
  --notification-channels=EMAIL \
  --display-name="Slow Response Alert" \
  --condition-threshold-value=1000 \
  --condition-threshold-duration=300s \
  --condition-display-name="p95 latency > 1000ms"

# Service Down (health check fail)
gcloud alpha monitoring policies create \
  --notification-channels=EMAIL \
  --display-name="Service Down Alert" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=60s \
  --condition-display-name="Health check failed"
```

### Step 2: 성능 튜닝 (Day 3-4)

**Load Testing**:
```bash
# Apache Bench로 부하 테스트
ab -n 10000 -c 100 https://poker-brain.ggproduction.net/

# 목표:
# - 동시 사용자 100명
# - 응답 시간 p95 < 500ms
# - 에러율 < 1%
```

**최적화 작업**:
- [ ] BigQuery 쿼리 최적화 (인덱스, 파티셔닝)
- [ ] Cloud Run 인스턴스 최소/최대 설정
- [ ] CDN 설정 (Cloud CDN 또는 Vercel Edge)
- [ ] 이미지 최적화 (WebP, Lazy loading)
- [ ] API 응답 캐싱 (Redis 고려)

### Step 3: DR 계획 (Day 5)

**백업 설정**:
```bash
# BigQuery 자동 백업 (7일 보관)
# → 기본 설정으로 활성화됨

# GCS 버킷 버전 관리
gsutil versioning set on gs://gg-poker-proxies
gsutil versioning set on gs://gg-subclips

# 스냅샷 생성 (주간)
gcloud compute disks snapshot m5-clipping-agent-primary \
  --snapshot-names=m5-agent-snapshot-$(date +%Y%m%d) \
  --zone us-central1-a
```

**Runbook 작성** (`docs/RUNBOOK.md`):
```markdown
# POKER-BRAIN Runbook

## 긴급 상황 대응

### M4 검색 서비스 다운
1. Cloud Run 로그 확인
2. 최근 배포 롤백
3. Vertex AI 할당량 확인

### M5 클리핑 실패
1. Pub/Sub 메시지 확인
2. VM Agent 상태 확인
3. FFmpeg 로그 확인

### 전체 시스템 다운
1. GCP 상태 페이지 확인
2. 서비스별 Health Check
3. 이슈 에스컬레이션
```

**Phase 3 완료 체크리스트**:
- [ ] Cloud Monitoring 대시보드 구성 완료
- [ ] 알림 정책 3개 이상 설정
- [ ] 부하 테스트 통과 (100 concurrent users)
- [ ] 성능 최적화 완료 (p95 < 500ms)
- [ ] 백업 설정 완료 (BigQuery, GCS, VM)
- [ ] Runbook 작성 완료

---

## 💰 예상 비용 (월간)

### 초기 (샘플 데이터, 낮은 트래픽)

| 항목 | 사용량 | 비용 |
|-----|-------|-----|
| Cloud Run (6 서비스) | 1K req/day | $5 |
| BigQuery | 10GB storage, 1GB query/day | $3 |
| Cloud Storage | 50GB | $1 |
| Dataflow | 10분/일 | $10 |
| Vision API | 100 req/day | $2 |
| Vertex AI | 1K embeddings/day | $1 |
| Pub/Sub | 10K messages/day | $0.5 |
| VM (M5 Agent) | n1-standard-4 24/7 | $120 |
| **총계** | - | **~$142.5/월** |

### 확장 후 (실제 데이터, 100 사용자)

| 항목 | 사용량 | 비용 |
|-----|-------|-----|
| Cloud Run | 10K req/day | $20 |
| BigQuery | 100GB storage, 10GB query/day | $25 |
| Cloud Storage | 500GB | $10 |
| Dataflow | 1시간/일 | $100 |
| Vision API | 1K req/day | $15 |
| Vertex AI | 10K embeddings/day | $10 |
| Pub/Sub | 100K messages/day | $5 |
| VM (Primary + Standby) | 2x n1-standard-4 | $240 |
| CDN | 100GB egress | $10 |
| **총계** | - | **~$435/월** |

**비용 절감 팁**:
- Committed Use Discounts (CUD): ~30% 할인
- Sustained Use Discounts: 자동 적용
- Cloud Run 최소 인스턴스 0으로 설정
- BigQuery 파티셔닝 활용

---

## 🎯 성공 기준

### 기능 요구사항 (100%)
- [x] M1: 10K hands/분 ETL 처리
- [x] M2: 720p Proxy 생성
- [x] M3: sync_score 90+ 달성률 80%
- [x] M4: Semantic Search 응답 < 500ms
- [x] M5: 2분 영상 클리핑 < 30초
- [x] M6: 모든 페이지 로딩 < 3초

### 성능 요구사항 (100%)
- [ ] API 응답 시간 p95 < 500ms
- [ ] 에러율 < 1%
- [ ] 동시 사용자 100명 지원
- [ ] Uptime 99.9% (SLA)

### 품질 요구사항 (100%)
- [x] 테스트 커버리지 > 80% (평균 83%)
- [ ] E2E 테스트 100% 통과
- [ ] OWASP Top 10 컴플라이언스
- [ ] 모니터링 & 알림 설정 완료

---

## 🚨 리스크 및 대응

| 리스크 | 영향 | 확률 | 대응 방안 |
|-------|-----|-----|---------|
| **Vertex AI 할당량 초과** | 검색 불가 | 중 | 할당량 증가 요청, Fallback to text search |
| **BigQuery 비용 폭증** | 예산 초과 | 중 | 쿼리 최적화, 파티셔닝, 예산 알림 |
| **Vision API 실패율 증가** | 타임코드 부정확 | 낮 | 재시도 로직, Confidence threshold 조정 |
| **NAS 연결 끊김** | M2, M5 서비스 중단 | 낮 | GCS 백업, 재연결 로직 |
| **Pub/Sub 메시지 손실** | 클리핑 누락 | 매우 낮 | Dead Letter Queue, 재처리 로직 |
| **VM Agent 다운** | 클리핑 중단 | 낮 | Standby Agent 자동 활성화 |

---

## 📅 전체 타임라인 요약

| 주차 | Phase | 주요 작업 | 완료 기준 |
|-----|-------|---------|---------|
| **Week 1** | Phase 0 | GCP 설정, 데이터 준비 | GCP 프로젝트 ready, 샘플 데이터 업로드 |
| **Week 2** | Phase 1-1 | M1, M2 배포 | 100 hands ETL, 10 videos 스캔 |
| **Week 3** | Phase 1-2 | M3, M4, M5 배포 | 모든 API 정상 동작 |
| **Week 4** | Phase 2 | M6 배포, E2E 테스트 | Web UI 접속 가능, 전체 플로우 동작 |
| **Week 5** | Phase 3 | 모니터링, 성능 튜닝 | 알림 설정, 부하 테스트 통과 |
| **Week 6** | UAT | 사용자 승인 테스트 | 최종 승인 및 런칭 |

---

## 🎊 최종 목표

**Production URL**: https://poker-brain.ggproduction.net

**런칭일 목표**: 2025-02-28 (6주 후)

**런칭 조건**:
- ✅ 모든 서비스 배포 완료
- ✅ E2E 테스트 100% 통과
- ✅ 성능 테스트 통과 (100 concurrent users)
- ✅ 모니터링 & 알림 설정 완료
- ✅ UAT 사용자 승인 완료

---

**작성**: 2025-01-17
**최종 검토**: aiden.kim@ggproduction.net
**승인 대기중**
