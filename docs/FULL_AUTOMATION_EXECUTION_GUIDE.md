# POKER-BRAIN 완전 자동화 실행 가이드

**버전**: 1.0.0
**팀 구성**: 사용자 1명 (aiden.kim) + AI 서브에이전트 17개
**자동화율**: 95% (사용자는 승인만 수행)

---

## 🎯 핵심 개념

### 팀 구성 (재정의)

```
실제 팀 구성:
┌─────────────────────────────────────────────┐
│  사용자 (aiden.kim)                          │
│  - 역할: PM (승인, 에스컬레이션 대응)         │
│  - 작업: Week 1 승인, Week 9 최종 승인        │
└─────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  개발 에이전트   │    │  검증 에이전트   │
│  (6개)          │    │  (6개)          │
└─────────────────┘    └─────────────────┘
│                       │
├─ Alice (M1)          ├─ Orchestrator
├─ Bob (M2)            ├─ Week 1-2 Validator
├─ Charlie (M3)        ├─ Week 4 Validator
├─ David (M4)          ├─ Week 5 Validator
├─ Eve (M5)            ├─ Week 7-8 Validator
└─ Frank (M6)          └─ Week 9 Validator

        ┌───────────────────────┐
        │  설계 에이전트 (5개)   │
        └───────────────────────┘
        │
        ├─ microservices-pm
        ├─ video-processing
        ├─ validation-engineer
        ├─ video-pipeline
        └─ integration-qa
```

### Alice-Frank는 실제 사람이 아닙니다!

- **Alice** = `m1-data-ingestion-developer` AI 에이전트
- **Bob** = `m2-video-metadata-developer` AI 에이전트
- **Charlie** = `m3-timecode-validation-developer` AI 에이전트
- **David** = `m4-rag-search-developer` AI 에이전트
- **Eve** = `m5-clipping-developer` AI 에이전트
- **Frank** = `m6-web-ui-developer` AI 에이전트

모두 **Claude Code Task tool로 호출되는 서브에이전트**입니다.

---

## 🚀 Week별 실행 방식

### Week 1: API 설계 (자동 생성)

#### ❌ 잘못된 이해
```
사용자: "Alice-Frank가 각자 OpenAPI 스펙을 작성한다"
→ 6명의 사람이 작업해야 한다고 생각
```

#### ✅ 올바른 실행
```bash
# 사용자 명령 (단 1줄)
python scripts/run_week_1.py

# 내부 동작:
# 1. microservices-pm 에이전트 호출
# 2. PRD 읽기 (prd_final.md)
# 3. 6개 OpenAPI 스펙 자동 생성
#    - modules/m1-data-ingestion/openapi.yaml
#    - modules/m2-video-metadata/openapi.yaml
#    - modules/m3-timecode-validation/openapi.yaml
#    - modules/m4-rag-search/openapi.yaml
#    - modules/m5-clipping/openapi.yaml
#    - modules/m6-web-ui/openapi.yaml
# 4. API 일관성 검증
# 5. PM 승인 요청 (Slack + Email)
```

**사용자 역할**: 승인만 수행 (`.validation/week-1-approval.json` 생성)

```bash
# 승인 명령
python scripts/approve_week.py --week 1
```

---

### Week 2: Mock 환경 구축 (완전 자동)

#### 실행 방식

```bash
# 사용자 명령
python scripts/run_week_2.py

# 내부 동작:
# 1. Mock BigQuery 테이블 생성 (M3용)
#    → scripts/generate_mock_data_m3.py 자동 실행
# 2. Mock Embeddings 생성 (M4용)
#    → scripts/generate_mock_data_m4.py 자동 실행
# 3. Pub/Sub Emulator 시작 (M5용)
#    → gcloud beta emulators pubsub start
# 4. Prism Mock Servers 시작 (M6용)
#    → prism mock ... (3개 서버)
# 5. Week 2 Validator 자동 검증
```

**사용자 역할**: 없음 (완전 자동)

---

### Week 3: 개발 시작 (AI 에이전트 병렬 실행)

#### ❌ 잘못된 이해
```
"Alice-Frank 6명이 각자 개발을 시작한다"
→ 사용자가 6개 모듈을 순차적으로 개발해야 한다고 생각
```

#### ✅ 올바른 실행

```bash
# 사용자 명령 (단 1줄)
python scripts/run_week_3.py

# 내부 동작: 6개 에이전트 병렬 실행
```

**스크립트 내부 (run_week_3.py)**:

```python
from concurrent.futures import ThreadPoolExecutor

def run_week_3():
    """Week 3: 6개 모듈 동시 개발 시작"""

    # 6개 개발 에이전트 병렬 실행
    agents = [
        ('m1-data-ingestion-developer', 'Alice'),
        ('m2-video-metadata-developer', 'Bob'),
        ('m3-timecode-validation-developer', 'Charlie'),
        ('m4-rag-search-developer', 'David'),
        ('m5-clipping-developer', 'Eve'),
        ('m6-web-ui-developer', 'Frank'),
    ]

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = []

        for agent_id, name in agents:
            # Claude Code Task tool로 에이전트 호출
            future = executor.submit(
                invoke_agent,
                agent_id=agent_id,
                task=f"Week 3 개발 시작 (30% 목표)",
                context={
                    'week': 3,
                    'target_progress': 30,
                    'mock_enabled': True,
                }
            )
            futures.append((name, future))

        # 결과 수집
        for name, future in futures:
            result = future.result()
            print(f"✅ {name} ({result['agent_id']}): {result['progress']}% 완료")
```

**사용자 역할**: 없음 (자동 실행)

**실행 시간**: 약 20-30분 (6개 에이전트 병렬 실행)

---

### Week 4: M1 완료 (자동 검증 + 재시도)

#### 실행 방식

```bash
# 사용자 명령
python scripts/run_week_4.py

# 내부 동작:
# 1. Alice (M1) 에이전트 호출 → 100% 완성
# 2. Week 4 Validator 자동 검증
#    - Dataflow 파이프라인 검증
#    - BigQuery 데이터 삽입 확인
#    - Cloud Run 배포 확인
# 3. 실패 시 자동 재시도 (최대 3회)
# 4. 3회 실패 시 PM 에스컬레이션
```

**사용자 역할**:
- 정상: 없음
- 에스컬레이션 발생 시: 문제 해결 후 재실행

---

### Week 5-9: 동일한 패턴

```bash
python scripts/run_week_5.py  # M2 완료 + Mock→Real 전환
python scripts/run_week_6.py  # M3-M6 완료
python scripts/run_week_7.py  # E2E 80% 통과
python scripts/run_week_8.py  # E2E 100% + 버그 수정
python scripts/run_week_9.py  # Production 배포
```

---

## 🎮 마스터 실행 명령 (Week 1-9 한 번에)

### 완전 자동화 모드

```bash
# 단 1줄로 전체 실행
python scripts/run_full_workflow.py

# 또는 Workflow Orchestrator 직접 호출
python .claude/plugins/agent-workflow-orchestrator/orchestrate.py
```

**내부 동작**:

```python
def run_full_workflow():
    """Week 1-9 완전 자동 실행"""

    for week in range(1, 10):
        print(f"\n{'='*60}")
        print(f"📅 Week {week} 시작...")
        print(f"{'='*60}\n")

        # 주차별 실행
        if week == 1:
            # microservices-pm 에이전트 → OpenAPI 스펙 자동 생성
            invoke_agent('microservices-pm', 'Generate 6 OpenAPI specs')

            # PM 승인 대기
            wait_for_approval(week=1)

        elif week == 2:
            # Mock 환경 자동 구축
            setup_mock_environment()

            # Week 1-2 Validator 검증
            validate('week-1-2-validator')

        elif week == 3:
            # 6개 개발 에이전트 병렬 실행 (30% 목표)
            parallel_invoke([
                'm1-data-ingestion-developer',
                'm2-video-metadata-developer',
                'm3-timecode-validation-developer',
                'm4-rag-search-developer',
                'm5-clipping-developer',
                'm6-web-ui-developer',
            ], target_progress=30)

        elif week == 4:
            # Alice (M1) 100% 완성
            invoke_agent('m1-data-ingestion-developer', 'Complete M1')

            # Week 4 Validator 검증 (자동 재시도)
            validate('week-4-validator', max_attempts=3)

        # ... Week 5-9 동일 패턴

        elif week == 9:
            # Production 배포
            deploy_to_production()

            # Week 9 Validator 검증 (자동 롤백 포함)
            validate('week-9-validator', max_attempts=3, auto_rollback=True)

            # 성공 시 프로젝트 완료
            finalize_project()
```

---

## 📋 사용자 개입 시점

### 필수 승인 (2회만)

1. **Week 1 승인**: OpenAPI 스펙 검토 후 승인
   ```bash
   python scripts/approve_week.py --week 1
   ```

2. **Week 9 최종 승인**: Production 배포 전 최종 승인
   ```bash
   python scripts/approve_week.py --week 9
   ```

### 선택적 개입 (에스컬레이션 발생 시)

- **Week 4**: M1 검증 3회 실패 시 → 문제 해결 후 재실행
- **Week 5**: Mock→Real 전환 실패 시 → 환경 변수 확인 후 재실행
- **Week 7-8**: E2E 테스트 실패 시 → 버그 수정 후 재실행
- **Week 9**: Production 배포 실패 시 → 로그 확인 후 재실행

---

## 🤖 에이전트 호출 방식 (실제 코드)

### Claude Code Task tool 사용

```python
# Claude Code에서 Task tool 호출 예시

# 1. microservices-pm 호출 (Week 1)
Task(
    subagent_type="microservices-pm",
    description="Generate OpenAPI specs",
    prompt="""
    Read docs/prd_final.md and generate 6 OpenAPI 3.0 specs:

    1. M1 Data Ingestion (4 endpoints)
    2. M2 Video Metadata (8 endpoints)
    3. M3 Timecode Validation (8 endpoints)
    4. M4 RAG Search (7 endpoints)
    5. M5 Clipping (6 endpoints)
    6. M6 Web UI (8 BFF endpoints)

    Save to modules/*/openapi.yaml
    Ensure API consistency (auth, errors, versioning)
    """
)

# 2. Alice (M1) 호출 (Week 3-4)
Task(
    subagent_type="m1-data-ingestion-developer",
    description="Develop M1 Data Ingestion",
    prompt="""
    Implement M1 Data Ingestion Service:

    Week 3 (30%):
    - Set up project structure
    - Implement Dataflow pipeline skeleton
    - Create BigQuery schema

    Week 4 (100%):
    - Complete Dataflow pipeline (ParseATIJson DoFn)
    - Implement Flask API (3 endpoints)
    - Write unit tests (80% coverage)
    - Deploy to Cloud Run
    - Test with M3, M4 (ensure they can read data)
    """
)

# 3. 6개 에이전트 병렬 호출 (Week 3)
# Claude Code에서는 단일 메시지에 여러 Task 호출 가능
Task(subagent_type="m1-data-ingestion-developer", ...),
Task(subagent_type="m2-video-metadata-developer", ...),
Task(subagent_type="m3-timecode-validation-developer", ...),
Task(subagent_type="m4-rag-search-developer", ...),
Task(subagent_type="m5-clipping-developer", ...),
Task(subagent_type="m6-web-ui-developer", ...)
```

---

## 📊 사용자 작업 시간 비교

### 기존 방식 (수동 개발)

```
Week 1: OpenAPI 스펙 작성 (6개 모듈) → 40시간
Week 2: Mock 환경 구축 → 8시간
Week 3-9: 6개 모듈 개발 → 320시간 (6개 x 53시간)
검증 및 테스트 → 40시간
총: 408시간 (약 10주)
```

### 완전 자동화 (현재 시스템)

```
Week 1: 승인 → 10분
Week 2: 없음 (자동)
Week 3-9: 없음 (자동, 에스컬레이션 없으면)
Week 9: 최종 승인 → 10분
총: 20분 + 에스컬레이션 대응 시간

시간 절감: 99.9%
```

---

## 🎯 실제 사용 시나리오

### 시나리오 1: 정상 케이스 (에스컬레이션 없음)

```bash
# Day 1: 프로젝트 시작
aiden.kim$ python scripts/run_full_workflow.py

[출력]
🚀 POKER-BRAIN 자동화 워크플로우 시작
==========================================================

📅 Week 1 시작...
  → microservices-pm 에이전트 호출 중...
  → 6개 OpenAPI 스펙 생성 완료
  → API 일관성 검증 통과
  → PM 승인 요청 발송 (Slack + Email)
  ⏳ PM 승인 대기 중...

# Day 1: 승인 (10분 소요)
aiden.kim$ cat modules/m1-data-ingestion/openapi.yaml
aiden.kim$ cat modules/m4-rag-search/openapi.yaml
aiden.kim$ # 검토 완료, 승인
aiden.kim$ python scripts/approve_week.py --week 1

[출력]
✅ Week 1 승인 완료
📅 Week 2 시작...
  → Mock BigQuery 테이블 생성 중... ✅
  → Mock Embeddings 생성 중... ✅
  → Pub/Sub Emulator 시작... ✅
  → Prism Mock Servers 시작... ✅
  → Week 1-2 Validator 검증 중... ✅
✅ Week 2 검증 통과

📅 Week 3 시작...
  → 6개 개발 에이전트 병렬 실행 중...
     • Alice (M1): 진행 중... (30% 목표)
     • Bob (M2): 진행 중...
     • Charlie (M3): 진행 중...
     • David (M4): 진행 중...
     • Eve (M5): 진행 중...
     • Frank (M6): 진행 중...
  ✅ 6개 모듈 모두 30% 완료

📅 Week 4 시작...
  → Alice (M1) 100% 완성 중...
  → Week 4 Validator 검증 중...
  ✅ Week 4 검증 통과 (M1 완료)

... (Week 5-8 자동 진행)

📅 Week 9 시작...
  → Production 배포 중...
  → Week 9 Validator 검증 중...
  ⏳ PM 최종 승인 대기 중...

# Day 63: 최종 승인 (10분 소요)
aiden.kim$ python scripts/approve_week.py --week 9

[출력]
✅ Week 9 최종 승인 완료
🎉 POKER-BRAIN 프로젝트 완료!

==========================================================
📊 최종 통계:
  • 전체 주차: 9주
  • 성공 검증: 9/9
  • 총 재시도: 0회
  • PM 에스컬레이션: 0회
  • 팀 활용률: 100%
  • 자동화율: 95%
==========================================================

Production URL: https://poker-brain.ggproduction.net

🍾 런치 파티: 2025-02-21 (금) 18:00
```

**사용자 작업 시간**: 20분 (승인 2회)

---

### 시나리오 2: 에스컬레이션 발생 케이스

```bash
# Week 4 검증 중 실패
[출력]
❌ Week 4 검증 실패 (Attempt 1/3): BigQuery insert failed
🔧 자동 수정: BigQuery 스키마 수정 완료
⏳ 5분 대기 후 재시도...

❌ Week 4 검증 실패 (Attempt 2/3): Dataflow job failed
🔧 자동 수정: Dataflow 파이프라인 수정 완료
⏳ 30분 대기 후 재시도...

❌ Week 4 검증 실패 (Attempt 3/3): Cloud Run deployment failed
🚨 Week 4 검증 3회 실패 - PM 에스컬레이션
📧 Slack + Email 발송 완료
⏸️ 워크플로우 일시 중지

# 사용자 개입 (1시간 소요)
aiden.kim$ # Slack 알림 확인
aiden.kim$ cat .validation/week-4-result.json
aiden.kim$ # Cloud Run 로그 확인
aiden.kim$ gcloud run logs read data-ingestion-service
aiden.kim$ # 문제 해결 (예: Dockerfile 수정)
aiden.kim$ vim m1-data-ingestion/Dockerfile
aiden.kim$ # 재실행
aiden.kim$ python scripts/resume_workflow.py --week 4

[출력]
🔄 Week 4 재실행 중...
  → Week 4 Validator 검증 중...
  ✅ Week 4 검증 통과

📅 Week 5 시작...
... (이후 정상 진행)
```

**사용자 작업 시간**: 20분 (승인 2회) + 1시간 (에스컬레이션 대응)

---

## 📁 자동 실행 스크립트 구조

### 생성 필요한 스크립트

```
scripts/
├── run_full_workflow.py          ← 마스터 스크립트 (Week 1-9 한 번에)
├── run_week_1.py                 ← Week 1 전용
├── run_week_2.py                 ← Week 2 전용
├── run_week_3.py                 ← Week 3 전용
├── run_week_4.py                 ← Week 4 전용
├── ... (Week 5-9 동일)
├── approve_week.py               ← 승인 스크립트
└── resume_workflow.py            ← 재실행 스크립트
```

---

## ✅ 결론

### 사용자 역할

1. **명령 실행**: `python scripts/run_full_workflow.py` (1회)
2. **Week 1 승인**: OpenAPI 스펙 검토 (10분)
3. **Week 9 승인**: Production 배포 승인 (10분)
4. **에스컬레이션 대응**: 문제 발생 시만 (평균 1시간/건)

### AI 서브에이전트 역할

- **모든 개발 작업 자동 수행** (Week 1-9)
- **자동 검증** (각 주차별)
- **자동 재시도** (최대 3회)
- **자동 수정** (일반적인 오류)
- **자동 롤백** (Week 9 실패 시)

### 시간 절감

- **기존**: 408시간 (10주)
- **자동화**: 20분 + 에스컬레이션 (평균 0-2시간)
- **절감률**: 99.9%

---

**다음 단계**: 실제 실행 스크립트 작성 (`run_full_workflow.py` 등)
