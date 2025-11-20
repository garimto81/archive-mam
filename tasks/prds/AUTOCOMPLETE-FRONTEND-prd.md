# PRD: Autocomplete 프론트엔드 (Frontend UI/UX)

**프로젝트**: archive-mam (포커 아카이브 검색 시스템)
**기능명**: Autocomplete Frontend - Smart Search Interface
**버전**: 1.0.0
**작성일**: 2025-11-19
**승인 상태**: Draft → Review 대기

---

## 📋 Executive Summary

포커 아카이브 검색 시스템의 자동완성 **프론트엔드** 구현 PRD입니다. 백엔드 API (`AUTOCOMPLETE-prd.md`)가 완료된 상태이며, 이를 사용자에게 제공할 프로덕션급 UI/UX를 구축합니다.

**핵심 가치**:
- 🎯 직관적 검색: 타이핑만으로 즉시 추천 (<500ms)
- ⚡ 키보드 중심: 마우스 없이 100% 조작 가능
- ♿ 접근성 우선: WCAG 2.1 AA 준수
- 📱 모바일 최적화: 반응형 디자인, 터치 친화적
- 🎨 포커 특화: 카드 아이콘, 칩 색상, 액션 라벨

**기술 스택 결정** (Task 0.1):
- ✅ **Morphic UI** (Next.js 15 + React 19) 선택
- ✅ Vercel AI SDK 4.3.6 (Generative UI 지원)
- ✅ shadcn/ui + Radix UI (접근성 내장)
- ❌ Perplexica 제외 (React 18 고정, TypeScript 미지원)

**예상 개발 기간**: **5-7일**

---

## 🎯 목표

### 비즈니스 목표

1. **사용자 만족도**: NPS 70 → 85 (검색 경험 개선)
2. **검색 성공률**: 60% → 85% (오타 허용)
3. **평균 검색 시간**: 15초 → 5초 (자동완성 활용)
4. **모바일 전환율**: +30% (반응형 디자인)

### 기술 목표

1. **응답 속도**: UI 렌더링 포함 <500ms
2. **접근성**: Lighthouse 접근성 점수 ≥95
3. **성능**: Lighthouse Performance ≥90, LCP <2.5s
4. **번들 크기**: Initial load <200KB (gzipped)

---

## 👥 사용자 스토리

### US-1: 오타 수정 UI

```
As a 포커 코치
I want 오타를 입력해도 올바른 선수명이 추천되길 원함
So that 빠르게 핸드를 찾을 수 있다

예시:
- "Phil Ivy" 입력
  → 드롭다운 표시: "✨ Did you mean? Phil Ivey"
  → Enter 키로 선택
  → 검색 실행
```

**수용 기준**:
- [ ] 오타 추천에 ✨ 아이콘 표시
- [ ] 키보드로 선택 가능 (↓ Enter)
- [ ] 300ms 이내 드롭다운 표시

### US-2: 키보드 네비게이션

```
As a 프로 플레이어
I want 마우스 없이 키보드만으로 검색하고 싶다
So that 빠르고 효율적으로 작업할 수 있다

예시:
- "Phil" 입력
  → ↓ 키: 첫 번째 추천 선택
  → ↑ 키: 이전 추천 선택
  → Enter: 선택 확정
  → Esc: 드롭다운 닫기
```

**수용 기준**:
- [ ] ↑↓ Home End 키 지원
- [ ] Tab 키로 첫 추천 자동완성
- [ ] Ctrl+K로 검색 바 포커스

### US-3: 모바일 터치 인터랙션

```
As a 비디오 편집자 (모바일 사용)
I want 터치로 쉽게 추천을 선택하고 싶다
So that 이동 중에도 검색할 수 있다

예시:
- 모바일에서 "Junglemann" 입력
  → 추천 목록 표시 (44x44px 터치 타겟)
  → 터치로 선택
  → 위로 스와이프: 드롭다운 닫기
```

**수용 기준**:
- [ ] 최소 44x44px 터치 타겟
- [ ] 스와이프 제스처 지원
- [ ] iOS 줌 방지 (16px 최소 폰트)

---

## 🏗️ 아키텍처

### 전체 구조 (Task 0.3 결과)

```
[프론트엔드 - Morphic UI]
Next.js 15 App Router
├── SearchBar.tsx (150 LOC)
│   ├── Input (shadcn/ui)
│   └── AutocompleteDropdown (120 LOC)
│       ├── SuggestionList
│       │   └── SuggestionItem (80 LOC) x5
│       ├── SourceBadge (40 LOC)
│       └── KeyboardHints
│
├── Hooks
│   ├── useAutocomplete (200 LOC)
│   │   └── API Client (100 LOC)
│   ├── useKeyboardNavigation (150 LOC)
│   └── useDebounce (30 LOC)
│
└── State Management
    └── React Hooks (useState + useContext)
        ├── Local: query, dropdown visibility
        ├── Server: API responses (useAutocomplete)
        └── URL: search params

    ↓ API 호출
[백엔드 - FastAPI]
GET /api/autocomplete?q={query}&limit=5
→ Response: { suggestions, source, response_time_ms }
```

### 기술 스택 (Task 0.1 결정)

**Frontend Framework**:
- **Morphic UI** (Next.js 15.2.3 + React 19.0.0)
- **Vercel AI SDK** 4.3.6 (Generative UI, streamUI)
- **TypeScript** 5.3+ (Strict mode)
- **Tailwind CSS** 3.4.1

**UI Components**:
- **shadcn/ui** (Radix UI primitives, 접근성 내장)
- **Framer Motion** (애니메이션)
- **Lucide React** (아이콘)

**State Management**:
- **React Hooks** (useState, useContext)
- 추가 라이브러리 불필요 (Zustand/Redux 제외)
- Server state: useAutocomplete hook (자체 구현)

**Testing**:
- **Jest** (unit tests)
- **React Testing Library** (component tests)
- **Playwright** (E2E tests, 8 browsers)

**Deployment**:
- **Vercel** (CI/CD, Edge Functions, Analytics)

**선택 근거** (Morphic > Perplexica):
| 항목 | Morphic UI | Perplexica |
|------|-----------|-----------|
| Next.js | 15.2.3 ✅ | 14.x ❌ |
| React | 19.0.0 ✅ | 18.x ❌ |
| Generative UI | AI SDK 4.3.6 ✅ | 미지원 ❌ |
| TypeScript | 공식 지원 ✅ | 미지원 ❌ |
| GitHub Stars | 8,300+ | 13,000+ |
| 개발 시간 | 4-5일 | 6-7일 |

**결정**: Morphic UI (최신 기술, 타입 안전성, 30% 시간 단축)

---

## 📊 UI/UX 요구사항 (Task 0.2 결과)

### 주요 사용자 플로우 3가지

#### Flow 1: 오타 수정 플로우

```
사용자 입력: "Phil Ivy"
    ↓ (debounce 300ms)
드롭다운 표시:
  ┌──────────────────────────────────┐
  │ 🔍 Phil Ivy                      │
  ├──────────────────────────────────┤
  │ ✨ Did you mean?                │
  │ → Phil Ivey (Typo corrected)    │  ← Highlighted
  │   Phil Hellmuth                 │
  │   Philip Ng                     │
  └──────────────────────────────────┘
    ↓ (↓ key or click)
선택: "Phil Ivey"
    ↓
검색 실행
```

#### Flow 2: 자동완성 플로우

```
사용자 입력: "Phil"
    ↓ (debounce 300ms)
드롭다운 표시:
  ┌──────────────────────────────────┐
  │ 🔍 Phil                          │
  ├──────────────────────────────────┤
  │ → Phil Ivey                      │  ← Focus
  │   Phil Hellmuth                 │
  │   Philip Ng                     │
  │ ──────────────────────────       │
  │ 💡 Related: #PHIL_IVEY          │
  └──────────────────────────────────┘
    ↓ (Enter)
검색 실행
```

#### Flow 3: 유사어 추천 (Vertex AI)

```
사용자 입력: "hero call"
    ↓ (Vertex AI 검색)
드롭다운 표시:
  ┌──────────────────────────────────┐
  │ 🔍 hero call                     │
  ├──────────────────────────────────┤
  │ → hero call                      │
  │   bluff catch  (AI-suggested)   │
  │   sick call                      │
  │ ──────────────────────────       │
  │ 🤖 AI-powered (92ms)             │
  └──────────────────────────────────┘
```

### 디자인 시스템 (Task 0.2)

**색상 팔레트** (shadcn/ui HSL 기반):
```css
:root {
  --primary: 222.2 47.4% 11.2%;       /* Dark blue */
  --accent: 210 40% 96.1%;            /* Light blue */
  --destructive: 0 84.2% 60.2%;       /* Red */
  --muted-foreground: 215.4 16.3% 46.9%;
}

/* Poker-specific */
:root {
  --poker-chip-white: 0 0% 100%;
  --poker-chip-red: 0 84% 60%;
  --poker-chip-green: 142 71% 45%;
  --highlight-typo: 48 96% 53%;       /* Yellow */
}
```

**타이포그래피**:
- Font Family: Inter (sans-serif)
- SearchInput: 16px (iOS 줌 방지)
- SuggestionItem: 14px
- SourceBadge: 12px (monospace for hints)

**간격 (Tailwind scale)**:
- SearchInput padding: 12px 48px 12px 16px
- Dropdown gap: 8px
- SuggestionItem padding: 12px 16px

**접근성 (WCAG 2.1 AA)**:
- 색상 대비: ≥ 4.5:1 (일반 텍스트)
- 터치 타겟: ≥ 44x44px (모바일)
- ARIA 속성: combobox, listbox, option
- 키보드 전용 조작 가능
- 스크린 리더 지원 (live regions)

### 반응형 디자인

**Breakpoints**:
```css
/* Mobile (default) */
.search-input {
  width: 100%;
  font-size: 16px;  /* Prevents iOS zoom */
}

/* Tablet (768px+) */
@media (min-width: 768px) {
  .search-input {
    max-width: 600px;
  }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
  .search-input {
    max-width: 720px;
  }
}
```

---

## 🧩 컴포넌트 설계 (Task 0.3 결과)

### 핵심 컴포넌트 4개

#### 1. SearchBar (150 LOC)

**Props**:
```typescript
interface SearchBarProps {
  initialQuery?: string;
  onSearch?: (query: string) => void;
  enableAutocomplete?: boolean;
  placeholder?: string;
  className?: string;
}
```

**State**:
- query (string)
- isDropdownOpen (boolean)
- isLoading (boolean)
- error (AutocompleteError | null)
- suggestions (Suggestion[])
- selectedIndex (number)

**Event Handlers**:
- handleInputChange: 300ms debounce → API call
- handleKeyDown: ↑↓ Enter Esc Tab
- handleClear: 입력 초기화
- handleSelectSuggestion: 선택 확정 → 검색 실행

#### 2. AutocompleteDropdown (120 LOC)

**Props**:
```typescript
interface AutocompleteDropdownProps {
  query: string;
  suggestions: Suggestion[];
  selectedIndex: number;
  onSelectSuggestion: (suggestion: Suggestion) => void;
  isLoading: boolean;
  error: AutocompleteError | null;
  source: "bigquery_cache" | "vertex_ai" | "hybrid";
  responseTimeMs: number;
}
```

**Features**:
- Framer Motion 애니메이션 (fade + scale)
- 위치 계산 (fixed position, 8px gap)
- Scroll into view (선택된 항목 자동 스크롤)
- Error state UI (ValidationError, RateLimitError, NetworkError, NoResults)

#### 3. SuggestionItem (80 LOC)

**Props**:
```typescript
interface SuggestionItemProps {
  text: string;
  query: string;  // For highlighting
  isSelected: boolean;
  isTypoCorrected?: boolean;
  onClick: () => void;
  onMouseEnter: () => void;
}
```

**Features**:
- 텍스트 하이라이팅 (매칭된 문자 <mark>)
- 오타 수정 표시 (✨ 아이콘)
- Hover/Selected 상태 (배경색 변경)
- Auto scroll into view

#### 4. SourceBadge (40 LOC)

**Props**:
```typescript
interface SourceBadgeProps {
  source: "bigquery_cache" | "vertex_ai" | "hybrid";
  responseTimeMs: number;
}
```

**Rendering**:
```typescript
const config = {
  bigquery_cache: { icon: "💾", label: "Fast", color: "green" },
  vertex_ai: { icon: "🤖", label: "AI-powered", color: "purple" },
  hybrid: { icon: "🧠", label: "Smart", color: "blue" }
};
```

### 상태 관리 전략

**선택**: React Hooks Only (Option 1)

**근거**:
- ✅ 단순성 (추가 라이브러리 불필요)
- ✅ 성능 (상태 업데이트가 SearchBar 내부로 제한)
- ✅ 번들 크기 절약 (~10KB vs Zustand)
- ✅ Next.js 15 Server Components 호환

**State Scopes**:
- **Local State** (useState): query, dropdown visibility
- **Server State** (useAutocomplete): API 응답, 캐싱
- **URL State** (useSearchParams): 검색 파라미터 (딥 링크)
- **Cache State** (in-memory): 5분 TTL

### 데이터 플로우

```
User Input → Debounce (300ms) → API Call → Cache Check
    ↓
[Cache Hit] → Return cached (< 5ms)
[Cache Miss] → Fetch API → Store cache
    ↓
Response → Update State → Re-render
    ↓
User Selection → Execute Search → Navigate to Results
```

---

## 🚀 API 통합 패턴 (Task 0.3)

### API Client (`lib/api/autocomplete.ts`)

**Features**:
- ✅ Request cancellation (AbortController)
- ✅ Timeout handling (5s default)
- ✅ Retry logic (2 retries, exponential backoff)
- ✅ In-memory caching (5-minute TTL)
- ✅ Error classification (validation, rate limit, network, server, timeout)

**Implementation**:
```typescript
export async function fetchAutocomplete(
  query: string,
  options?: AutocompleteOptions
): Promise<AutocompleteResponse> {
  // 1. Validate query
  if (query.length < 2) {
    throw new ValidationError("Query must be at least 2 characters");
  }

  // 2. Check cache
  const cached = cache.get(query);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }

  // 3. Fetch with abort + timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options?.timeout ?? 5000);

  try {
    const response = await fetch(
      `${API_URL}/api/autocomplete?q=${encodeURIComponent(query)}&limit=${options?.limit ?? 5}`,
      { signal: controller.signal }
    );

    clearTimeout(timeoutId);

    // 4. Handle errors
    if (response.status === 422) {
      throw new ValidationError("Invalid query format");
    }
    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get("Retry-After") || "60");
      throw new RateLimitError(retryAfter);
    }
    if (!response.ok) {
      throw new ServerError(`HTTP ${response.status}`);
    }

    // 5. Parse + cache
    const data = await response.json();
    cache.set(query, { data, timestamp: Date.now() });

    return data;

  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof DOMException && error.name === "AbortError") {
      throw new TimeoutError("Request timed out");
    }
    if (error instanceof TypeError) {
      throw new NetworkError("Network error");
    }
    throw error;
  }
}
```

---

## ⚡ 성능 요구사항

### Core Web Vitals 목표

| 메트릭 | 목표 | 측정 방법 |
|--------|------|----------|
| **Initial Load** | <3초 | Lighthouse Performance ≥90 |
| **Autocomplete Response** | <500ms | API + rendering |
| **LCP** | <2.5초 | Largest Contentful Paint |
| **CLS** | <0.1 | Cumulative Layout Shift |
| **FID** | <100ms | First Input Delay |
| **TTI** | <3.8초 | Time to Interactive |
| **60 FPS Scroll** | 100% | DevTools Performance |

### 번들 크기 최적화

**Target**:
```
Initial Load (gzipped):    < 200 KB
├── Next.js runtime:       ~ 75 KB
├── React 19:              ~ 42 KB
├── SearchBar + Dropdown:  ~ 18 KB
└── Utilities:             ~ 10 KB
                           ─────────
Total:                     ~ 145 KB ✅
```

**Techniques**:
- Dynamic imports (VideoPlayer, FilterSidebar)
- Image optimization (WebP/AVIF, next/image)
- Code splitting (per route)
- Tree shaking (Tailwind CSS JIT)
- Compression (Brotli, Gzip)

### 렌더링 최적화

- React.memo (SuggestionItem)
- useMemo (highlightMatch)
- useCallback (event handlers)
- Virtual scrolling (100+ 결과 시)
- requestIdleCallback (prefetching)

---

## 🧪 테스트 전략

### Unit Tests (Jest)

**Coverage Target**: ≥80%

```typescript
// __tests__/hooks/useDebounce.test.ts
test("debounces value changes", async () => {
  const { result, rerender } = renderHook(
    ({ value, delay }) => useDebounce(value, delay),
    { initialProps: { value: "test", delay: 300 } }
  );

  expect(result.current).toBe("test");
  rerender({ value: "new", delay: 300 });
  expect(result.current).toBe("test");  // Still old

  await waitFor(() => expect(result.current).toBe("new"), {
    timeout: 400
  });
});
```

### Component Tests (React Testing Library)

```typescript
// __tests__/components/SearchBar.test.tsx
test("shows dropdown when typing", async () => {
  render(<SearchBar />);

  const input = screen.getByRole("searchbox");
  fireEvent.change(input, { target: { value: "Phil" } });

  await waitFor(() => {
    expect(screen.getByRole("listbox")).toBeInTheDocument();
  });
});
```

### E2E Tests (Playwright)

**Test Suites**:
1. Autocomplete 기본 플로우 (5 scenarios)
2. 키보드 네비게이션 (8 key combinations)
3. 에러 핸들링 (4 error types)
4. 반응형 디자인 (3 breakpoints)
5. 크로스 브라우저 (Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari)

```typescript
// e2e/autocomplete.spec.ts
test("오타 수정: Phil Ivy → Phil Ivey", async ({ page }) => {
  await page.goto("/search");

  const input = page.getByRole("searchbox");
  await input.fill("Phil Ivy");

  await expect(page.getByRole("listbox")).toBeVisible();
  await expect(page.getByText("Phil Ivey")).toBeVisible();

  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");

  await expect(input).toHaveValue("Phil Ivey");
});
```

---

## 📅 구현 로드맵 (7 Days)

### Phase 1: Foundation (Day 1-2)

**Day 1**:
- [x] Next.js 15 + React 19 프로젝트 생성
- [x] shadcn/ui 초기화 (button, input, badge, skeleton)
- [x] Tailwind CSS 설정
- [x] 환경 변수 설정 (.env.local)
- [x] 프로젝트 구조 생성

**Day 2**:
- [ ] SearchBar 컴포넌트 구현 (150 LOC)
- [ ] AutocompleteDropdown 컴포넌트 (120 LOC)
- [ ] Basic styling (Light mode)

### Phase 2: Core Components (Day 3-4)

**Day 3**:
- [ ] SuggestionItem 컴포넌트 (80 LOC)
  - Text highlighting
  - Typo correction indicator
- [ ] SourceBadge 컴포넌트 (40 LOC)
- [ ] KeyboardHints 컴포넌트

**Day 4**:
- [ ] useAutocomplete hook (200 LOC)
- [ ] API client (100 LOC)
  - Fetch wrapper
  - Error handling
  - Caching
- [ ] useDebounce hook (30 LOC)

### Phase 3: Hooks + API (Day 4-5)

**Day 4 (continued)**:
- [ ] useKeyboardNavigation hook (150 LOC)
- [ ] useClickOutside hook
- [ ] useFocusManagement hook

**Day 5**:
- [ ] Error state components
  - ValidationError
  - RateLimitError
  - NetworkError
  - NoResults
- [ ] Loading state (Skeleton UI)

### Phase 4: Accessibility (Day 5-6)

**Day 5 (continued)**:
- [ ] ARIA 속성 추가 (combobox, listbox, option)
- [ ] Keyboard navigation 완성
- [ ] Focus management

**Day 6**:
- [ ] Screen reader 지원 (live regions)
- [ ] Color contrast 검증 (≥ 4.5:1)
- [ ] 키보드 전용 조작 테스트

### Phase 5: Performance (Day 6)

- [ ] React.memo 적용
- [ ] useMemo/useCallback 최적화
- [ ] Code splitting (dynamic imports)
- [ ] Image optimization (WebP/AVIF)
- [ ] Lighthouse 테스트 (Performance ≥90)

### Phase 6: Testing (Day 7)

**Morning**:
- [ ] Unit tests (hooks)
- [ ] Component tests (RTL)
- [ ] 80%+ coverage 달성

**Afternoon**:
- [ ] E2E tests (Playwright)
  - 5 core scenarios
  - Cross-browser testing
- [ ] Accessibility tests (axe-core)

### Phase 7: Deployment (Day 7)

**Evening**:
- [ ] Vercel 배포
- [ ] 환경 변수 설정
- [ ] Analytics 설정 (Vercel Analytics + Speed Insights)
- [ ] Production smoke tests

---

## 🔒 보안 요구사항

### Input Validation (프론트엔드)

```typescript
function validateQuery(query: string): boolean {
  // 1. Length check
  if (query.length < 2 || query.length > 100) {
    return false;
  }

  // 2. Character whitelist
  const allowedChars = /^[a-zA-Z0-9\s\-]+$/;
  if (!allowedChars.test(query)) {
    return false;
  }

  return true;
}
```

### XSS Prevention

- React 기본 escaping 사용 (dangerouslySetInnerHTML 금지)
- 사용자 입력 sanitization (DOMPurify, 필요 시)
- CSP 헤더 설정 (Vercel)

### CORS

```typescript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: "/api/:path*",
        headers: [
          { key: "Access-Control-Allow-Origin", value: "https://morphic.archive-mam.com" },
          { key: "Access-Control-Allow-Methods", value: "GET" },
        ],
      },
    ];
  },
};
```

---

## 💰 비용 분석

### 프론트엔드 비용 (월간)

| 항목 | 비용/월 |
|------|---------|
| **Vercel Pro** (배포 + Analytics) | $20 |
| **Vercel Edge Functions** (1만 요청) | $0 (Free tier) |
| **Bandwidth** (10GB) | $0 (Free tier) |
| **Total** | **$20/월** |

**개발 비용 절감**:
- **Perplexica 직접 개발**: 6-7일 ($4,000)
- **Morphic UI 활용**: 5-7일 ($3,000)
- **절감액**: $1,000 (25% 절감)

---

## 📊 성공 지표 (KPI)

**출시 후 1개월 측정**:

| KPI | 현재 | 목표 | 측정 방법 |
|-----|------|------|---------  |
| **Lighthouse Performance** | - | ≥90 | Vercel Analytics |
| **Lighthouse Accessibility** | - | ≥95 | axe-core + manual |
| **Autocomplete 사용률** | 0% | 60% | 프론트엔드 이벤트 트래킹 |
| **모바일 트래픽** | 20% | 35% | Google Analytics |
| **평균 검색 시간** | 15초 | 5초 | 사용자 세션 분석 |
| **NPS** | 70 | 85 | 분기별 설문조사 |

---

## 🚨 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|---------  |
| **Morphic UI 버그** | 낮 | 중 | Fallback to vanilla shadcn/ui |
| **성능 목표 미달** | 중 | 높 | Code splitting, lazy loading |
| **접근성 테스트 실패** | 낮 | 중 | Early axe-core 통합 |
| **Vercel 비용 초과** | 낮 | 낮 | Edge Functions 모니터링 |

---

## ✅ 수용 기준

### Phase 1 (Foundation)
- [ ] Next.js 15 + React 19 프로젝트 생성
- [ ] shadcn/ui 초기화
- [ ] Tailwind CSS 설정
- [ ] 환경 변수 설정

### Phase 2 (Core Components)
- [ ] SearchBar 컴포넌트 구현
- [ ] AutocompleteDropdown 구현
- [ ] SuggestionItem 구현
- [ ] SourceBadge 구현

### Phase 3 (Hooks + API)
- [ ] useAutocomplete hook 구현
- [ ] API client 구현 (cache, retry, timeout)
- [ ] useKeyboardNavigation 구현

### Phase 4 (Accessibility)
- [ ] WCAG 2.1 AA 준수
- [ ] Lighthouse 접근성 ≥95
- [ ] 키보드 전용 조작 가능
- [ ] Screen reader 테스트 (NVDA, JAWS, VoiceOver)

### Phase 5 (Performance)
- [ ] Lighthouse Performance ≥90
- [ ] LCP <2.5s
- [ ] CLS <0.1
- [ ] 번들 크기 <200KB (gzipped)

### Phase 6 (Testing)
- [ ] Unit 테스트 커버리지 ≥80%
- [ ] Component 테스트 PASS
- [ ] E2E 테스트 5개 시나리오 PASS
- [ ] Cross-browser 테스트 (Chrome, Firefox, Safari)

### Phase 7 (Deployment)
- [ ] Vercel 배포 성공
- [ ] Production smoke tests PASS
- [ ] Analytics 설정 완료

---

## 📚 참고 자료

### 기술 문서

- [Next.js 15 Documentation](https://nextjs.org/docs)
- [Morphic UI GitHub](https://github.com/miurla/morphic)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)
- [React 19 Release Notes](https://react.dev/blog/2024/04/25/react-19)

### 접근성

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices - Combobox](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)

### 내부 문서

- `AUTOCOMPLETE-prd.md` - 백엔드 PRD
- `AUTOCOMPLETE-FRONTEND-UX-REQUIREMENTS.md` - Task 0.2 산출물
- `AUTOCOMPLETE-FRONTEND-ARCHITECTURE.md` - Task 0.3 산출물
- `AUTOCOMPLETE_WORKFLOW.md` - 전체 워크플로우

---

## ✍️ 승인

**승인 필요**:
- [ ] 제품 책임자 (Aiden Kim)
- [ ] 기술 책임자 (Claude Code)
- [ ] UX 디자이너 (검토 필요)
- [ ] 백엔드 팀 (API 연동 확인)

**승인 후 Phase 1 시작**

---

**PRD 버전**: 1.0.0
**작성일**: 2025-11-19
**마지막 업데이트**: 2025-11-19
**상태**: Draft → **Review 대기**
**예상 개발 기간**: **5-7일**
**예상 비용**: **$3,000** (개발) + **$20/월** (운영)
