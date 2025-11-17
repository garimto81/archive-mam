# POKER-BRAIN Validation Checklist (Week 1-9)

**버전**: 1.0.0
**최종 업데이트**: 2025-11-17
**목적**: 주차별 완료 기준 및 자동 검증 체크리스트

---

## 📊 전체 개요

POKER-BRAIN 프로젝트는 **Week 1-9 완전 자동화** 워크플로우를 사용합니다.

### 검증 시스템 구조

```
┌──────────────────────────────────────────────────────────┐
│         Workflow Orchestrator (Main)                     │
│  - Week 1-9 순차 실행                                    │
│  - 주차별 검증 에이전트 자동 호출                         │
│  - 재시도 관리 (최대 3회)                                │
│  - PM 에스컬레이션                                        │
└────────────┬─────────────────────────────────────────────┘
             │
             ├─→ Week 1-2 Validator (API + Mock 환경)
             ├─→ Week 4 Validator (M1 완료)
             ├─→ Week 5 Validator (Mock → Real 전환)
             ├─→ Week 7-8 Validator (E2E 80% → 100%)
             └─→ Week 9 Validator (Production 배포)
```

### 자동화 수준

| Week | 자동 검증 | 자동 재시도 | 자동 수정 | PM 에스컬레이션 |
|------|----------|------------|----------|----------------|
| 1-2  | ✅       | ✅ (3회)   | ✅       | ✅ (3회 실패 시) |
| 3    | Manual   | N/A        | N/A      | Manual          |
| 4    | ✅       | ✅ (3회)   | ✅       | ✅              |
| 5    | ✅       | ✅ (3회)   | ✅       | ✅              |
| 6    | Manual   | N/A        | N/A      | Manual          |
| 7-8  | ✅       | ✅ (3회)   | Partial  | ✅              |
| 9    | ✅       | ✅ (3회)   | ✅ + Rollback | ✅       |

---

## Week 1: API 설계 (완전 자동 검증)

### 완료 기준

- [ ] 6개 모듈 OpenAPI 스펙 완성
- [ ] API 계약 일관성 검증 통과
- [ ] PM 승인 완료

### L0: Pre-flight Check

- [ ] PRD 승인 완료 (`prd_final.md`)
- [ ] 팀 배정 확인 (Alice, Bob, Charlie, David, Eve, Frank)
- [ ] 타임라인 승인 완료 (`week-by-week-timeline.md`)

### L1: OpenAPI 스펙 완성

**검증 대상**: `modules/*/openapi.yaml`

- [ ] M1: Data Ingestion (4 endpoints)
  - `/v1/ingest` (POST)
  - `/v1/ingest/{job_id}/status` (GET)
  - `/v1/stats` (GET)
  - `/v1/ingest/{job_id}` (DELETE)
- [ ] M2: Video Metadata (8 endpoints)
- [ ] M3: Timecode Validation (8 endpoints)
- [ ] M4: RAG Search (7 endpoints)
- [ ] M5: Clipping (6 endpoints)
- [ ] M6: Web UI (8 BFF endpoints)

**자동 검증**:
```bash
python .claude/plugins/agent-week-1-2-validator/validate.py --level L1
```

### L2: API 계약 일관성

- [ ] 모든 모듈이 동일한 인증 방식 사용
- [ ] 에러 응답 형식 통일 (`error` 필드 포함)
- [ ] API 버저닝 일관성 (`/v1/` prefix)
- [ ] Health check 엔드포인트 (`/health`) 모두 포함

### L3: PM 승인

- [ ] `.validation/week-1-approval.json` 파일 존재
- [ ] `approved: true` 확인
- [ ] 승인자: aiden.kim@ggproduction.net

**자동 알림**: PM 승인 대기 시 Slack + Email 발송

---

## Week 2: Mock 환경 구축 (완전 자동 검증)

### 완료 기준

- [ ] Mock BigQuery 테이블 생성 (M3용)
- [ ] Mock Embeddings 테이블 생성 (M4용)
- [ ] Pub/Sub Emulator 설정 (M5용)
- [ ] Prism Mock Servers 설정 (M6용)
- [ ] 6명 개발자 환경 설정 완료

### L0: Week 1 통과 확인

- [ ] Week 1 검증 통과 (`week-1` status = passed)
- [ ] OpenAPI 스펙 동결 확인

### L1: Mock BigQuery (M3용)

**테이블**: `gg-poker.dev.hand_summary_mock`, `dev.video_files_mock`

- [ ] 테이블 스키마 확인 (12+ 필드)
- [ ] Mock 데이터 최소 1000개 (hand_summary)
- [ ] Mock 데이터 최소 100개 (video_files)

**생성 스크립트**:
```bash
python scripts/generate_mock_data_m3.py
```

### L2: Mock Embeddings (M4용)

**테이블**: `gg-poker.dev.hand_embeddings_mock`

- [ ] Embedding 768차원 벡터 확인
- [ ] Mock 데이터 최소 1000개

**생성 스크립트**:
```bash
python scripts/generate_mock_data_m4.py
```

### L3: Pub/Sub Emulator (M5용)

- [ ] Emulator 실행 확인 (`localhost:8085`)
- [ ] Topic 생성: `clipping-requests`
- [ ] Subscription 생성: `clipping-requests-sub`

**시작 명령**:
```bash
gcloud beta emulators pubsub start --host-port=localhost:8085
```

### L4: Prism Mock Servers (M6용)

- [ ] M3 Mock Server 실행 (`localhost:8003`)
- [ ] M4 Mock Server 실행 (`localhost:8004`)
- [ ] M5 Mock Server 실행 (`localhost:8005`)

**시작 명령**:
```bash
prism mock modules/m3-timecode-validation/openapi.yaml --port 8003 &
prism mock modules/m4-rag-search/openapi.yaml --port 8004 &
prism mock modules/m5-clipping/openapi.yaml --port 8005 &
```

### L5: 개발자 환경 설정

- [ ] Alice (M1) 환경 설정 완료
- [ ] Bob (M2) 환경 설정 완료
- [ ] Charlie (M3) Mock BigQuery 접근 확인
- [ ] David (M4) Mock Embeddings 접근 확인
- [ ] Eve (M5) Pub/Sub Emulator 접근 확인
- [ ] Frank (M6) Prism Servers 접근 확인

**자동 검증**:
```bash
python .claude/plugins/agent-week-1-2-validator/validate.py --week 2
```

---

## Week 3: 개발 시작 (Manual 검증)

### 완료 기준

- [ ] 6명 개발자 모두 개발 시작
- [ ] 각 모듈 30% 진행률 달성

**검증 방식**: PM이 수동으로 진행률 확인

---

## Week 4: M1 완료 (완전 자동 검증)

### 완료 기준

- [ ] Dataflow 파이프라인 동작
- [ ] BigQuery 데이터 삽입 성공 (최소 10 hands)
- [ ] Flask API 3개 엔드포인트 동작
- [ ] Cloud Run 배포 완료
- [ ] M3, M4가 M1 데이터 읽기 성공

### L0: Pre-flight Check

- [ ] Week 3 검증 통과
- [ ] M1 진행률 ≥ 70%
- [ ] BigQuery 접근 가능

### L1: 작업 산출물 확인

**필수 파일**:
- [ ] `m1-data-ingestion/app/dataflow_pipeline.py`
- [ ] `m1-data-ingestion/app/api.py`
- [ ] `m1-data-ingestion/Dockerfile`
- [ ] `m1-data-ingestion/tests/test_pipeline.py`

**코드 품질**:
- [ ] 코드 라인 수 > 500
- [ ] 테스트 커버리지 > 80%

### L2: 기능 검증

- [ ] Dataflow 파이프라인 실행 성공
  ```bash
  python -m app.dataflow_pipeline \
    --gcs-path gs://gg-poker-ati/sample-10hands.jsonl \
    --runner DirectRunner
  ```
- [ ] BigQuery 데이터 확인 (≥ 10 rows)
  ```sql
  SELECT COUNT(*) FROM `gg-poker.prod.hand_summary`
  ```
- [ ] Flask API Health Check
  ```bash
  curl http://localhost:8001/health
  ```

### L3: 통합 검증

- [ ] M3 (Charlie)가 M1 데이터 읽기 성공
- [ ] M4 (David)가 M1 데이터 읽기 성공

### L4: Production Readiness

- [ ] Cloud Run 배포 확인
  ```bash
  gcloud run services describe data-ingestion-service --region us-central1
  ```
- [ ] Production Health Check 통과
- [ ] README.md 문서화 (> 50 lines)

**자동 검증**:
```bash
python scripts/run_weekly_validator.py --week 4 --max-attempts 3
```

**자동 수정**:
- BigQuery 스키마 불일치 → 자동 재생성
- Dataflow 실패 → 파이프라인 자동 수정
- Cloud Run 배포 실패 → Dockerfile 자동 수정 + 재빌드

---

## Week 5: M2 완료 + Mock → Real 전환 (완전 자동 검증)

### 완료 기준

- [ ] M2 Video Metadata Service 완료
- [ ] M3 Mock → Real BigQuery 전환
- [ ] M4 Mock → Real Vertex AI 전환
- [ ] M5 Emulator → Real Pub/Sub 전환
- [ ] M6 Prism → Real API 전환

### L0: Pre-flight Check

- [ ] Week 4 통과
- [ ] M2 진행률 ≥ 80%
- [ ] M1 배포 완료

### L1: M2 완료 검증

**필수 파일**:
- [ ] `m2-video-metadata/app/nas_scanner.py`
- [ ] `m2-video-metadata/app/metadata_extractor.py`
- [ ] `m2-video-metadata/app/proxy_generator.py`

**기능 테스트**:
- [ ] Cloud Run 배포 확인
- [ ] NAS scan API 동작 (`/v1/scan`)
- [ ] 프록시 파일 생성 확인 (GCS `gs://gg-poker-ati/proxy/`)

### L2: M3 Mock → Real 전환

- [ ] 환경 변수 전환: `POKER_ENV=production`
- [ ] Real BigQuery 접근 테스트
  ```sql
  SELECT * FROM `gg-poker.prod.hand_summary` LIMIT 5
  ```
- [ ] M3 API로 Real 데이터 검증
  ```bash
  curl -X POST https://timecode-validation-service/v1/timecode/validate \
    -d '{"hand_id": "wsop2024_me_d1_h001", ...}'
  ```

### L3: M4 Mock → Real 전환

- [ ] 환경 변수 전환: `POKER_ENV=production`
- [ ] Vertex AI 검색 테스트
  ```bash
  curl -X POST https://rag-search-service/v1/search \
    -d '{"query": "2024 WSOP all-in hands", "top_k": 5}'
  ```
- [ ] Relevance score > 0.1 확인 (Mock은 random)

### L4: M5 Emulator → Real 전환

- [ ] 환경 변수 확인 (`PUBSUB_EMULATOR_HOST` 제거)
- [ ] Real Pub/Sub Topic 확인: `clipping-requests`
- [ ] Clipping 요청 테스트
  ```bash
  curl -X POST https://clipping-service/v1/clip \
    -d '{"hand_id": "wsop2024_me_d1_h001", ...}'
  ```

### L5: M6 Prism → Real 전환

- [ ] 환경 변수 전환: `NEXT_PUBLIC_ENV=production`
- [ ] Real API URLs 설정 확인 (`M3_API_URL`, `M4_API_URL`, `M5_API_URL`)
- [ ] Next.js BFF로 Real API 호출 성공

### L6: 통합 테스트

**E2E 시나리오**: 검색 → Timecode 검증 → 클리핑 요청

- [ ] M4 검색 성공
- [ ] M3 sync_score > 50
- [ ] M5 clipping request_id 발급

**자동 검증**:
```bash
python scripts/run_weekly_validator.py --week 5 --max-attempts 3
```

**자동 수정**:
- 환경 변수 미전환 → 자동 `.env` 파일 수정
- BigQuery 접근 실패 → 권한 재설정
- Pub/Sub Topic 없음 → 자동 Topic 생성

---

## Week 6: M3, M4, M5, M6 완료 (Manual 검증)

### 완료 기준

- [ ] M3 Timecode Validation 완료
- [ ] M4 RAG Search 완료
- [ ] M5 Clipping 완료
- [ ] M6 Web UI 완료
- [ ] 전체 진행률 85%

**검증 방식**: PM이 수동으로 각 모듈 완성도 확인

---

## Week 7: E2E 테스트 80% 통과 (완전 자동 검증)

### 완료 기준

- [ ] Playwright E2E 테스트 작성 완료 (5개 시나리오)
- [ ] E2E 통과율 ≥ 80%
- [ ] 실패 테스트에서 버그 티켓 자동 생성

### L0: Pre-flight Check

- [ ] Week 6 통과
- [ ] 6개 모듈 모두 배포 완료
- [ ] 통합 테스트 통과

### L1: E2E 테스트 구현 확인

**필수 파일**:
- [ ] `m6-web-ui/tests/e2e/search-flow.spec.ts`
- [ ] `m6-web-ui/tests/e2e/video-preview.spec.ts`
- [ ] `m6-web-ui/tests/e2e/timecode-validation.spec.ts`
- [ ] `m6-web-ui/tests/e2e/clipping-request.spec.ts`
- [ ] `m6-web-ui/tests/e2e/download-clip.spec.ts`

**각 파일당 최소 3개 테스트 케이스** 필요

### L2: E2E 테스트 실행

```bash
cd m6-web-ui
npx playwright test --reporter=json
```

**통과 기준**: ≥ 80%

**자동 버그 티켓 생성**:
- 실패한 테스트 → `.validation/week-7-bug-tickets.json`
- 자동 담당자 배정 (테스트 파일 경로 기반)
- Slack 알림 발송

**자동 검증**:
```bash
python scripts/run_weekly_validator.py --week 7-8 --max-attempts 3
```

---

## Week 8: 버그 수정 + E2E 100% 통과 (완전 자동 검증)

### 완료 기준

- [ ] Week 7 버그 모두 수정 완료
- [ ] E2E 테스트 100% 통과
- [ ] Performance 테스트 통과
- [ ] Production 배포 준비 완료

### L0: Week 7 통과 확인

- [ ] Week 7 검증 통과
- [ ] 버그 티켓 확인 (`.validation/week-7-bug-tickets.json`)

### L1: 버그 수정 확인

- [ ] 모든 버그 티켓 `status: RESOLVED`
- [ ] 미해결 버그 0개

### L2: E2E 100% 통과

```bash
npx playwright test
```

**통과 기준**: 5 passed, 0 failed

### L3: Performance 테스트

- [ ] M3 Health Check p95 < 500ms
- [ ] M4 Health Check p95 < 500ms
- [ ] M5 Health Check p95 < 500ms
- [ ] M4 검색 평균 < 2초

### L4: Production 준비

- [ ] 모든 `.env` 파일 `POKER_ENV=production`
- [ ] Mock 설정 제거 (localhost, emulator)
- [ ] 문서화 완료 (README, deployment-guide, monitoring-guide, troubleshooting-guide)

**자동 검증**:
```bash
python scripts/run_weekly_validator.py --week 7-8 --max-attempts 3
```

---

## Week 9: Production 배포 (완전 자동 검증 + 자동 롤백)

### 완료 기준

- [ ] Staging 배포 성공
- [ ] Production 배포 성공
- [ ] E2E 테스트 100% 통과 (Production)
- [ ] 사용성 테스트 통과 (평균 만족도 ≥ 4.0/5.0)
- [ ] 모니터링 시스템 동작
- [ ] 재해 복구 준비 완료

### L0: Pre-flight Check

- [ ] Week 1-8 모두 통과
- [ ] PM 배포 승인 완료
- [ ] 이해관계자 승인 완료

### L1: Staging 배포 검증

**서비스**:
- [ ] data-ingestion-service-staging
- [ ] video-metadata-service-staging
- [ ] timecode-validation-service-staging
- [ ] rag-search-service-staging
- [ ] clipping-service-staging
- [ ] poker-brain-ui-staging

**검증**:
- [ ] 모든 서비스 Health Check 통과
- [ ] Staging E2E 테스트 5 passed

### L2: Production 배포 검증

**Production URLs**:
- [ ] M1: `https://data-ingestion-service-prod.run.app`
- [ ] M2: `https://video-metadata-service-prod.run.app`
- [ ] M3: `https://timecode-validation-service-prod.run.app`
- [ ] M4: `https://rag-search-service-prod.run.app`
- [ ] M5: `https://clipping-service-prod.run.app`
- [ ] M6: `https://poker-brain.ggproduction.net`

**검증**:
- [ ] DNS 설정 확인
- [ ] SSL 인증서 확인
- [ ] 모든 서비스 Health Check 통과 (최대 3회 재시도, 5초 간격)

### L3: Production E2E 테스트

```bash
ENVIRONMENT=production BASE_URL=https://poker-brain.ggproduction.net \
  npx playwright test
```

**통과 기준**: 5 passed, 0 failed

### L4: 사용성 테스트

- [ ] 최소 3명 테스터 참여
- [ ] 평균 만족도 ≥ 4.0/5.0
- [ ] Critical 이슈 0개

### L5: 모니터링 및 알림

- [ ] Cloud Monitoring 대시보드 확인
  - `poker-brain-overview`
  - `poker-brain-m1-m6`
  - `poker-brain-errors`
- [ ] 알림 정책 확인
  - `High Error Rate`
  - `Slow Response Time`
  - `Service Down`
- [ ] Slack Webhook 테스트

### L6: 재해 복구 준비

- [ ] BigQuery 자동 백업 확인 (7일 보관)
- [ ] 재해 복구 문서 확인
  - `docs/disaster-recovery-plan.md`
  - `docs/backup-restore-guide.md`
  - `docs/incident-response-playbook.md`
- [ ] 롤백 스크립트 확인: `scripts/rollback-deployment.sh`

**자동 검증**:
```bash
python scripts/run_weekly_validator.py --week 9 --max-attempts 3
```

**실패 시 자동 롤백**:
- 3회 재시도 후에도 실패 → `scripts/rollback-deployment.sh` 자동 실행
- PM 즉시 에스컬레이션 (Slack + Email)

---

## 🚀 실행 방법

### 로컬 실행

```bash
# 특정 주차 검증
python scripts/run_weekly_validator.py --week 1-2
python scripts/run_weekly_validator.py --week 4
python scripts/run_weekly_validator.py --week 5
python scripts/run_weekly_validator.py --week 7-8
python scripts/run_weekly_validator.py --week 9

# 전체 주차 순차 검증
python scripts/run_weekly_validator.py --week all

# 재시도 횟수 지정
python scripts/run_weekly_validator.py --week 4 --max-attempts 5
```

### GitHub Actions 실행

```bash
# Manual trigger
gh workflow run weekly-validation.yml -f week=4

# 자동 실행
# - 매주 월요일 09:00 KST
# - main, week-* 브랜치에 push 시
```

### 검증 결과 확인

```bash
# 특정 주차 결과
cat .validation/week-4-result.json

# 요약 리포트 생성
python scripts/generate_validation_summary.py
cat .validation/summary.md
```

---

## 📊 에스컬레이션 정책

| 상황 | 자동 재시도 | 자동 수정 | PM 에스컬레이션 | 워크플로우 |
|------|------------|----------|----------------|-----------|
| 1회 실패 | ✅ 5분 후 재시도 | ✅ | ❌ | 계속 |
| 2회 실패 | ✅ 30분 후 재시도 | ✅ | ❌ | 계속 |
| 3회 실패 | ❌ | ❌ | ✅ Slack + Email | 중단 |

**PM 에스컬레이션 내용**:
- 실패 주차
- 에러 메시지
- 재시도 기록
- 블로킹 시간
- 예상 지연

---

## 📧 알림 채널

- **Slack**: `#poker-brain-dev` (일반), `#poker-brain-alerts` (Critical)
- **Email**: aiden.kim@ggproduction.net
- **GitHub**: PR 코멘트 (검증 결과 요약)

---

**작성자**: aiden.kim@ggproduction.net
**에이전트**: Workflow Orchestrator + 5개 Week Validators
**자동화율**: 95%
