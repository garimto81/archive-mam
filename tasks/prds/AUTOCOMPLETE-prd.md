# PRD: Autocomplete 기능 (AI 기반 오타 수정 + 자동완성)

**프로젝트**: archive-mam (포커 아카이브 검색 시스템)
**기능명**: Smart Autocomplete (AI-powered Typo Correction + Auto-suggestion)
**버전**: 1.0.0
**작성일**: 2025-11-19
**승인 상태**: Draft → Review 대기

---

## 📋 요약

포커 아카이브 검색 시스템에 **AI 기반 오타 수정 및 자동완성** 기능을 추가하여 사용자 경험을 개선합니다.

**핵심 가치**:
- 🎯 오타 허용: "Phil Ivy" → "Phil Ivey" 자동 제안
- ⚡ 빠른 검색: 타이핑 중 실시간 추천 (300ms debounce)
- 🧠 AI 의미 이해: "Junglman" → "Junglemann" (유사도 기반)

---

## 🎯 목표

### 비즈니스 목표
1. **검색 성공률 향상**: 60% → 85% (오타로 인한 실패 감소)
2. **검색 시간 단축**: 평균 15초 → 5초 (자동완성으로 입력 시간 단축)
3. **사용자 만족도**: NPS 70 → 85

### 기술 목표
1. **응답 속도**: API 응답 <100ms (p95)
2. **정확도**: 오타 수정 정확도 >85%
3. **확장성**: 10만 핸드 → 100만 핸드 대응

---

## 👥 사용자 스토리

### US-1: 오타 수정
```
As a 포커 코치
I want 선수 이름을 정확히 몰라도 검색이 되길 원함
So that 빠르게 원하는 핸드를 찾을 수 있다

예시:
- "Phil Ivy" 입력 → "Phil Ivey" 제안 ✅
- "Junglman" 입력 → "Junglemann" 제안 ✅
- "bluf" 입력 → "bluff" 제안 ✅
```

**수용 기준**:
- [ ] Levenshtein distance 2 이내 오타 감지
- [ ] 제안 단어 최대 5개
- [ ] 응답 시간 <100ms

### US-2: 자동완성
```
As a 포커 플레이어
I want 타이핑 중 자동완성 추천을 받고 싶다
So that 빠르게 검색할 수 있다

예시:
- "Phil" 입력 → ["Phil Ivey", "Phil Hellmuth", "Philip Ng"] 제안
- "river" 입력 → ["river call", "river bluff", "river decision"] 제안
```

**수용 기준**:
- [ ] 2글자 이상 입력 시 자동완성 시작
- [ ] 실시간 추천 (300ms debounce)
- [ ] 키보드 네비게이션 지원 (↑↓ Enter Esc)

### US-3: 유사어 추천
```
As a 비디오 편집자
I want 비슷한 의미의 태그를 추천받고 싶다
So that 일관된 검색이 가능하다

예시:
- "hero call" 검색 → "bluff catch", "thin call" 추천
- "river decision" → "river spot", "river play" 추천
```

**수용 기준**:
- [ ] Vertex AI 의미론적 검색 활용
- [ ] 유사도 점수 >0.7인 태그만 추천
- [ ] 최대 3개 추천

---

## 🏗️ 아키텍처

### 전체 구조
```
[프론트엔드]
Morphic UI
└── PokerCommandSearch (shadcn Command)
    └── semantic-autocomplete (MUI v6)
        ↓ HTTP GET
[백엔드]
FastAPI /api/autocomplete?q={query}&limit=5
├── BigQueryService (캐시 검색, 빠름 <10ms)
└── VertexSearchService (의미론적 검색, 느림 <100ms)
    ↓
[데이터]
BigQuery (hero_name, villain_name, tags)
Vertex AI Vector Search (embeddings)
```

### 기술 스택

**백엔드**:
- FastAPI 0.104+ (Python 3.11)
- Google Cloud BigQuery (캐시 레이어)
- Vertex AI TextEmbedding-004 (768차원)
- Vertex AI Vector Search (하이브리드 검색)

**프론트엔드**:
- Morphic UI (Next.js 15 + Vercel AI SDK)
- MUI Autocomplete v6 (공식 컴포넌트)
- shadcn/ui Command (키보드 네비게이션)
- TypeScript 5+

**변경 사유** (2025-11-19):
- semantic-autocomplete는 React 18 고정 → Next.js 15 App Router 불가
- TypeScript 공식 미지원 → 타입 안전성 문제
- MUI v6 Autocomplete로 동일 기능 구현 가능 (Vertex AI 백엔드 연동)

---

## 📊 API 스펙

### GET /api/autocomplete

**요청**:
```http
GET /api/autocomplete?q=Phil%20Ivy&limit=5
```

**응답** (성공, 200):
```json
{
  "suggestions": [
    "Phil Ivey",
    "Phil Hellmuth",
    "Philip Ng"
  ],
  "query": "Phil Ivy",
  "source": "bigquery_cache",
  "response_time_ms": 45
}
```

**응답** (에러, 422):
```json
{
  "error": "Query too short",
  "message": "Query must be at least 2 characters",
  "query": "P"
}
```

**파라미터**:
- `q` (required): 검색 쿼리 (최소 2자, 최대 100자)
- `limit` (optional): 추천 개수 (기본 5, 최대 10)

**응답 헤더**:
```
X-RateLimit-Remaining: 95
X-RateLimit-Limit: 100
X-Response-Time-Ms: 45
```

---

## 🎯 성능 목표

| 지표 | 목표 | 측정 방법 |
|------|------|---------|
| **API 응답 시간** | p95 <100ms | Prometheus |
| **정확도** | >85% | 수동 테스트 (100개 샘플) |
| **가용성** | >99.9% | Uptime monitoring |
| **동시 사용자** | 100명 | Load testing (Artillery) |
| **Rate Limit** | 100 req/min | FastAPI limiter |

### 성능 벤치마크

**BigQuery 캐시** (빠름):
- 응답 시간: <10ms
- 정확도: 95% (정확한 prefix 매칭)
- 커버리지: 선수명, 토너먼트명 (~1000개)

**Vertex AI 검색** (느림):
- 응답 시간: <100ms
- 정확도: 85% (의미론적 유사도)
- 커버리지: 모든 핸드 description, tags

---

## 🔒 보안 요구사항

### 1. Input Validation
```python
# 입력 검증
- 최소 길이: 2자
- 최대 길이: 100자
- 허용 문자: 영문, 숫자, 공백, 하이픈
- SQL Injection 방지: 파라미터화 쿼리
```

### 2. Rate Limiting
```
- 100 requests/minute per IP
- 429 Too Many Requests 응답
- Exponential backoff 권장
```

### 3. CORS
```python
# 허용 Origin
- https://morphic.archive-mam.com (production)
- http://localhost:3000 (development)
```

### 4. 개인정보 보호
```
- 검색 쿼리 로깅: 익명화 (IP 마스킹)
- 개인정보 없음 (선수명은 공개 정보)
```

---

## 🧪 테스트 계획

### 단위 테스트 (pytest)
```python
# backend/tests/services/test_autocomplete.py
def test_bigquery_prefix_search():
    """BigQuery prefix 검색 테스트"""
    results = bigquery_service.get_autocomplete_suggestions("Phil")
    assert "Phil Ivey" in results
    assert len(results) <= 10

def test_vertex_semantic_search():
    """Vertex AI 의미론적 검색 테스트"""
    results = vertex_service.semantic_autocomplete("Junglman")
    assert "Junglemann" in results
    assert all(score > 0.7 for score in results)

def test_api_rate_limiting():
    """Rate limiting 테스트"""
    # 100회 요청
    for i in range(100):
        response = client.get("/api/autocomplete?q=test")
        assert response.status_code == 200

    # 101번째 요청
    response = client.get("/api/autocomplete?q=test")
    assert response.status_code == 429
```

**목표**: 커버리지 ≥85%

### 통합 테스트
```python
def test_autocomplete_end_to_end():
    """E2E 통합 테스트"""
    response = client.get("/api/autocomplete?q=Phil%20Ivy&limit=5")

    assert response.status_code == 200
    assert "Phil Ivey" in response.json()["suggestions"]
    assert response.headers["X-Response-Time-Ms"] < "100"
```

### E2E 테스트 (Playwright)
```typescript
// tests/e2e/autocomplete.spec.ts
test('오타 수정: Phil Ivy → Phil Ivey', async ({ page }) => {
  await page.goto('http://localhost:3000/search')

  // 입력
  await page.fill('[data-testid=search-input]', 'Phil Ivy')

  // 자동완성 드롭다운 대기
  await page.waitForSelector('[data-testid=autocomplete-dropdown]')

  // "Phil Ivey" 제안 확인
  const suggestions = await page.$$('[data-testid=suggestion-item]')
  expect(await suggestions[0].textContent()).toBe('Phil Ivey')

  // 클릭
  await suggestions[0].click()

  // 검색 실행 확인
  await page.waitForURL(/search\?q=Phil\+Ivey/)
})
```

**목표**: 5개 시나리오 100% PASS

---

## 📅 일정

| Phase | 작업 | 기간 | 담당 |
|-------|------|------|------|
| **Phase 0** | 설계 & 검증 | Day 0 (1일) | Claude Code |
| **Phase 1** | 백엔드 API | Day 1 (1일) | Claude Code + fullstack-developer |
| **Phase 2** | 프론트엔드 UI | Day 2-3 (2일) | Claude Code + frontend-developer |
| **Phase 3** | E2E 통합 | Day 4 (1일) | Claude Code + playwright-engineer |
| **Phase 4** | 최종 검증 | Day 5 (1일) | Claude Code + code-reviewer |
| **Phase 5** | 재작업 (조건부) | Day 6-7 (최대 2일) | (필요 시) |

**총 예상 기간**: 5-7일

---

## 💰 비용 분석

### GCP 비용 (월간, 1만 검색 기준)

| 서비스 | 사용량 | 비용/월 |
|--------|--------|---------|
| BigQuery 쿼리 | 1만 쿼리 × 0.01GB | $0.05 |
| Vertex AI Embeddings | 5천 호출 (50% hit) | $0.10 |
| Vertex AI Vector Search | 5천 검색 | $5.00 |
| Cloud Run (FastAPI) | 1만 요청 | $0.20 |
| **총합** | | **$5.35/월** |

**10만 검색 시**: ~$53/월
**100만 검색 시**: ~$530/월

### 개발 비용 (절감)
- **기존 계획** (직접 구현): 2-3주 ($10,000)
- **현재 계획** (Morphic + Vertex AI): 5-7일 ($3,000)
- **절감액**: $7,000 (70% 절감)

---

## 🚨 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|---------|
| Vertex AI 응답 느림 | 중 | 중 | BigQuery 캐시 우선, Vertex AI는 fallback |
| semantic-autocomplete 호환성 | 낮 | 중 | context7-engineer로 사전 검증 |
| 정확도 목표 미달 | 중 | 높 | 수동 큐레이션된 선수명 리스트 준비 |
| Rate limiting 우회 | 낮 | 중 | IP + User-Agent 기반 제한 |

---

## ✅ 수용 기준

### Phase 0 (설계)
- [ ] PRD 승인 완료
- [ ] API 스펙 OpenAPI 문서 작성
- [ ] 기술 스택 호환성 검증 (semantic-autocomplete + MUI v6)

### Phase 1 (백엔드)
- [ ] /api/autocomplete 엔드포인트 구현
- [ ] 단위 테스트 커버리지 ≥85%
- [ ] API 응답 시간 <100ms (p95)
- [ ] 정확도 >85% (100개 샘플 테스트)

### Phase 2 (프론트엔드)
- [ ] PokerCommandSearch 컴포넌트 구현
- [ ] 키보드 네비게이션 작동 (↑↓ Enter Esc)
- [ ] 접근성 검증 WCAG 2.1 AA
- [ ] 모바일 대응 (터치 이벤트)

### Phase 3 (E2E)
- [ ] 5개 E2E 시나리오 PASS (Chrome, Firefox, Mobile)
- [ ] 스크린샷 회귀 테스트 PASS

### Phase 4 (최종 검증)
- [ ] 코드 리뷰 Critical 이슈 0개
- [ ] 보안 감사 High 취약점 0개
- [ ] 성능 프로파일링 통과
- [ ] 문서 작성 완료

---

## 📚 참고 자료

**기술 문서**:
- [Vertex AI TextEmbedding API](https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/get-text-embeddings)
- [semantic-autocomplete GitHub](https://github.com/Mihaiii/semantic-autocomplete)
- [shadcn/ui Command](https://ui.shadcn.com/docs/components/command)

**내부 문서**:
- `AUTOCOMPLETE_WORKFLOW.md` - 상세 워크플로우
- `AUTOCOMPLETE_QUICKSTART.md` - 빠른 시작 가이드
- `CLAUDE.md` - 프로젝트 개요

---

## 🎯 성공 지표 (KPI)

**출시 후 1개월 측정**:

| KPI | 현재 | 목표 | 측정 방법 |
|-----|------|------|---------|
| 검색 성공률 | 60% | 85% | Google Analytics |
| 평균 검색 시간 | 15초 | 5초 | 사용자 세션 분석 |
| 오타 수정 사용률 | 0% | 40% | API 로그 분석 |
| 자동완성 클릭률 | 0% | 60% | 프론트엔드 이벤트 트래킹 |
| NPS | 70 | 85 | 분기별 설문조사 |

---

## ✍️ 승인

**승인 필요**:
- [ ] 제품 책임자 (Aiden Kim)
- [ ] 기술 책임자 (Claude Code)
- [ ] UX 디자이너 (검토 필요)

**승인 후 Phase 1 시작**

---

**PRD 버전**: 1.0.0
**작성일**: 2025-11-19
**마지막 업데이트**: 2025-11-19
**상태**: Draft → **Review 대기**
