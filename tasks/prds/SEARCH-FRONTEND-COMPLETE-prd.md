# PRD: Smart Hybrid Search 프론트엔드 완전 구현

**프로젝트**: archive-mam (포커 아카이브 검색 시스템)
**기능명**: Smart Hybrid Search Frontend - Complete Implementation
**버전**: 2.0.0 (Updated)
**작성일**: 2025-01-19
**업데이트**: Vertex AI + Firestore 백엔드 기반
**승인 상태**: 실행 준비

---

## 📋 Executive Summary

포커 아카이브 검색 시스템의 **프론트엔드 전체**를 구현합니다. 백엔드는 **Vertex AI Vector Search + Firestore**를 사용하며, 프론트엔드는 이를 활용한 검색 경험을 제공합니다.

**현재 완료 상태**:
- ✅ Phase 1: 기초 구조 완료 (SearchBar, Autocomplete, Hooks, API Client)
- ⏳ Phase 2-6: 미완성

**핵심 가치**:
- 🔍 **Hybrid Search**: Vector (의미) + Metadata (필터) 동시 검색
- 🎯 **Autocomplete**: 오타 보정 ("pil" → "Phil Hellmuth")
- ⚡ **실시간 검색**: <500ms 응답
- 📱 **모바일 최적화**: 반응형 디자인
- ♿ **접근성**: WCAG 2.1 AA 준수

---

## 🏗️ 백엔드 아키텍처 (확정)

```
[데이터 소스]
ATI 분석 DB (별도 프로젝트에서 제공)
    ↓
[GCP Search Engine]
├── Firestore (메타데이터 저장)
│   - players, game_logic, tags
│   - Composite Index 최적화
│   - 실시간 필터링
│
└── Vertex AI Vector Search
    - TextEmbedding-004 (768차원)
    - Semantic Search (유사도 검색)
    - ScaNN 알고리즘
    ↓
[Backend API]
FastAPI (Cloud Run)
- GET /api/autocomplete?q={query}
- GET /api/search?q={query}&filters={...}
- GET /api/hands/{id}
    ↓
[Frontend]
Next.js 15 + shadcn/ui (현재 프로젝트)
```

**결정 사유** (docs/search_engine_fair_comparison.md):
- ✅ 99.9% SLA (엔터프라이즈 신뢰성)
- ✅ DevOps 인건비 제로 (Managed Service)
- ✅ 검증된 사례 (Lowe's, Shopify)
- ✅ GCP 통합 (이미 사용 중)

---

## 🎯 목표

### 비즈니스 목표

1. **사용자 만족도**: NPS 70 → 85
2. **검색 성공률**: 60% → 85% (오타 허용)
3. **평균 검색 시간**: 15초 → 5초
4. **모바일 전환율**: +30%

### 기술 목표

1. **응답 속도**: 검색 <500ms, Autocomplete <100ms
2. **접근성**: Lighthouse 접근성 ≥95
3. **성능**: Lighthouse Performance ≥90
4. **번들 크기**: Initial load <200KB (gzipped)

---

## 👥 사용자 스토리

### US-1: 오타 보정 Autocomplete

```
As a 포커 코치
I want "pil" 입력 시 "Phil Hellmuth" 추천을 받고 싶다
So that 정확한 이름을 몰라도 검색할 수 있다

수용 기준:
- [ ] 2글자 이상 입력 시 Autocomplete 시작
- [ ] 오타/별명 자동 보정 (Firestore entities 컬렉션)
- [ ] 응답 시간 <100ms
- [ ] 키보드 네비게이션 (↑↓ Enter Esc)
```

### US-2: Hybrid Search

```
As a 포커 플레이어
I want "bluffing" + "Phil Hellmuth" + "AA" 필터를 동시에 검색하고 싶다
So that 정확한 핸드를 빠르게 찾을 수 있다

수용 기준:
- [ ] Vector Search: "bluffing" 의미론적 검색
- [ ] Metadata Filter: Players, Cards, Pot Size
- [ ] 결과 병합 (RRF - Reciprocal Rank Fusion)
- [ ] 응답 시간 <500ms
```

### US-3: 검색 결과 표시

```
As a 비디오 편집자
I want 검색 결과를 카드 형태로 보고 싶다
So that 원하는 핸드를 빠르게 선택할 수 있다

수용 기준:
- [ ] 카드 레이아웃 (썸네일 + 요약)
- [ ] 페이지네이션 (무한 스크롤 or 버튼)
- [ ] 정렬 옵션 (관련도, 날짜, Pot Size)
- [ ] 로딩 스켈레톤
```

### US-4: 고급 필터

```
As a 포커 코치
I want GUI로 카드를 선택하고 싶다
So that 텍스트 입력 없이 필터링할 수 있다

수용 기준:
- [ ] 카드 선택기 (A♠ K♥ Q♦ J♣)
- [ ] Pot Size Range Slider
- [ ] 토너먼트 선택 (드롭다운)
- [ ] 태그 다중 선택
```

### US-5: 비디오 통합

```
As a 포커 플레이어
I want 검색 결과에서 바로 영상을 볼 수 있다
So that 별도 다운로드 없이 확인할 수 있다

수용 기준:
- [ ] 비디오 플레이어 내장
- [ ] 핸드 구간만 재생 (start_seconds ~ end_seconds)
- [ ] 재생 속도 조절
- [ ] 전체 화면 지원
```

---

## 🛠️ 기술 스택

### Frontend

- **Framework**: Next.js 15.2.3 + React 19.0.0
- **UI Library**: shadcn/ui + Radix UI
- **Styling**: Tailwind CSS 3.4.1
- **Animation**: Framer Motion 12.23.24
- **Icons**: Lucide React 0.554.0
- **State**: React Hooks (useState, useEffect, useContext)
- **Video**: React Player or Video.js

### Backend API (제공됨)

- **Framework**: FastAPI (Python 3.11)
- **Runtime**: Cloud Run (Serverless)
- **Database**: Firestore
- **Vector Search**: Vertex AI Vector Search

---

## 📐 UI/UX 설계

### 레이아웃 구조

```
┌─────────────────────────────────────────────┐
│         Header (Logo + User Menu)          │
├─────────────────────────────────────────────┤
│                                             │
│          Search Bar (Autocomplete)          │
│    [    "Phil Hellmuth bluffing AA"    ]    │
│              ↓ (Dropdown)                   │
│    ┌─────────────────────────────┐          │
│    │ ✨ Phil Hellmuth (Player)   │          │
│    │    Phil Laak (Player)       │          │
│    │    Bluffing (Tag)           │          │
│    └─────────────────────────────┘          │
│                                             │
├──────────────┬──────────────────────────────┤
│   Filters    │    Search Results            │
│              │                              │
│ ☑ Players    │  ┌──────────────────┐        │
│   - Phil     │  │ [Thumbnail]      │        │
│   - Daniel   │  │ Phil vs Daniel   │        │
│              │  │ River bluff...   │        │
│ ☑ Cards      │  │ Pot: $2.5M       │        │
│   [A♠][K♥]   │  └──────────────────┘        │
│              │                              │
│ ☑ Pot Size   │  ┌──────────────────┐        │
│   [====|====] │  │ [Thumbnail]      │        │
│   $0 - $5M   │  │ ...              │        │
│              │  └──────────────────┘        │
│ ☑ Tournament │                              │
│   WSOP 2024  │  [Load More]                 │
│              │                              │
└──────────────┴──────────────────────────────┘
│                 Footer                      │
└─────────────────────────────────────────────┘
```

### 컴포넌트 구조

```
src/app/
├── layout.tsx (Root Layout)
├── page.tsx (Home - Redirect to /search)
├── search/
│   ├── page.tsx (Main Search Page) ⭐
│   └── [id]/
│       └── page.tsx (Hand Detail Page)
│
src/components/
├── search/
│   ├── SearchBar.tsx ✅ (완료)
│   ├── AutocompleteDropdown.tsx ✅ (완료)
│   ├── SuggestionItem.tsx ✅ (완료)
│   ├── SearchResults.tsx ⏳ (신규)
│   ├── HandCard.tsx ⏳ (신규)
│   ├── Pagination.tsx ⏳ (신규)
│   └── EmptyState.tsx ⏳ (신규)
│
├── filters/
│   ├── FilterPanel.tsx ⏳ (신규)
│   ├── CardSelector.tsx ⏳ (신규)
│   ├── PotSizeSlider.tsx ⏳ (신규)
│   ├── TournamentSelect.tsx ⏳ (신규)
│   └── TagsSelect.tsx ⏳ (신규)
│
├── video/
│   ├── VideoPlayer.tsx ⏳ (신규)
│   └── HandTimeline.tsx ⏳ (신규)
│
└── layout/
    ├── Header.tsx ⏳ (신규)
    └── Footer.tsx ⏳ (신규)
```

---

## 🔌 API 통합

### API Endpoints (백엔드 제공)

#### 1. Autocomplete

```typescript
GET /api/autocomplete?q={query}&limit=5

Response:
{
  "suggestions": [
    {
      "entity_id": "player_phil_hellmuth",
      "canonical_name": "Phil Hellmuth",
      "type": "PLAYER"
    }
  ],
  "query": "pil",
  "source": "firestore_entities",
  "response_time_ms": 45
}
```

#### 2. Hybrid Search

```typescript
GET /api/search?q={query}&filters={...}&page=1&limit=20

Request Query Params:
- q: 텍스트 쿼리 (예: "bluffing")
- filters: JSON 필터 (예: {"players": ["player_phil_hellmuth"], "hole_cards": ["Ah", "Ac"]})
- page: 페이지 번호 (기본: 1)
- limit: 페이지 크기 (기본: 20, 최대: 100)

Response:
{
  "results": [
    {
      "hand_id": "h_wsop24_ev1_17150020",
      "description": "Phil Hellmuth bluffs with pocket aces...",
      "summary_text": "...",
      "hero_name": "Phil Hellmuth",
      "villain_name": "Daniel Negreanu",
      "hole_cards": ["Ah", "Ac"],
      "pot_final": 2500000,
      "video_url": "gs://...",
      "start_seconds": 1420.5,
      "end_seconds": 1580.2,
      "thumbnail_url": "https://...",
      "score": 0.92  // Hybrid search score
    }
  ],
  "total": 47,
  "page": 1,
  "pages": 3,
  "query_time_ms": 285
}
```

#### 3. Hand Detail

```typescript
GET /api/hands/{hand_id}

Response:
{
  "hand_id": "h_wsop24_ev1_17150020",
  "video_ref_id": "wsop24_ev1_part1",
  "media_refs": {
    "master_gcs_uri": "gs://...",
    "time_range": {
      "start_seconds": 1420.5,
      "end_seconds": 1580.2,
      "duration_seconds": 159.7
    }
  },
  "game_logic": {
    "stage": "Final Table",
    "is_showdown": true,
    "winning_hand_rank": "Full House",
    "pot_final": 2500000,
    "board": {
      "flop": ["As", "Td", "2h"],
      "turn": ["Kh"],
      "river": ["2c"]
    }
  },
  "players": [
    {
      "entity_id": "player_phil_hellmuth",
      "display_name": "Phil Hellmuth",
      "position": "BTN",
      "hole_cards": ["Ah", "Ac"],
      "is_winner": false
    }
  ],
  "semantics": {
    "summary_text": "...",
    "mood_tags": ["Tilt", "Bad Beat"]
  }
}
```

---

## 🎨 디자인 시스템

### Colors (Poker Theme)

```typescript
// tailwind.config.ts (이미 적용됨)
colors: {
  poker: {
    chip: {
      white: "hsl(0, 0%, 100%)",
      red: "hsl(0, 84%, 60%)",
      green: "hsl(142, 71%, 45%)",
      blue: "hsl(210, 100%, 56%)",
      black: "hsl(0, 0%, 13%)",
      purple: "hsl(271, 76%, 53%)",
      yellow: "hsl(48, 96%, 53%)",
      orange: "hsl(25, 95%, 53%)"
    },
    suit: {
      spade: "hsl(0, 0%, 13%)",    // ♠
      heart: "hsl(0, 84%, 60%)",    // ♥
      diamond: "hsl(210, 100%, 56%)", // ♦
      club: "hsl(142, 71%, 45%)"    // ♣
    }
  },
  highlight: {
    typo: "hsl(48, 96%, 53%)",  // 오타 보정
    match: "hsl(142, 71%, 45%)" // 매칭
  }
}
```

### Typography

```typescript
// Font families (Geist Sans + Geist Mono)
font-sans: 본문, UI
font-mono: 코드, 통계

// Sizes
text-xs: 12px (메타데이터)
text-sm: 14px (보조 텍스트)
text-base: 16px (본문)
text-lg: 18px (부제목)
text-xl: 20px (제목)
text-2xl: 24px (페이지 제목)
```

---

## 📊 성능 목표

| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| **First Contentful Paint (FCP)** | <1.8s | Lighthouse |
| **Largest Contentful Paint (LCP)** | <2.5s | Lighthouse |
| **Time to Interactive (TTI)** | <3.8s | Lighthouse |
| **Total Blocking Time (TBT)** | <200ms | Lighthouse |
| **Cumulative Layout Shift (CLS)** | <0.1 | Lighthouse |
| **API Response Time** | <500ms | Network Tab |
| **Autocomplete Response** | <100ms | Network Tab |

---

## ♿ 접근성 요구사항

### WCAG 2.1 AA 준수

1. **키보드 네비게이션**
   - Tab, Shift+Tab: 포커스 이동
   - ↑↓: Autocomplete 선택
   - Enter: 선택/검색
   - Esc: Dropdown 닫기

2. **ARIA 속성**
   - `role="combobox"` (SearchBar)
   - `role="listbox"` (Dropdown)
   - `role="option"` (Suggestion)
   - `aria-expanded`, `aria-selected`

3. **Color Contrast**
   - 텍스트: 최소 4.5:1
   - 큰 텍스트: 최소 3:1
   - UI 컴포넌트: 최소 3:1

4. **Screen Reader**
   - `aria-live="polite"` (검색 결과 업데이트)
   - `aria-label` (아이콘 버튼)
   - `alt` 텍스트 (이미지)

---

## 🧪 테스트 계획

### Unit Tests (Jest + React Testing Library)

```typescript
// src/components/search/__tests__/SearchBar.test.tsx
describe('SearchBar', () => {
  test('오타 입력 시 자동완성 표시', async () => {
    render(<SearchBar />);
    const input = screen.getByRole('combobox');

    await user.type(input, 'pil');

    await waitFor(() => {
      expect(screen.getByText('Phil Hellmuth')).toBeInTheDocument();
    });
  });

  test('↓ 키로 제안 선택', async () => {
    // ...
  });
});
```

**목표**: 커버리지 ≥80%

### Integration Tests (MSW)

```typescript
// Mock API 응답
import { rest } from 'msw';

const handlers = [
  rest.get('/api/autocomplete', (req, res, ctx) => {
    return res(
      ctx.json({
        suggestions: [{ canonical_name: 'Phil Hellmuth', type: 'PLAYER' }]
      })
    );
  })
];
```

### E2E Tests (Playwright)

```typescript
// tests/e2e/search.spec.ts
test('전체 검색 플로우', async ({ page }) => {
  await page.goto('http://localhost:3000/search');

  // 1. Autocomplete
  await page.fill('[data-testid=search-input]', 'pil');
  await page.click('text=Phil Hellmuth');

  // 2. 필터 추가
  await page.click('[data-testid=filter-cards]');
  await page.click('text=A♠');
  await page.click('text=A♣');

  // 3. 검색 실행
  await page.click('[data-testid=search-button]');

  // 4. 결과 확인
  await expect(page.locator('[data-testid=search-results]')).toBeVisible();
  await expect(page.locator('[data-testid=hand-card]').first()).toContainText('Phil Hellmuth');
});
```

**목표**: 5개 시나리오 100% PASS

---

## 📅 구현 일정

### Phase 2: 백엔드 API 연동 (Day 8-10, 3일)
- [ ] API Client 완성 (Firestore + Vertex AI)
- [ ] 환경변수 설정 (.env.local)
- [ ] Error Handling 강화
- [ ] API Mocking (MSW)

### Phase 3: 검색 결과 페이지 (Day 11-13, 3일)
- [ ] SearchResults 컴포넌트
- [ ] HandCard 컴포넌트
- [ ] Pagination 컴포넌트
- [ ] EmptyState 컴포넌트
- [ ] Loading Skeleton

### Phase 4: 고급 필터 UI (Day 14-16, 3일)
- [ ] FilterPanel 컴포넌트
- [ ] CardSelector (카드 선택기)
- [ ] PotSizeSlider (범위 슬라이더)
- [ ] TournamentSelect (드롭다운)
- [ ] TagsSelect (다중 선택)

### Phase 5: 비디오 통합 (Day 17-19, 3일)
- [ ] VideoPlayer 컴포넌트
- [ ] HandTimeline (타임라인 마커)
- [ ] Video.js or React Player 통합
- [ ] 재생 속도 조절
- [ ] 전체 화면

### Phase 6: 테스트 + 최적화 (Day 20-22, 3일)
- [ ] Unit Tests (Jest)
- [ ] Integration Tests (MSW)
- [ ] E2E Tests (Playwright)
- [ ] Performance Optimization
- [ ] Lighthouse 점수 검증

### Phase 7: 배포 (Day 23-24, 2일)
- [ ] Vercel 배포 설정
- [ ] 환경변수 Production 설정
- [ ] Domain 연결
- [ ] Analytics 설정 (Google Analytics)

**총 예상 기간**: **17일** (Phase 1 제외)

---

## 💰 비용 분석

### Frontend Hosting (Vercel)

| 플랜 | 비용/월 | 제공 사항 |
|------|---------|----------|
| Hobby | $0 | 100GB 대역폭, 1 팀원 |
| Pro | $20 | 1TB 대역폭, 무제한 팀원 |

**예상**: Hobby 플랜 ($0)

### Backend API (Cloud Run)

| 항목 | 비용/월 |
|------|---------|
| Firestore (메타데이터) | $100 |
| Vertex AI Vector Search | $900 |
| Cloud Run (Backend) | $120 |
| **총 비용** | **$1,120** |

**총 프로젝트 비용**: **$1,120/월** (Frontend $0 + Backend $1,120)

---

## 🚨 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|----------|
| **Vertex AI 응답 느림** | 중 | 높 | Firestore 캐시, 프리페칭 |
| **복잡한 필터 UI** | 중 | 중 | shadcn/ui 활용, 단순화 |
| **비디오 재생 문제** | 중 | 중 | 검증된 라이브러리 (Video.js) |
| **성능 목표 미달** | 낮 | 중 | Code Splitting, 이미지 최적화 |
| **접근성 미준수** | 낮 | 중 | Lighthouse CI, axe DevTools |

---

## ✅ 수용 기준

### Phase 2 (백엔드 연동)
- [ ] Autocomplete API 연동 성공
- [ ] Search API 연동 성공
- [ ] Error Handling 동작 확인

### Phase 3 (검색 결과)
- [ ] 검색 결과 20개 표시
- [ ] 페이지네이션 동작
- [ ] Loading Skeleton 표시

### Phase 4 (고급 필터)
- [ ] 카드 선택기 동작
- [ ] Pot Size Slider 동작
- [ ] 필터 적용 시 검색 재실행

### Phase 5 (비디오)
- [ ] 비디오 재생 동작
- [ ] 핸드 구간만 재생 (start_seconds ~ end_seconds)
- [ ] 전체 화면 지원

### Phase 6 (테스트)
- [ ] Unit Test 커버리지 ≥80%
- [ ] E2E 테스트 5개 PASS
- [ ] Lighthouse Performance ≥90
- [ ] Lighthouse Accessibility ≥95

### Phase 7 (배포)
- [ ] Vercel 배포 성공
- [ ] Production 환경 동작 확인
- [ ] Analytics 데이터 수집 확인

---

## 📚 참고 자료

### 내부 문서
- `AUTOCOMPLETE-FRONTEND-prd.md` - 기존 PRD
- `search_engine_fair_comparison.md` - 백엔드 솔루션 비교
- `QUICK_VERIFICATION.md` - 검증 가이드

### 기술 문서
- [Next.js 15 Docs](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/docs/components)
- [Vertex AI Vector Search](https://cloud.google.com/vertex-ai/docs/vector-search)
- [Firestore](https://firebase.google.com/docs/firestore)

---

**PRD 버전**: 2.0.0
**작성일**: 2025-01-19
**상태**: **실행 준비 완료**
