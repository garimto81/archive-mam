# 완전 자동화 워크플로우 (Week 1-9)

**목적**: Production 배포까지 완전 자동화 및 엄격한 품질 관리
**전략**: 주차별 검증 게이트 + 자동 재시도 + 에스컬레이션
**작성일**: 2025-11-17
**버전**: 1.0.0

---

## 🎯 핵심 원칙

### 1. Gate-Based Approach
```
Week N 시작
    ↓
Week N 작업 수행
    ↓
Week N Validator 실행 ⭐
    ↓
✅ 통과 → Week N+1 시작
❌ 실패 → 자동 재시도 (최대 3회)
    ↓
3회 실패 → PM 에스컬레이션
```

### 2. 자동 재시도 전략
- **1차 실패**: 즉시 재시도 (5분 대기)
- **2차 실패**: 로그 분석 + 자동 수정 + 재시도 (30분 대기)
- **3차 실패**: PM에게 알림 + 수동 개입 대기

### 3. 검증 레벨
- **L0**: Pre-flight Check (사전 조건 확인)
- **L1**: 작업 완료 확인 (파일 존재, 코드 작성)
- **L2**: 기능 검증 (테스트 통과, API 동작)
- **L3**: 통합 검증 (다른 모듈과 연동)
- **L4**: Production Readiness (배포 준비 완료)

---

## 📋 주차별 검증 체크리스트

### Week 1: API 설계 검증 ⭐

**L0: Pre-flight Check**
- [ ] 팀원 6명 확정
- [ ] GCP 프로젝트 생성 (`gg-poker`)
- [ ] GitHub 저장소 생성 (`archive-mam`)

**L1: 작업 완료 확인**
- [ ] OpenAPI 스펙 6개 파일 존재 (`modules/*/openapi.yaml`)
- [ ] 각 스펙 최소 100줄 이상
- [ ] 각 스펙 `version: 1.0.0` 명시

**L2: 기능 검증**
- [ ] OpenAPI Validator 통과 (모든 스펙)
- [ ] 엔드포인트 총 41개 이상
- [ ] 인증 방식 일관성 (IAP Bearer Token)

**L3: 통합 검증**
- [ ] 의존성 그래프 생성 (Mermaid)
- [ ] 순환 의존성 없음
- [ ] Breaking Change 없음 (모두 v1.0.0)

**통과 기준**: L0-L3 모두 100% 통과

**자동 재시도**:
```python
if openapi_validation_fails:
    auto_fix_common_errors()  # 예: schema 오류 자동 수정
    retry()
```

---

### Week 2: Mock 환경 검증 ⭐

**L0: Pre-flight Check**
- [ ] Week 1 검증 통과
- [ ] BigQuery 데이터셋 생성 권한 확인

**L1: 작업 완료 확인**
- [ ] BigQuery Mock 테이블 2개 생성
  - `dev.hand_summary_mock` (1000 rows)
  - `dev.video_files_mock` (100 rows)
- [ ] Pub/Sub Emulator 실행 중 (`localhost:8085`)
- [ ] Prism Mock 서버 3개 실행 중
  - `localhost:8003` (M3)
  - `localhost:8004` (M4)
  - `localhost:8005` (M5)

**L2: 기능 검증**
- [ ] BigQuery Mock 데이터 조회 성공
  ```sql
  SELECT COUNT(*) FROM `gg-poker.dev.hand_summary_mock`
  -- 결과: 1000
  ```
- [ ] Pub/Sub Emulator 메시지 발행/구독 성공
  ```bash
  curl -X POST localhost:8085/v1/projects/gg-poker-dev/topics/test:publish
  ```
- [ ] Prism Mock API 호출 성공
  ```bash
  curl http://localhost:8004/v1/search -X POST
  # 200 OK + Mock 응답
  ```

**L3: 통합 검증**
- [ ] 6명 팀원 로컬 환경 검증 완료
- [ ] `.env.development` 파일 전체 배포
- [ ] Mock 데이터 품질 검증 (NULL 값 10% 이하)

**통과 기준**: L0-L3 모두 100% 통과

**자동 재시도**:
```python
if bigquery_mock_empty:
    regenerate_mock_data()  # 자동 재생성
    retry()

if pubsub_emulator_down:
    restart_emulator()
    retry()
```

---

### Week 3: 개발 시작 검증 ⭐

**L0: Pre-flight Check**
- [ ] Week 2 검증 통과
- [ ] 6명 팀원 모두 개발 환경 설정 완료

**L1: 작업 완료 확인** (6개 모듈)
- [ ] M1: 프로젝트 구조 생성 (`m1-data-ingestion/`)
- [ ] M2: 프로젝트 구조 생성 (`m2-video-metadata/`)
- [ ] M3: 프로젝트 구조 생성 (`m3-timecode-validation/`)
- [ ] M4: 프로젝트 구조 생성 (`m4-rag-search/`)
- [ ] M5: 프로젝트 구조 생성 (`m5-clipping/`)
- [ ] M6: 프로젝트 구조 생성 (`m6-web-ui/`)

**L2: 기능 검증** (각 모듈)
- [ ] M1: `app/dataflow_pipeline.py` 존재 + 기본 구조
- [ ] M2: `app/scanner.py` 존재 + NAS 스캔 로직
- [ ] M3: Mock BigQuery 연동 성공
  ```python
  get_hand_metadata('wsop2024_me_d1_h001')  # Mock 데이터 반환
  ```
- [ ] M4: Mock Embeddings 조회 성공
- [ ] M5: Pub/Sub Emulator 구독 성공
- [ ] M6: Next.js 프로젝트 실행 성공 (`npm run dev`)

**L3: 통합 검증**
- [ ] 유닛 테스트 최소 1개 이상 (각 모듈)
- [ ] Linting 통과 (flake8, eslint)
- [ ] Git 커밋 최소 3개 이상 (각 모듈)

**통과 기준**: 진행률 30% 이상 (전체 6개 모듈 평균)

**자동 재시도**:
```python
if module_progress < 20%:
    notify_developer(module, "진행률 부족")
    extend_deadline(days=2)
    retry()
```

---

### Week 4: M1 완료 검증 ⭐

**L0: Pre-flight Check**
- [ ] Week 3 검증 통과
- [ ] M1 진행률 70% 이상

**L1: 작업 완료 확인**
- [ ] M1 Dataflow 파이프라인 완성
- [ ] M1 Flask API 서버 구현 (3개 엔드포인트)
- [ ] M1 유닛 테스트 80% 커버리지
- [ ] M1 Dockerfile 작성

**L2: 기능 검증**
- [ ] Dataflow 파이프라인 실행 성공 (샘플 10 hands)
  ```bash
  python -m app.dataflow_pipeline --gcs-path=gs://sample.jsonl
  ```
- [ ] BigQuery에 데이터 삽입 확인
  ```sql
  SELECT COUNT(*) FROM `gg-poker.prod.hand_summary`
  -- 결과: 10
  ```
- [ ] API 엔드포인트 동작 확인
  ```bash
  curl http://localhost:8001/v1/stats
  # {"total_hands": 10}
  ```
- [ ] 중복 방지 검증 (동일 hand_id 재삽입 시 중복 없음)

**L3: 통합 검증**
- [ ] M3 (Charlie)가 `prod.hand_summary` 읽기 성공
- [ ] M4 (David)가 `prod.hand_summary` 읽기 성공

**L4: Production Readiness**
- [ ] Cloud Run 배포 성공
  ```bash
  gcloud run deploy data-ingestion-service --region us-central1
  ```
- [ ] Health check 응답 200 OK
- [ ] 문서화 완료 (README.md)

**통과 기준**: L0-L4 모두 100% 통과 ⭐ (M1 완료)

**자동 재시도**:
```python
if dataflow_job_failed:
    analyze_error_logs()
    auto_fix_schema_mismatch()
    retry()

if bigquery_insert_failed:
    check_table_schema()
    recreate_table_if_needed()
    retry()
```

---

### Week 5: Mock → Real 전환 검증 ⭐

**L0: Pre-flight Check**
- [ ] Week 4 검증 통과 (M1 완료)
- [ ] M2 진행률 70% 이상

**L1: 작업 완료 확인**
- [ ] M2 완료 (100%)
- [ ] M3 환경 변수 변경 (`POKER_ENV=production`)
- [ ] M4 환경 변수 변경 (`POKER_ENV=production`)
- [ ] M5 Pub/Sub Emulator → Real Pub/Sub 전환

**L2: 기능 검증**
- [ ] M3 Real BigQuery 연동 성공
  ```python
  # 환경: production
  hand = get_hand_metadata('wsop2024_me_d1_h001')
  assert hand is not None  # Real 데이터 조회 성공
  ```
- [ ] M4 Vertex AI Embedding 파이프라인 실행 중
  ```bash
  python -m app.embedding_pipeline --hands 1000
  ```
- [ ] M5 Real Pub/Sub Topic 메시지 발행 성공

**L3: 통합 검증**
- [ ] M3 sync_score 계산 (Real 데이터) 평균 70 이상
- [ ] M4 Vector Search 인덱스 생성 완료
- [ ] M5 Local Agent 구독 성공 (Real Topic)

**통과 기준**: 진행률 70% 이상 (M1, M2 완료, M3-M5 Real 전환)

**자동 재시도**:
```python
if real_bigquery_connection_failed:
    check_service_account_permissions()
    grant_permissions_if_needed()
    retry()

if vertex_ai_quota_exceeded:
    request_quota_increase()
    wait_for_quota_reset()
    retry()
```

---

### Week 6: 백엔드 완료 검증 ⭐

**L0: Pre-flight Check**
- [ ] Week 5 검증 통과
- [ ] M3, M4, M5 진행률 80% 이상

**L1: 작업 완료 확인**
- [ ] M3 완료 (100%) - Cloud Run 배포
- [ ] M4 완료 (100%) - Cloud Run 배포
- [ ] M5 완료 (100%) - Local Agent Production 배포

**L2: 기능 검증**
- [ ] M3 API 동작 확인
  ```bash
  curl https://timecode-validation-service-prod.run.app/v1/validate \
    -X POST -d '{"hand_id":"wsop2024_me_d1_h001","video_id":"wsop2024_me_d1_t1"}'
  # {"sync_score": 87.5}
  ```
- [ ] M4 검색 정확도 확인
  ```bash
  curl https://rag-search-service-prod.run.app/v1/search \
    -X POST -d '{"query":"Tom Dwan bluff"}'
  # 10개 결과 반환, relevance_score > 0.7
  ```
- [ ] M5 클리핑 성공
  ```bash
  # Pub/Sub 메시지 발행 → 1분 내 완료
  ```

**L3: 통합 검증**
- [ ] M3 + M4 + M5 연동 테스트
- [ ] M6 (Frank)이 M3, M4, M5 API 호출 성공 (Dev 환경)

**L4: Production Readiness**
- [ ] 백엔드 5개 모듈 모두 Cloud Run 배포 완료
- [ ] Health check 모두 200 OK
- [ ] 모니터링 설정 완료 (Cloud Monitoring)

**통과 기준**: 진행률 85% 이상 (백엔드 완료)

**자동 재시도**:
```python
if cloud_run_deployment_failed:
    check_dockerfile()
    rebuild_image()
    retry()

if api_response_timeout:
    increase_timeout_limit()
    scale_up_instances()
    retry()
```

---

### Week 7: 통합 테스트 검증 ⭐

**L0: Pre-flight Check**
- [ ] Week 6 검증 통과 (백엔드 완료)
- [ ] M6 진행률 70% 이상

**L1: 작업 완료 확인**
- [ ] M6 Mock → Real API 전환 완료
- [ ] E2E 테스트 시나리오 작성 (Playwright, 5개 이상)

**L2: 기능 검증**
- [ ] M6 → M4 검색 성공
  ```tsx
  // app/search/page.tsx
  const results = await fetch('/api/search', {method: 'POST'});
  // Real M4 API 호출 성공
  ```
- [ ] M6 → M5 클리핑 다운로드 성공
- [ ] M6 → M3 타임코드 검증 성공

**L3: 통합 검증**
- [ ] E2E 테스트 80% 통과 (5개 중 4개)
  ```bash
  npx playwright test
  # 4 passed, 1 failed
  ```
- [ ] 통합 시나리오 테스트
  - 검색 → 영상 미리보기 → 클리핑 요청 → 다운로드

**통과 기준**: 진행률 93% 이상, E2E 80% 통과

**자동 재시도**:
```python
if e2e_test_failed:
    analyze_test_logs()
    fix_common_ui_bugs()  # 예: selector 변경
    retry()

if api_integration_failed:
    check_cors_settings()
    update_api_endpoints()
    retry()
```

---

### Week 8: 버그 수정 검증 ⭐

**L0: Pre-flight Check**
- [ ] Week 7 검증 통과
- [ ] E2E 테스트 80% 이상 통과

**L1: 작업 완료 확인**
- [ ] Critical Bugs 모두 수정 (P0)
- [ ] Major Bugs 80% 수정 (P1)
- [ ] 성능 최적화 완료
  - M4 검색 속도 <500ms
  - M5 클리핑 속도 <60s (1시간 영상 기준)

**L2: 기능 검증**
- [ ] E2E 테스트 100% 통과
  ```bash
  npx playwright test
  # 5 passed, 0 failed ✅
  ```
- [ ] 부하 테스트 통과
  ```bash
  artillery run load-test.yml
  # p95 latency < 1000ms
  ```

**L3: 통합 검증**
- [ ] 전체 시스템 Smoke Test 통과
- [ ] 6개 모듈 모두 Health Check 200 OK

**L4: Production Readiness**
- [ ] 문서화 100% 완료
  - API 문서 (Swagger UI)
  - 운영 가이드
  - 트러블슈팅 가이드
- [ ] 알림 설정 완료 (Slack, Email)

**통과 기준**: 진행률 97% 이상, E2E 100% 통과

**자동 재시도**:
```python
if performance_degraded:
    optimize_database_queries()
    enable_caching()
    retry()

if e2e_flaky:
    increase_test_timeout()
    add_retry_logic()
    retry()
```

---

### Week 9: Production 배포 검증 ⭐⭐⭐

**L0: Pre-flight Check**
- [ ] Week 8 검증 통과
- [ ] Production 배포 승인 (PM)

**L1: 작업 완료 확인**
- [ ] Staging 환경 배포 완료
- [ ] Staging E2E 테스트 통과
- [ ] Production 환경 배포 완료
  - M1, M2, M3, M4, M5 (Cloud Run)
  - M6 (Cloud Run)
  - Local Agent (NAS 서버)

**L2: 기능 검증**
- [ ] Production Health Check 모두 200 OK
  ```bash
  curl https://data-ingestion-service-prod.run.app/health  # M1
  curl https://video-metadata-service-prod.run.app/health  # M2
  curl https://timecode-validation-service-prod.run.app/health  # M3
  curl https://rag-search-service-prod.run.app/health  # M4
  curl https://clipping-service-prod.run.app/health  # M5
  curl https://poker-brain-ui-prod.run.app/health  # M6
  ```
- [ ] Production E2E 테스트 통과
  ```bash
  ENVIRONMENT=production npx playwright test
  # 5 passed ✅
  ```

**L3: 통합 검증**
- [ ] 사용성 테스트 완료 (내부 사용자 3명)
- [ ] 실제 데이터로 검색 테스트 (100 hands)

**L4: Production Readiness**
- [ ] DNS 설정 완료 (`poker-brain.ggproduction.net`)
- [ ] SSL 인증서 설정 완료
- [ ] 모니터링 대시보드 설정 완료
- [ ] 백업 설정 완료 (BigQuery 자동 백업)
- [ ] 재해 복구 계획 문서화

**통과 기준**: L0-L4 모두 100% 통과 ⭐⭐⭐

**자동 재시도**:
```python
if production_deployment_failed:
    rollback_to_previous_version()
    analyze_deployment_logs()
    fix_deployment_issues()
    retry()

if production_e2e_failed:
    check_production_data()
    verify_api_keys()
    retry()
```

**최종 확인**:
```python
def final_validation():
    checks = [
        verify_all_services_running(),
        verify_data_pipeline_active(),
        verify_monitoring_alerts(),
        verify_backup_running(),
        verify_user_access(),
    ]

    if all(checks):
        send_notification("🎉 POKER-BRAIN Production 배포 완료!")
        mark_project_complete()
    else:
        escalate_to_pm("Production 배포 실패")
```

---

## 🤖 자동화 오케스트레이터

### Workflow Orchestrator Agent

**역할**: 전체 9주 워크플로우 자동 관리

**기능**:
1. 주차별 검증 에이전트 순차 실행
2. 검증 실패 시 자동 재시도 (최대 3회)
3. 3회 실패 시 PM 에스컬레이션
4. 진행 상황 모니터링 및 리포팅
5. 병목 구간 자동 감지 및 알림

**실행 흐름**:
```python
for week in range(1, 10):
    validator = load_validator(f"week-{week}-validator")

    for attempt in range(1, 4):  # 최대 3회
        result = validator.validate()

        if result.passed:
            log(f"✅ Week {week} 검증 통과")
            send_notification(f"Week {week} 완료")
            break
        else:
            log(f"❌ Week {week} 검증 실패 (Attempt {attempt}/3)")

            if attempt < 3:
                auto_fix(result.errors)
                wait(minutes=5 * attempt)  # 점진적 대기
            else:
                escalate_to_pm(f"Week {week} 3회 실패", result.errors)
                pause_workflow()
                break

    if not result.passed:
        break  # 해당 주차 통과 못하면 다음 주차 진행 안 함
```

---

## 📊 모니터링 대시보드

### 실시간 진행 상황

```
┌─────────────────────────────────────────────────┐
│  POKER-BRAIN 개발 진행 상황 (Week 5/9)        │
├─────────────────────────────────────────────────┤
│  전체 진행률: ████████████░░░░░ 70%            │
│                                                 │
│  Week 1: ✅ 통과 (API 설계)                    │
│  Week 2: ✅ 통과 (Mock 환경)                   │
│  Week 3: ✅ 통과 (개발 시작)                   │
│  Week 4: ✅ 통과 (M1 완료)                     │
│  Week 5: 🟡 진행 중 (Mock → Real 전환)        │
│    └─ M3: ✅ 전환 완료                         │
│    └─ M4: 🔄 Embedding 생성 중 (40%)          │
│    └─ M5: ⏸️ 대기 (M4 완료 후)               │
│  Week 6-9: ⏸️ 대기                            │
│                                                 │
│  현재 블로커: M4 Vertex AI Quota 부족          │
│  조치: Quota 증가 요청 완료, 승인 대기          │
└─────────────────────────────────────────────────┘
```

---

## 🔔 알림 시스템

### Slack 알림

**성공 알림**:
```
✅ Week 5 검증 통과!
• M3: Real BigQuery 전환 완료
• M4: Vertex AI Embedding 40% 진행
• 다음: Week 6 백엔드 완료

예상 완료: 2025-02-15
```

**실패 알림**:
```
❌ Week 5 검증 실패 (Attempt 2/3)
• M4: Vertex AI Quota 부족
• 자동 조치: Quota 증가 요청 완료
• 재시도: 30분 후

담당자: David (@david)
```

**에스컬레이션 알림** (3회 실패):
```
🚨 Week 5 검증 3회 실패 - PM 개입 필요
• M4: Vertex AI Quota 증가 승인 필요
• 블로킹 시간: 2시간
• 예상 지연: 1일

@aiden.kim 검토 요청
```

---

## 📈 성공 지표

| 지표 | 목표 | 실제 | 상태 |
|------|------|------|------|
| 전체 완료율 | 100% (Week 9) | 70% (Week 5) | 🟢 On Track |
| 자동 재시도 성공률 | 80% | 85% | 🟢 Good |
| PM 에스컬레이션 | <5회 | 2회 | 🟢 Good |
| 평균 주차 지연 | <2일 | 1.2일 | 🟢 Good |
| 검증 실패율 | <10% | 8% | 🟢 Good |

---

## ✅ 최종 완료 조건

**POKER-BRAIN 프로젝트 완료 정의**:

1. ✅ 6개 모듈 모두 Production 배포
2. ✅ E2E 테스트 100% 통과
3. ✅ 내부 사용자 사용성 테스트 완료 (3명)
4. ✅ 모니터링 및 알림 설정 완료
5. ✅ 문서화 100% 완료
6. ✅ 재해 복구 계획 수립 완료

**완료 시**:
```bash
python scripts/mark_project_complete.py

# 출력:
# 🎉 POKER-BRAIN 프로젝트 완료!
# • 개발 기간: 9주
# • 팀 활용률: 100%
# • 자동화율: 95%
# • 배포 성공률: 100%
#
# Production URL: https://poker-brain.ggproduction.net
# 런치 파티: 2025-02-21 (금) 18:00 🍾
```

---

**작성자**: workflow-orchestrator (AI Agent)
**버전**: 1.0.0
**마지막 업데이트**: 2025-11-17
