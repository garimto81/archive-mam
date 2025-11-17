# 완전 병렬 개발 전략 (6개 모듈 동시)

**목적**: 6명 팀원이 Week 3부터 동시에 개발 시작
**핵심**: Contract-First + Mock Everything
**작성일**: 2025-11-17
**버전**: 2.0.0 (업데이트)

---

## 🎯 핵심 전략

### 기존 방식 (Tier 기반)

```
Week 3-4: M1, M2, M5, M6 (4명)
    ↓
Week 5-6: M3, M4 시작 (6명)
    ↓
평균 활용률: 89%
```

### 새로운 방식 (완전 병렬) ⭐

```
Week 3-8: M1, M2, M3, M4, M5, M6 (6명 동시)
    ↓
평균 활용률: 100%
```

**효과**:
- ✅ 팀 활용률: 89% → **100%** (+11%p)
- ✅ Charlie, David 2주 일찍 시작
- ✅ 통합 테스트 시간 확보 (+1주)

---

## 🔑 핵심 1: Contract-First Development

### 1.1 OpenAPI 스펙 = 계약

```yaml
Week 1: API 스펙 확정 및 동결 ⭐
    ↓
Week 2: Mock 서버 구축 (모든 모듈)
    ↓
Week 3-6: 스펙 변경 금지 (Breaking Change 엄격 통제)
```

**규칙**:
- 스펙 변경 시 PM 승인 필수
- Breaking Change는 v2 API로 분리
- Optional 필드 추가만 허용

---

## 🔑 핵심 2: Mock Everything

### 2.1 모듈별 Mock 전략

#### M1 (Alice) - 독립

```
의존성 없음 → 즉시 시작 ✅
```

#### M2 (Bob) - 독립

```
의존성 없음 → 즉시 시작 ✅
```

#### M3 (Charlie) - Mock BigQuery ⭐

```yaml
의존성:
  - M1 (hand_summary) → Mock BigQuery data
  - M2 (video_files) → Mock BigQuery data
  - NAS 영상 → 샘플 영상 파일

Mock 준비:
  - Week 2에 Mock BigQuery 테이블 생성
  - 샘플 데이터 1000 rows 준비
  - 샘플 영상 파일 5개 준비
```

**Mock 데이터 예시**:
```sql
-- Week 2에 미리 생성
CREATE TABLE dev.hand_summary_mock (
  hand_id STRING,
  event_id STRING,
  timestamp_start_utc TIMESTAMP,
  timestamp_end_utc TIMESTAMP,
  players ARRAY<STRING>,
  pot_size_usd NUMERIC
);

-- 샘플 데이터 삽입
INSERT INTO dev.hand_summary_mock VALUES
  ('mock_001', 'wsop2024_me', '2024-07-15T15:24:15Z', '2024-07-15T15:26:45Z', ['Tom Dwan', 'Phil Ivey'], 450000),
  ('mock_002', 'wsop2024_me', '2024-07-15T16:10:30Z', '2024-07-15T16:12:15Z', ['Daniel Negreanu', 'Phil Hellmuth'], 280000),
  ...
  (1000 rows total);
```

#### M4 (David) - Mock BigQuery + Mock Vertex AI ⭐

```yaml
의존성:
  - M1 (hand_summary with embeddings) → Mock BigQuery data
  - Vertex AI → Vertex AI Emulator (선택) 또는 Real Vertex AI

Mock 준비:
  - Week 2에 Mock embedding 데이터 생성
  - Vertex AI는 Real 사용 (무료 티어)
```

**Mock Embedding 생성**:
```python
# scripts/generate_mock_embeddings.py
import numpy as np

# Random embedding (512-dim)
for hand_id in mock_hand_ids:
    embedding = np.random.rand(512).tolist()

    bigquery_client.query(f"""
        UPDATE dev.hand_summary_mock
        SET embedding = {embedding}
        WHERE hand_id = '{hand_id}'
    """)
```

#### M5 (Eve) - Mock Pub/Sub

```yaml
의존성:
  - Pub/Sub → Pub/Sub Emulator

Mock 준비:
  - Week 2에 Pub/Sub Emulator 설정
  - M6에서 발행 → M5에서 수신 테스트
```

#### M6 (Frank) - Mock All APIs

```yaml
의존성:
  - M3, M4, M5 → Prism Mock 서버

Mock 준비:
  - Week 2에 Prism 구축
  - M3, M4, M5 OpenAPI 스펙 기반 자동 응답
```

---

## 📅 새로운 타임라인 (6명 동시)

### Week 1-2: 준비 (동일)

**Week 1**: API 스펙 확정
**Week 2**: Mock 환경 구축 ⭐

#### Week 2 상세 일정

**월요일**:
- PM: Prism Mock 서버 구축 (M3, M4, M5용)
- Alice: BigQuery 스키마 생성 (prod + dev)
- Bob: 샘플 영상 파일 준비 (5개, NAS)
- Charlie: Vision API 학습
- David: Vertex AI 학습
- Eve: Pub/Sub Emulator 설정
- Frank: Next.js 프로젝트 초기화

**화요일**:
- PM: Mock BigQuery 데이터 생성 (1000 rows)
- Alice: Mock embedding 생성 스크립트
- Bob: FFmpeg 학습
- Charlie: M3 샘플 영상 + Mock data 연동 테스트
- David: M4 Mock BigQuery 연동 테스트
- Eve: M5 Pub/Sub Emulator 테스트
- Frank: M6 Prism Mock 연동 테스트

**수-목요일**:
- 전체: 각자 기술 스택 학습
- PM: Mock 환경 최종 검증

**금요일**:
- ✅ **개발 준비 완료 확인 미팅** (14:00-16:00)
  - 각자 Mock 환경 테스트 결과 공유
  - Week 3 개발 시작 선언 🚀

---

### Week 3-6: 완전 병렬 개발 ⭐

#### Week 3

| 팀원 | 모듈 | 작업 | 환경 |
|------|------|------|------|
| **Alice** | M1 | Dataflow 파이프라인 | Real GCS, BigQuery |
| **Bob** | M2 | NAS 스캔 + 메타데이터 | Real NAS, BigQuery |
| **Charlie** | M3 | Vision API + sync_score | **Mock BigQuery** ⭐ |
| **David** | M4 | Embedding + Vector Search | **Mock BigQuery** ⭐ |
| **Eve** | M5 | FFmpeg 클리핑 | **Pub/Sub Emulator** ⭐ |
| **Frank** | M6 | 검색 UI | **Prism Mock** ⭐ |

**효율**: 6/6 팀원 활발 (100%) 🎉

#### Week 4

- Alice: M1 API 서버 + 테스트 → **M1 완료** ✅
- Bob: M2 프록시 생성 + 테스트
- Charlie: M3 Offset 계산 + 수동 매칭
- David: M4 Re-ranking + 자동 완성
- Eve: M5 GCS 업로드 + Signed URL
- Frank: M6 다운로드 UI

#### Week 5

- Alice: M1 성능 최적화 (완료 후)
- Bob: M2 완료 → **M2 완료** ✅
- Charlie: M3 배치 검증
- David: M4 피드백 시스템
- Eve: M5 HA 설정
- Frank: M6 관리자 대시보드

#### Week 6

- Alice: M1 문서화
- Bob: M2 문서화
- Charlie: M3 완료 → **M3 완료** ✅
- David: M4 완료 → **M4 완료** ✅
- Eve: M5 완료 → **M5 완료** ✅
- Frank: M6 Mock → Real 전환 준비

**진행률**: 75% (모든 모듈 구현 완료)

---

### Week 7-8: Mock → Real 통합

#### Week 7: 데이터 통합

**월요일**:
- Charlie: M3 Mock → Real BigQuery 전환
  - M1 real data 연동
  - M2 real data 연동
- David: M4 Mock → Real BigQuery 전환
  - M1 real data 연동
  - Real embedding 생성 (100K hands, ~2시간)

**화-수요일**:
- Eve: M5 Mock → Real Pub/Sub 전환
- Frank: M6 Mock → Real API 전환
  - M3 API 연동
  - M4 API 연동
  - M5 API 연동

**목-금요일**:
- 전체: Contract Testing
  - M1 → M3 (data flow)
  - M1 → M4 (data flow)
  - M6 → M4 → M5 (user flow)

#### Week 8: E2E 테스트

- Playwright E2E 테스트
- 버그 수정
- 성능 최적화

**진행률**: 95%

---

### Week 9: Production 배포

동일 (기존 계획)

**진행률**: 100% ✅

---

## 🔄 Mock → Real 전환 가이드

### M3 (Charlie)

```python
# src/config.py
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'false') == 'true'

if USE_MOCK_DATA:
    BIGQUERY_TABLE = 'dev.hand_summary_mock'
else:
    BIGQUERY_TABLE = 'prod.hand_summary'

# Week 3-6: USE_MOCK_DATA=true
# Week 7+: USE_MOCK_DATA=false (Real data)
```

### M4 (David)

```python
# src/config.py
USE_MOCK_EMBEDDINGS = os.getenv('USE_MOCK_EMBEDDINGS', 'false') == 'true'

if USE_MOCK_EMBEDDINGS:
    BIGQUERY_TABLE = 'dev.hand_summary_mock'
else:
    BIGQUERY_TABLE = 'prod.hand_summary'

# Week 7: Real embedding 생성
python scripts/generate_embeddings.py --table prod.hand_summary
```

### M5 (Eve)

```bash
# Week 3-6: Pub/Sub Emulator
export PUBSUB_EMULATOR_HOST=localhost:8085

# Week 7+: Real Pub/Sub
unset PUBSUB_EMULATOR_HOST
```

### M6 (Frank)

```tsx
// lib/api-config.ts
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true';

export const API_ENDPOINTS = USE_MOCK ? {
  M3: 'http://localhost:8003',  // Prism
  M4: 'http://localhost:8004',  // Prism
  M5: 'http://localhost:8005',  // Prism
} : {
  M3: 'https://timecode-validation-service-prod.run.app',
  M4: 'https://rag-search-service-prod.run.app',
  M5: 'https://clipping-service-prod.run.app',
};

// Week 3-6: NEXT_PUBLIC_USE_MOCK=true
// Week 7+: NEXT_PUBLIC_USE_MOCK=false
```

---

## ⚠️ 리스크 관리

### 리스크 1: Mock 데이터 불일치

**문제**: Mock data가 실제와 달라 통합 시 버그

**대응**:
1. Week 2에 Alice가 Real 스키마 공유
2. Mock data 생성 시 Real 스키마 엄격 준수
3. Week 4부터 Alice가 Real data 샘플 제공 (100 rows)

---

### 리스크 2: 통합 시 버그 폭증

**문제**: Week 7 통합 시 예상보다 많은 버그

**대응**:
1. **Contract Testing** (Week 4부터)
   ```bash
   # M3가 M1 API 계약 준수 확인
   dredd modules/data-ingestion/openapi.yaml http://localhost:8001
   ```
2. **Integration Test** (Week 5부터)
   ```python
   # M1 → M3 데이터 흐름 테스트
   @pytest.mark.integration
   def test_m1_to_m3_flow():
       # M1에 데이터 수집
       # M3에서 검증
       # 결과 확인
   ```
3. Week 8을 버그 수정 전용으로 확보

---

### 리스크 3: Real Embedding 생성 실패

**문제**: Week 7에 100K embedding 생성 실패 (2시간+)

**대응**:
1. Week 5에 사전 테스트 (1K rows, ~1분)
2. 병렬 처리 (Dataflow)로 속도 향상
3. 실패 시 Mock embedding 계속 사용 (검색 정확도 낮음)

---

## 📊 비교: 기존 vs 새로운 방식

### 타임라인 비교

| Week | 기존 방식 | 새로운 방식 | 차이 |
|------|----------|------------|------|
| 3 | 4명 작업 | **6명 작업** | +2명 |
| 4 | 4명 작업 | **6명 작업** | +2명 |
| 5 | 6명 작업 | 6명 작업 | 동일 |
| 6 | 6명 작업 | 6명 작업 | 동일 |
| 7 | 6명 통합 | 6명 통합 + Mock→Real | 통합 작업 증가 |
| 8 | 버그 수정 | 버그 수정 | 동일 |

### 팀 활용률

| 방식 | Week 3-4 | Week 5-6 | 평균 |
|------|----------|----------|------|
| 기존 | 67% | 100% | 89% |
| 새로운 | **100%** | 100% | **100%** |

**개선**: +11%p 향상

---

### 리스크 비교

| 리스크 | 기존 | 새로운 | 대응 |
|--------|------|--------|------|
| M1 지연 | 높음 (M3, M4 블로킹) | **낮음** (Mock으로 독립) | ✅ |
| 통합 버그 | 중간 | **높음** | Contract Test 강화 |
| Mock 불일치 | 낮음 | **중간** | Real 스키마 엄격 준수 |

**결론**:
- ✅ 팀 활용률 대폭 향상
- ⚠️ 통합 리스크 증가 → Contract Testing으로 완화

---

## ✅ Week 2 체크리스트 (필수)

### PM 작업

- [ ] Prism Mock 서버 구축 (M3, M4, M5)
- [ ] Pub/Sub Emulator 설정
- [ ] Mock BigQuery 데이터 생성 (1000 rows)
- [ ] Mock embedding 생성
- [ ] 전체 Mock 환경 통합 테스트

### Alice (M1)

- [ ] BigQuery 스키마 생성 (prod + dev)
- [ ] Mock embedding 생성 스크립트 작성
- [ ] Charlie, David에게 스키마 공유

### Bob (M2)

- [ ] 샘플 영상 파일 5개 준비
- [ ] NAS 마운트 테스트
- [ ] Charlie에게 샘플 영상 경로 공유

### Charlie (M3)

- [ ] Mock BigQuery 연동 테스트
- [ ] 샘플 영상으로 Vision API 테스트
- [ ] Mock 환경 검증

### David (M4)

- [ ] Mock BigQuery 연동 테스트
- [ ] Vertex AI API 테스트
- [ ] Mock embedding으로 Vector Search 테스트

### Eve (M5)

- [ ] Pub/Sub Emulator 연동 테스트
- [ ] Frank와 메시지 송수신 테스트

### Frank (M6)

- [ ] Prism Mock 연동 테스트 (M3, M4, M5)
- [ ] Eve와 Pub/Sub Emulator 테스트

---

## 🎯 성공 기준

### Week 2 종료 시

- [x] 6명 모두 Mock 환경 동작 확인
- [x] 각자 "Hello World" 레벨 코드 실행 성공
- [x] Mock API 호출 성공 확인

### Week 6 종료 시

- [x] 6개 모듈 모두 구현 완료 (Mock 환경)
- [x] 유닛 테스트 80% 이상
- [x] Contract Test 통과

### Week 7 종료 시

- [x] Mock → Real 전환 완료
- [x] Integration Test 통과
- [x] E2E Test 50% 작성

---

## 📝 요약

### 핵심 변경사항

1. ✅ **6명 동시 시작** (Week 3부터)
2. ✅ **Mock Everything** (의존성 완전 제거)
3. ✅ **Contract-First** (API 스펙 = 계약)
4. ✅ **Week 2 준비 강화** (Mock 환경 구축)

### 효과

- 팀 활용률: 89% → **100%** (+11%p)
- Charlie, David 2주 일찍 시작
- 통합 테스트 시간 확보
- 전체 일정: 9주 (동일)

### 트레이드오프

- ✅ 장점: 병렬성 극대화, 팀 활용률 100%
- ⚠️ 단점: 통합 리스크 증가, Week 2 준비 작업 증가
- 🛡️ 대응: Contract Testing + Week 8 버그 수정

---

**작성자**: microservices-pm (AI Agent)
**버전**: 2.0.0 (완전 병렬 개발)
**업데이트**: 2025-11-17
**승인 필요**: aiden.kim@ggproduction.net
