# 병렬 개발 전략

**목적**: 6명 팀원의 동시 작업 최대화
**목표**: 9주 내 전체 시스템 완성
**작성일**: 2025-11-17

---

## 1. 핵심 전략

### 1.1 Tier-based Development

```
Tier 1 (독립 모듈) → Tier 2 (Tier 1 의존) → Tier 3 (통합)
```

**Tier 1**: M1, M2, M5 (Mock)
- 의존성 없음
- Week 3부터 즉시 시작
- Critical Path 우선

**Tier 2**: M3, M4
- M1, M2 완료 후 시작
- Week 5부터 시작

**Tier 3**: M6
- M3, M4, M5 완료 후 통합
- Week 7부터 시작

---

## 2. 팀원별 작업 계획

### Week 3-4: **완전 병렬 개발** ⭐

| 팀원 | 모듈 | 작업 | 의존성 | Mock 전략 |
|------|------|------|--------|----------|
| **Alice** | M1 | Dataflow 파이프라인 구현 | ❌ 없음 | - |
| **Bob** | M2 | NAS 스캔 + 프록시 생성 | ❌ 없음 | - |
| **Charlie** | M3 | Vision API + sync_score 구현 | ✅ Mock BigQuery | **Mock 데이터** ⭐ |
| **David** | M4 | Vertex AI + Vector Search | ✅ Mock BigQuery + Embeddings | **Mock 데이터** ⭐ |
| **Eve** | M5 | Local Agent 구현 | ❌ 없음 | **Pub/Sub Emulator** |
| **Frank** | M6 | UI 개발 | ❌ 없음 | **Prism Mock Servers** |

**효율**: 6/6 팀원 활발 (**100%**) 🎉

---

### Week 5-6: Mock → Real 전환

| 팀원 | 모듈 | 작업 | Mock → Real 전환 |
|------|------|------|------------------|
| **Alice** | M1 | ✅ 완료 → 코드 리뷰 | - |
| **Bob** | M2 | 완료 준비 → ✅ 완료 | - |
| **Charlie** | M3 | Real 데이터 전환 + 최적화 | **Mock → Real** ⭐ |
| **David** | M4 | Real 데이터 전환 + Vector Search | **Mock → Real** ⭐ |
| **Eve** | M5 | Real Pub/Sub 통합 + HA | **Emulator → Real** |
| **Frank** | M6 | Real API 통합 준비 | **Mock → Real 준비** |

**효율**: 6/6 팀원 활발 (**100%**) ⭐
**핵심**: Charlie, David가 Mock 데이터로 2주 먼저 개발하고 Week 5에 Real 전환

---

### Week 7-8: Tier 3 통합

| 팀원 | 모듈 | 작업 | 의존성 |
|------|------|------|--------|
| **Alice** | M1 | 성능 최적화 | - |
| **Bob** | M2 | ✅ 완료 → 문서화 | - |
| **Charlie** | M3 | Phase 0 대시보드 UI 지원 | - |
| **David** | M4 | Re-ranking 알고리즘 개선 | - |
| **Eve** | M5 | Failover 테스트 | - |
| **Frank** | M6 | Real API 통합 + E2E 테스트 | ✅ M3, M4, M5 |

**효율**: 6/6 팀원 활발 (100%)

---

## 3. 블로킹 최소화 전략

### 3.1 Mock API (M6용)

```
Frank (M6) → Mock M4, M5
    ↓
  Week 3-6: 독립 개발
    ↓
  Week 7: Real API 전환
```

**효과**: Frank가 3주 일찍 시작 가능

---

### 3.2 BigQuery 테이블 우선 생성

```sql
-- Week 2에 미리 생성 (Alice)
CREATE TABLE prod.hand_summary (...);
CREATE TABLE prod.video_files (...);
```

**효과**: Charlie (M3), David (M4)가 스키마 참조 가능

---

### 3.3 OpenAPI Contract 엄격 준수

```
Week 1: API 스펙 확정 및 동결
    ↓
  Week 3-6: 스펙 변경 금지
    ↓
  변경 필요 시 → PM 승인 → Breaking Change 검토
```

**효과**: API 변경으로 인한 재작업 방지

---

## 4. 통신 프로토콜

### 4.1 일일 스탠드업 (15분, 매일 10:00)

**형식**:
```
각 팀원:
- 어제 완료: [작업]
- 오늘 할 일: [작업]
- 블로커: [이슈 또는 없음]
```

**예시**:
```
Alice (M1):
- 어제: Dataflow 파이프라인 80% 완료
- 오늘: 에러 핸들링 구현
- 블로커: 없음

Charlie (M3):
- 어제: 대기 (M1 미완)
- 오늘: Vision API 학습
- 블로커: M1 완료 대기 중 (예상: 내일)
```

---

### 4.2 주간 Sync-up (1시간, 금요일 16:00)

**Agenda**:
1. 각 모듈 진행률 (%)
2. 통합 이슈 논의
3. 다음 주 우선순위
4. API 변경 요청 검토

---

### 4.3 Slack 채널

```
#poker-brain-dev: 전체 개발 논의
#poker-brain-m1: M1 관련
#poker-brain-m2: M2 관련
...
#poker-brain-blockers: 블로킹 이슈 즉시 공유
```

---

## 5. 블로커 해결 프로세스

### 5.1 블로커 유형

**Type A: 의존성 블로커**
```
Charlie: "M1이 완료되어야 M3 시작 가능"
→ Alice에게 M1 예상 완료일 확인
→ Charlie는 대기 중 Vision API 학습
```

**Type B: 기술 블로커**
```
Eve: "Local Agent에서 NAS 마운트 실패"
→ #poker-brain-blockers에 공유
→ Bob (M2 NAS 전문가) 지원
```

**Type C: API 계약 블로커**
```
Frank: "M4 응답에 proxy_url 필요한데 스펙에 없음"
→ PM에게 Breaking Change 요청
→ PM 승인 후 David (M4)가 추가
→ 스펙 업데이트 및 전체 공유
```

---

## 6. 진행률 추적

### 6.1 주간 진행률 보고 (금요일)

```markdown
## Week 3 Progress Report (2025-01-19)

| 모듈 | 팀원 | 진행률 | 상태 | 블로커 |
|------|------|--------|------|--------|
| M1 | Alice | 80% | 🟢 On Track | 없음 |
| M2 | Bob | 65% | 🟢 On Track | 없음 |
| M3 | Charlie | 0% | ⏸️ Waiting | M1 완료 대기 |
| M4 | David | 0% | ⏸️ Waiting | M1 완료 대기 |
| M5 | Eve | 45% | 🟢 On Track | 없음 |
| M6 | Frank | 30% | 🟢 On Track | 없음 (Mock) |

**Overall**: 🟢 On Track
**Risk**: M1이 Week 4까지 완료되어야 M3, M4 시작 가능
```

---

## 7. 성공 지표

### 7.1 개발 속도

**목표**: Week당 15-20% 진행

```
Week 3: 20% (M1, M2, M5 Mock, M6 UI)
Week 4: 35% (M1 완료, M2 80%, M5 70%, M6 50%)
Week 5: 55% (M3, M4 시작 + 진행)
Week 6: 75% (M3, M4 완료, M5 완료)
Week 7: 90% (M6 통합, E2E 테스트)
Week 8: 95% (버그 수정)
Week 9: 100% (Production 배포)
```

---

### 7.2 팀 활용률

**목표**: 평균 85% 이상

```
기존 Tier 방식:
Week 3-4: 67% (Charlie, David 대기)
Week 5-8: 100% (전원 활발)
평균: (67% * 2 + 100% * 4) / 6 = 89%

신규 Mock Everything 방식: ⭐
Week 3-9: 100% (전원 활발, 7주 연속)
평균: 100% ✅ 목표 초과 달성

개선: +11% 향상 (+2명 × 2주 = 160시간 추가 생산성)
```

---

## 8. 리스크 관리

### 8.1 Critical Path 지연

**리스크**: M1이 Week 5로 밀리면 전체 일정 지연

**대응**:
1. M1 우선순위 최상 (Alice 전담)
2. Alice 블로킹 이슈 즉시 해결 (팀 전체 지원)
3. M1 진행률 매일 확인

---

### 8.2 통합 실패

**리스크**: Week 7 통합 시 API 불일치

**대응**:
1. OpenAPI Contract Testing (Week 4부터)
2. Weekly API 스펙 검토
3. Mock API로 사전 통합 테스트

---

## 9. 도구 활용

### 9.1 GitHub Projects

```
Board: POKER-BRAIN Development
Columns: Todo → In Progress → Review → Done

Cards:
- M1: Dataflow 파이프라인 구현 (Alice, Week 3-4)
- M2: NAS 스캔 로직 (Bob, Week 3-4)
...
```

---

### 9.2 OpenAPI Tools

```bash
# 스펙 검증 (CI)
npx @openapitools/openapi-generator-cli validate -i openapi.yaml

# Contract Testing
npm install -g dredd
dredd openapi.yaml http://localhost:8001
```

---

**작성자**: microservices-pm (AI Agent)
**최종 업데이트**: 2025-11-17
