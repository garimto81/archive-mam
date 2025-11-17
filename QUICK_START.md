# POKER-BRAIN Quick Start Guide (사용자용)

**대상**: 사용자 1명 (aiden.kim)
**팀 구성**: 나 + AI 서브에이전트 17개
**소요 시간**: 20분 (승인 2회) + 9주 (자동 실행)

---

## 🚀 3단계로 끝내기

### Step 1: 프로젝트 시작 (1분)

```bash
# 단 1줄 명령
python scripts/run_full_workflow.py
```

**출력 예시**:
```
🚀 POKER-BRAIN 자동화 워크플로우 시작
==========================================================
팀 구성: 사용자 1명 + AI 서브에이전트 17개
자동화율: 95%
예상 완료: 9주

==========================================================
📅 Week 1 시작...
==========================================================

📋 Week 1: API 설계 및 OpenAPI 스펙 자동 생성
------------------------------------------------------------

1️⃣ microservices-pm 에이전트 호출 중...
   → PRD 읽기 (docs/prd_final.md)
   → 6개 OpenAPI 스펙 자동 생성 중...
   ✅ modules/m1-data-ingestion/openapi.yaml
   ✅ modules/m2-video-metadata/openapi.yaml
   ✅ modules/m3-timecode-validation/openapi.yaml
   ✅ modules/m4-rag-search/openapi.yaml
   ✅ modules/m5-clipping/openapi.yaml
   ✅ modules/m6-web-ui/openapi.yaml

2️⃣ API 일관성 검증 중...
   ✅ 인증 방식 일관성 확인
   ✅ 에러 응답 형식 통일 확인
   ✅ API 버저닝 확인 (/v1/)

3️⃣ PM 승인 요청 발송...
   📧 Slack + Email 발송 완료 (aiden.kim@ggproduction.net)

⏳ PM 승인 대기 중...

💡 승인 명령:
   python scripts/approve_week.py --week 1
```

---

### Step 2: Week 1 승인 (10분)

**스펙 검토**:
```bash
# 6개 OpenAPI 스펙 파일 확인
cat modules/m1-data-ingestion/openapi.yaml
cat modules/m2-video-metadata/openapi.yaml
cat modules/m3-timecode-validation/openapi.yaml
cat modules/m4-rag-search/openapi.yaml
cat modules/m5-clipping/openapi.yaml
cat modules/m6-web-ui/openapi.yaml
```

**승인**:
```bash
python scripts/approve_week.py --week 1
```

**출력**:
```
==========================================================
✅ Week 1 승인
==========================================================

승인 요청 정보:
  • 요청 주차: Week 1
  • 요청 시간: 2025-01-17T10:23:45
  • 상태: pending

📋 Week 1 승인 내용:
  • OpenAPI 스펙 6개 생성 완료
  • API 일관성 검증 통과

💡 검토 사항:
  - modules/m1-data-ingestion/openapi.yaml
  - modules/m2-video-metadata/openapi.yaml
  - modules/m3-timecode-validation/openapi.yaml
  - modules/m4-rag-search/openapi.yaml
  - modules/m5-clipping/openapi.yaml
  - modules/m6-web-ui/openapi.yaml

Week 1을(를) 승인하시겠습니까? (y/n): y

✅ Week 1 승인 완료
   파일 생성: .validation/week-1-approval.json
   승인자: aiden.kim@ggproduction.net
   승인 시간: 2025-01-17T10:35:12

📅 다음: Week 2 (Mock 환경 구축) 자동 시작
```

---

### Step 3: 9주 대기 → Week 9 최종 승인 (10분)

**9주 후 (자동 실행 완료)**:

Slack/Email 알림:
```
🚀 Week 9 Production 배포 완료!

PM 최종 승인이 필요합니다.

승인 명령:
  python scripts/approve_week.py --week 9
```

**최종 승인**:
```bash
python scripts/approve_week.py --week 9
```

**출력**:
```
==========================================================
✅ Week 9 승인
==========================================================

🚀 Week 9 최종 승인 내용:
  • Staging 배포 완료
  • Production 배포 완료
  • E2E 테스트 100% 통과

💡 Production URLs:
  - M1: https://data-ingestion-service-prod.run.app
  - M2: https://video-metadata-service-prod.run.app
  - M3: https://timecode-validation-service-prod.run.app
  - M4: https://rag-search-service-prod.run.app
  - M5: https://clipping-service-prod.run.app
  - M6: https://poker-brain.ggproduction.net

Week 9을(를) 승인하시겠습니까? (y/n): y

✅ Week 9 승인 완료

🎉 POKER-BRAIN 프로젝트 완료!
   Production URL: https://poker-brain.ggproduction.net
   🍾 런치 파티: 2025-02-21 (금) 18:00
```

---

## 🎯 끝!

**사용자 작업 시간**: 총 20분
- Step 1: 1분 (명령 실행)
- Step 2: 10분 (Week 1 승인)
- Step 3: 10분 (Week 9 승인)

**자동 실행 시간**: 9주 (AI 서브에이전트들이 알아서 처리)

---

## ⚠️ 에스컬레이션 발생 시 (선택)

### 예시: Week 4 검증 3회 실패

**Slack/Email 알림**:
```
🚨 Week 4 검증 3회 실패 - PM 개입 필요

• 실패 주차: Week 4
• 재시도 횟수: 3회
• 에러 내용: Cloud Run deployment failed

@aiden.kim 즉시 검토 요청
```

**문제 해결 (1시간)**:
```bash
# 1. 로그 확인
cat .validation/week-4-result.json
gcloud run logs read data-ingestion-service

# 2. 문제 수정 (예: Dockerfile 수정)
vim m1-data-ingestion/Dockerfile

# 3. 재실행
python scripts/resume_workflow.py --week 4
```

**재실행 성공 후 자동 진행**

---

## 📊 전체 타임라인

```
Day 1:
  10:00 - 사용자: python scripts/run_full_workflow.py (1분)
  10:23 - Week 1 완료, 승인 대기
  10:30 - 사용자: OpenAPI 스펙 검토 (10분)
  10:35 - 사용자: python scripts/approve_week.py --week 1
  10:36 - Week 2-9 자동 실행 시작

Week 2-9: (자동 실행, 사용자 개입 불필요)
  - Week 2: Mock 환경 자동 구축
  - Week 3: 6개 에이전트 병렬 개발 시작
  - Week 4: M1 자동 완성 + 검증
  - Week 5: M2 완성 + Mock→Real 자동 전환
  - Week 6: M3-M6 자동 완성
  - Week 7: E2E 80% 자동 달성
  - Week 8: 버그 자동 수정 + E2E 100%
  - Week 9: Production 자동 배포

Day 63 (9주 후):
  14:00 - Week 9 완료, 최종 승인 대기
  14:10 - 사용자: Production URLs 확인 (10분)
  14:15 - 사용자: python scripts/approve_week.py --week 9
  14:16 - 🎉 프로젝트 완료!
```

---

## 🤖 AI 서브에이전트들이 하는 일

### Week 1 (microservices-pm)
- PRD 읽고 6개 OpenAPI 스펙 자동 생성
- API 일관성 자동 검증

### Week 2 (스크립트)
- Mock BigQuery 테이블 자동 생성
- Pub/Sub Emulator 자동 시작
- Prism Mock Servers 자동 시작

### Week 3-9 (6개 개발 에이전트 + 검증 에이전트)
- **Alice** (M1): Dataflow, BigQuery ETL 자동 개발
- **Bob** (M2): NAS 스캔, FFmpeg, 프록시 생성 자동 개발
- **Charlie** (M3): Vision API, sync_score 자동 개발
- **David** (M4): Vertex AI, RAG Search 자동 개발
- **Eve** (M5): Pub/Sub, FFmpeg 클리핑 자동 개발
- **Frank** (M6): Next.js, React UI 자동 개발
- **검증 에이전트들**: 각 주차별 자동 검증 + 재시도 + 에스컬레이션

---

## 📁 핵심 파일

```
scripts/
├── run_full_workflow.py          ← 마스터 스크립트 (이것만 실행!)
└── approve_week.py                ← 승인 스크립트 (Week 1, 9)

.validation/
├── current-week.txt               ← 현재 진행 주차
├── progress.json                  ← 진행 상황
├── week-1-approval.json           ← Week 1 승인 기록
├── week-9-approval.json           ← Week 9 승인 기록
└── final-report.json              ← 최종 리포트

docs/
├── FULL_AUTOMATION_EXECUTION_GUIDE.md  ← 상세 가이드
└── VALIDATION_CHECKLIST.md             ← 검증 체크리스트
```

---

## 💡 핵심 개념

### Alice-Frank는 AI 에이전트입니다!

- ❌ "Alice한테 작업 지시해야 한다"
- ❌ "Bob이 개발 완료했는지 확인해야 한다"
- ✅ "스크립트 실행하면 Alice 에이전트가 자동으로 개발한다"
- ✅ "검증 에이전트가 자동으로 확인한다"

### 사용자는 승인만 합니다

- **Week 1**: OpenAPI 스펙 검토 + 승인
- **Week 9**: Production 배포 승인
- **에스컬레이션**: 문제 발생 시만 개입

### 나머지는 전부 자동

- 개발: AI 에이전트 6개가 병렬 수행
- 검증: 검증 에이전트 5개가 자동 수행
- 재시도: 최대 3회 자동
- 에스컬레이션: 3회 실패 시 자동 알림

---

**시작하려면**:
```bash
python scripts/run_full_workflow.py
```

끝! 🎉
