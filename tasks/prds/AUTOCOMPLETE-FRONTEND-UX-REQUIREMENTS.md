# 프론트엔드 UI/UX 요구사항 - 포커 아카이브 Autocomplete

**문서 버전**: 1.0.0
**작성일**: 2025-11-19
**프로젝트**: archive-mam (포커 아카이브 검색 시스템)
**목적**: 자동완성 기능의 프론트엔드 UI/UX 요구사항 정의
**기술 스택**: Morphic UI (Next.js 15 + React 19) + Vercel AI SDK 4.3.6 + shadcn/ui

---

## Table of Contents

1. [프로젝트 컨텍스트](#1-프로젝트-컨텍스트)
2. [사용자 플로우](#2-사용자-플로우)
3. [컴포넌트 계층 구조](#3-컴포넌트-계층-구조)
4. [인터랙션 패턴](#4-인터랙션-패턴)
5. [디자인 시스템](#5-디자인-시스템)
6. [접근성](#6-접근성)
7. [반응형 디자인](#7-반응형-디자인)
8. [성능 요구사항](#8-성능-요구사항)
9. [에러 핸들링](#9-에러-핸들링)
10. [구현 가이드라인](#10-구현-가이드라인)

---

## 1. 프로젝트 컨텍스트

### 1.1 개요

포커 아카이브 검색 시스템의 자동완성 기능으로, 사용자가 플레이어 이름, 액션 키워드, 핸드 태그를 빠르게 찾을 수 있도록 돕는 스마트 입력 인터페이스입니다.

### 1.2 핵심 기능

- **오타 수정**: "Phil Ivy" → "Phil Ivey" 자동 제안
- **실시간 추천**: 타이핑 중 <500ms 응답
- **의미론적 검색**: "hero call" 입력 시 "bluff catch", "sick call" 추천
- **키워드 하이라이팅**: 매칭된 문자 강조 표시
- **소스 표시**: 캐시/AI 검색 출처 표시

### 1.3 백엔드 API

```
GET /api/autocomplete?q={query}&limit=5

Response:
{
  "suggestions": ["Phil Ivey", "Phil Hellmuth", "Philip Ng"],
  "query": "Phil",
  "source": "bigquery_cache",
  "response_time_ms": 45,
  "total": 3
}
```

### 1.4 주요 사용자

| 페르소나 | 사용 목적 | 우선순위 |
|---------|---------|---------|
| **포커 코치** | 특정 플레이어의 핸드 분석 | 1 |
| **프로 플레이어** | 자신의 과거 핸드 복습 | 1 |
| **비디오 편집자** | 대회별/플레이어별 클립 검색 | 2 |
| **포커 팬** | 유명 핸드 탐색 | 3 |

---

## 2. 사용자 플로우

### 2.1 주요 플로우 3가지

#### Flow 1: 오타 수정 플로우

```
사용자 입력: "Phil Ivy"
    ↓ (debounce 300ms)
드롭다운 표시:
  ┌──────────────────────────────────┐
  │ 🔍 Phil Ivy                      │
  ├──────────────────────────────────┤
  │ ✨ Did you mean?                │
  │ → Phil Ivey (Typo corrected)    │  ← Highlighted suggestion
  │   Phil Hellmuth                 │
  │   Philip Ng                     │
  └──────────────────────────────────┘
    ↓ (↓ key or click)
선택: "Phil Ivey"
    ↓
검색 실행
```

**상태 머신**:
```
IDLE → TYPING (keydown) → DEBOUNCING (300ms) → FETCHING → SHOWING_RESULTS
  ↑                                                              ↓
  └──────────────────── ESC or Click Outside ──────────────────┘
```

#### Flow 2: 자동완성 플로우 (정확한 입력)

```
사용자 입력: "Phil"
    ↓ (debounce 300ms)
드롭다운 표시:
  ┌──────────────────────────────────┐
  │ 🔍 Phil                          │
  ├──────────────────────────────────┤
  │ → Phil Ivey                      │  ← Focus on first item
  │   Phil Hellmuth                 │
  │   Philip Ng                     │
  │ ──────────────────────────       │
  │ 💡 Related tags:                │
  │   #PHIL_IVEY #HIGH_STAKES       │
  └──────────────────────────────────┘
    ↓ (Enter key)
선택: "Phil Ivey"
    ↓
검색 실행
```

**인터랙션 옵션**:
- ↓/↑ 키: 리스트 내비게이션
- Enter: 현재 선택 항목 확정
- Tab: 첫 번째 추천 자동 완성
- Esc: 드롭다운 닫기

#### Flow 3: 유사어 추천 플로우 (의미론적 검색)

```
사용자 입력: "hero call"
    ↓ (debounce 300ms)
Vertex AI 검색 (BigQuery 결과 <3개)
    ↓
드롭다운 표시:
  ┌──────────────────────────────────┐
  │ 🔍 hero call                     │
  ├──────────────────────────────────┤
  │ → hero call                      │  ← Exact match
  │   bluff catch                    │  ← Semantic match
  │   sick call                      │
  │   river decision                 │
  │ ──────────────────────────       │
  │ 🤖 AI-powered (92ms)             │  ← Source indicator
  └──────────────────────────────────┘
    ↓
선택 또는 계속 타이핑
```

**소스 표시 규칙**:
- `bigquery_cache` → 💾 Fast (10ms)
- `vertex_ai` → 🤖 AI-powered (92ms)
- `hybrid` → 🧠 Smart search (78ms)

### 2.2 사용자 여정 맵

```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│   검색 의도  │  입력 시작   │  추천 확인   │    선택     │   결과 확인  │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 목표:        │ 행동:        │ 행동:        │ 행동:        │ 목표:        │
│ 특정 핸드    │ 키워드 입력  │ 드롭다운     │ 클릭 또는    │ 비디오 재생  │
│ 빠르게 찾기  │ "jungl..."   │ 스캔         │ Enter 키     │ 핸드 분석    │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 감정:        │ 감정:        │ 감정:        │ 감정:        │ 감정:        │
│ 😐 Neutral   │ 🤔 Focus     │ 👀 Scanning  │ ✅ Confident │ 😊 Satisfied │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 요구사항:    │ 요구사항:    │ 요구사항:    │ 요구사항:    │ 요구사항:    │
│ - 빠른 시작  │ - 즉각 반응  │ - 관련성     │ - 정확성     │ - 올바른     │
│ - 명확한 UI  │ - 오타 허용  │   높은 추천  │ - 빠른 전환  │   결과       │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

### 2.3 엣지 케이스 플로우

#### 2.3.1 결과 없음

```
사용자 입력: "xyz123"
    ↓
드롭다운 표시:
  ┌──────────────────────────────────┐
  │ 🔍 xyz123                        │
  ├──────────────────────────────────┤
  │ 🚫 No suggestions found          │
  │                                  │
  │ 💡 Try:                          │
  │   - Checking spelling            │
  │   - Using player names           │
  │   - Using poker terms            │
  └──────────────────────────────────┘
```

#### 2.3.2 Rate Limit 초과

```
사용자 입력: (100회/분 초과)
    ↓
드롭다운 표시:
  ┌──────────────────────────────────┐
  │ ⚠️ Too many requests              │
  │                                  │
  │ Please wait 60 seconds           │
  │ Remaining: 45s                   │  ← Countdown timer
  └──────────────────────────────────┘
```

#### 2.3.3 네트워크 에러

```
API 호출 실패
    ↓
드롭다운 표시:
  ┌──────────────────────────────────┐
  │ 🔌 Connection error               │
  │                                  │
  │ [Retry] Check your connection    │
  └──────────────────────────────────┘
```

---

## 3. 컴포넌트 계층 구조

### 3.1 컴포넌트 트리

```
<SearchPage>
  ├── <Header>
  │     ├── <Logo>
  │     └── <Navigation>
  │
  ├── <SearchContainer>  ← Main autocomplete area
  │     ├── <SearchBar>
  │     │     ├── <SearchIcon>
  │     │     ├── <SearchInput>
  │     │     │     ├── value: string
  │     │     │     ├── onChange: (e) => void
  │     │     │     ├── onFocus: () => void
  │     │     │     ├── onKeyDown: (e) => void
  │     │     │     └── placeholder: string
  │     │     │
  │     │     ├── <ClearButton>  (conditional: if value.length > 0)
  │     │     └── <LoadingSpinner>  (conditional: if fetching)
  │     │
  │     └── <AutocompleteDropdown>  (conditional: if isOpen)
  │           ├── <DropdownHeader>
  │           │     ├── <QueryDisplay>  "You searched: {query}"
  │           │     └── <SourceBadge>  "💾 Fast (10ms)"
  │           │
  │           ├── <SuggestionList>
  │           │     ├── <SuggestionItem> (x5 max)
  │           │     │     ├── icon: React.ReactNode
  │           │     │     ├── text: string
  │           │     │     ├── highlight: string
  │           │     │     ├── isSelected: boolean
  │           │     │     ├── onClick: () => void
  │           │     │     └── onMouseEnter: () => void
  │           │     │
  │           │     └── <NoResults>  (conditional: if total === 0)
  │           │           ├── <EmptyIcon>
  │           │           └── <HelpText>
  │           │
  │           ├── <RelatedTags>  (conditional: if tags exist)
  │           │     └── <TagBadge> (x3 max)
  │           │
  │           └── <DropdownFooter>
  │                 ├── <KeyboardHints>  "↑↓ Navigate • Enter Select • Esc Close"
  │                 └── <ResponseTime>  "Response: 45ms"
  │
  ├── <SearchResults>  (after search execution)
  │     ├── <FilterSidebar>
  │     │     ├── <PotSizeFilter>
  │     │     ├── <TagFilter>
  │     │     └── <PlayerFilter>
  │     │
  │     └── <HandCardGrid>
  │           └── <HandCard> (x20 per page)
  │                 ├── <Thumbnail>
  │                 ├── <PlayerInfo>
  │                 ├── <PotInfo>
  │                 ├── <Description>
  │                 └── <VideoPlayer>
  │
  └── <Footer>
```

### 3.2 컴포넌트 사양

#### 3.2.1 SearchInput

**Props**:
```typescript
interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onFocus: () => void;
  onBlur: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  placeholder?: string;
  disabled?: boolean;
  ariaLabel: string;
  ariaDescribedBy?: string;
}
```

**State**:
```typescript
const [isFocused, setIsFocused] = useState(false);
const [inputValue, setInputValue] = useState("");
```

**Behavior**:
- Focus 시 드롭다운 자동 오픈
- Blur 시 200ms 후 드롭다운 닫기 (suggestion 클릭 시간 확보)
- 300ms debounce 후 API 호출
- 2자 미만 입력 시 API 호출 안 함

#### 3.2.2 AutocompleteDropdown

**Props**:
```typescript
interface AutocompleteDropdownProps {
  isOpen: boolean;
  suggestions: string[];
  query: string;
  source: "bigquery_cache" | "vertex_ai" | "hybrid";
  responseTimeMs: number;
  total: number;
  selectedIndex: number;
  onSelectSuggestion: (suggestion: string) => void;
  onClose: () => void;
}
```

**Position Calculation**:
```typescript
// Fixed position relative to input
const dropdownStyle = {
  position: "absolute",
  top: `${inputRect.bottom + 8}px`, // 8px gap
  left: `${inputRect.left}px`,
  width: `${inputRect.width}px`,
  maxHeight: "400px",
  zIndex: 1000
};
```

**Animation**:
```typescript
// Framer Motion variants
const dropdownVariants = {
  hidden: { opacity: 0, y: -10, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.15, ease: "easeOut" }
  },
  exit: {
    opacity: 0,
    y: -10,
    scale: 0.95,
    transition: { duration: 0.1 }
  }
};
```

#### 3.2.3 SuggestionItem

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

**Rendering Logic**:
```typescript
// Highlight matching characters
function highlightMatch(text: string, query: string): React.ReactNode {
  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const index = lowerText.indexOf(lowerQuery);

  if (index === -1) return text;

  return (
    <>
      {text.slice(0, index)}
      <mark className="bg-yellow-200 dark:bg-yellow-800 font-semibold">
        {text.slice(index, index + query.length)}
      </mark>
      {text.slice(index + query.length)}
    </>
  );
}
```

**Visual States**:
```css
/* Default */
.suggestion-item {
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

/* Hover */
.suggestion-item:hover {
  background-color: hsl(var(--muted));
}

/* Selected (keyboard navigation) */
.suggestion-item.selected {
  background-color: hsl(var(--accent));
  color: hsl(var(--accent-foreground));
}

/* Typo corrected (special indicator) */
.suggestion-item.typo-corrected::before {
  content: "✨";
  margin-right: 8px;
}
```

#### 3.2.4 SourceBadge

**Props**:
```typescript
interface SourceBadgeProps {
  source: "bigquery_cache" | "vertex_ai" | "hybrid";
  responseTimeMs: number;
}
```

**Rendering**:
```typescript
function SourceBadge({ source, responseTimeMs }: SourceBadgeProps) {
  const config = {
    bigquery_cache: { icon: "💾", label: "Fast", color: "green" },
    vertex_ai: { icon: "🤖", label: "AI-powered", color: "purple" },
    hybrid: { icon: "🧠", label: "Smart search", color: "blue" }
  };

  const { icon, label, color } = config[source];

  return (
    <Badge variant={color} className="text-xs">
      <span>{icon}</span>
      <span>{label}</span>
      <span className="ml-1 text-muted-foreground">({responseTimeMs}ms)</span>
    </Badge>
  );
}
```

---

## 4. 인터랙션 패턴

### 4.1 키보드 네비게이션

**핵심 원칙**: 마우스 없이 100% 키보드로 조작 가능

#### 4.1.1 키 맵핑

| 키 | 동작 | 조건 | 우선순위 |
|----|------|------|---------|
| **↓ (ArrowDown)** | 다음 suggestion 선택 | Dropdown open | P0 |
| **↑ (ArrowUp)** | 이전 suggestion 선택 | Dropdown open | P0 |
| **Enter** | 선택된 suggestion 확정 | Dropdown open & item selected | P0 |
| **Esc** | Dropdown 닫기 | Dropdown open | P0 |
| **Tab** | 첫 번째 suggestion 자동완성 | Dropdown open | P1 |
| **Home** | 첫 번째 suggestion 선택 | Dropdown open | P2 |
| **End** | 마지막 suggestion 선택 | Dropdown open | P2 |
| **Ctrl+K** | 검색 바 포커스 | Anywhere on page | P1 |

**구현 예시**:
```typescript
function useKeyboardNavigation(
  suggestions: string[],
  onSelect: (suggestion: string) => void,
  onClose: () => void
) {
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;

      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;

      case "Enter":
        e.preventDefault();
        if (selectedIndex >= 0) {
          onSelect(suggestions[selectedIndex]);
        }
        break;

      case "Escape":
        e.preventDefault();
        onClose();
        break;

      case "Tab":
        e.preventDefault();
        if (suggestions.length > 0) {
          onSelect(suggestions[0]);
        }
        break;

      case "Home":
        e.preventDefault();
        setSelectedIndex(0);
        break;

      case "End":
        e.preventDefault();
        setSelectedIndex(suggestions.length - 1);
        break;
    }
  }, [suggestions, selectedIndex, onSelect, onClose]);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return { selectedIndex, setSelectedIndex };
}
```

#### 4.1.2 Scroll Into View

선택된 항목이 화면 밖으로 나가면 자동 스크롤:

```typescript
useEffect(() => {
  if (selectedIndex >= 0 && dropdownRef.current) {
    const selectedElement = dropdownRef.current.children[selectedIndex];
    selectedElement?.scrollIntoView({
      behavior: "smooth",
      block: "nearest"
    });
  }
}, [selectedIndex]);
```

### 4.2 터치 이벤트 (모바일)

#### 4.2.1 Swipe to Dismiss

```typescript
function useSwipeGesture(onDismiss: () => void) {
  const [touchStart, setTouchStart] = useState(0);

  const handleTouchStart = (e: TouchEvent) => {
    setTouchStart(e.touches[0].clientY);
  };

  const handleTouchEnd = (e: TouchEvent) => {
    const touchEnd = e.changedTouches[0].clientY;
    const diff = touchStart - touchEnd;

    // Swipe up to dismiss (50px threshold)
    if (diff > 50) {
      onDismiss();
    }
  };

  return { handleTouchStart, handleTouchEnd };
}
```

#### 4.2.2 Touch Target Size

모든 터치 대상은 최소 44x44px:

```css
.suggestion-item {
  min-height: 44px;
  padding: 12px 16px;
}

.clear-button {
  width: 44px;
  height: 44px;
}
```

### 4.3 Debounce 전략

**목표**: 불필요한 API 호출 방지, UX 최적화

```typescript
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Usage
const SearchInput: React.FC = () => {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery.length >= 2) {
      fetchSuggestions(debouncedQuery);
    }
  }, [debouncedQuery]);

  return (
    <input
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      placeholder="Search players, hands, tags..."
    />
  );
};
```

**Debounce Delay 가이드**:
- 200ms: 너무 빠름, API 부하 증가
- **300ms**: **권장** (UX 최적 밸런스)
- 500ms: 너무 느림, 답답한 느낌

### 4.4 로딩 상태

#### 4.4.1 Skeleton UI

첫 로드 시 skeleton 표시:

```tsx
<AutocompleteDropdown isLoading={true}>
  <div className="space-y-2 p-4">
    {[1, 2, 3, 4, 5].map((i) => (
      <div key={i} className="flex items-center space-x-3">
        <Skeleton className="h-4 w-4 rounded-full" />
        <Skeleton className="h-4 w-[200px]" />
      </div>
    ))}
  </div>
</AutocompleteDropdown>
```

#### 4.4.2 Spinner (Subsequent Loads)

이미 결과가 있는 상태에서 재검색 시:

```tsx
<div className="relative">
  <SearchInput />
  {isFetching && (
    <div className="absolute right-3 top-1/2 -translate-y-1/2">
      <Spinner size="sm" />
    </div>
  )}
</div>
```

### 4.5 Click Outside to Close

```typescript
function useClickOutside(
  ref: React.RefObject<HTMLElement>,
  handler: () => void
) {
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [ref, handler]);
}

// Usage
const dropdownRef = useRef<HTMLDivElement>(null);
useClickOutside(dropdownRef, () => setIsOpen(false));
```

---

## 5. 디자인 시스템

### 5.1 색상 팔레트

**기본 원칙**: shadcn/ui의 HSL 변수 기반 색상 시스템 사용

```css
/* Light Mode */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;

  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;

  --popover: 0 0% 100%;
  --popover-foreground: 222.2 84% 4.9%;

  --primary: 222.2 47.4% 11.2%;  /* Dark blue for poker brand */
  --primary-foreground: 210 40% 98%;

  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;

  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;

  --accent: 210 40% 96.1%;
  --accent-foreground: 222.2 47.4% 11.2%;

  --destructive: 0 84.2% 60.2%;  /* Red for errors */
  --destructive-foreground: 210 40% 98%;

  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 222.2 84% 4.9%;

  --radius: 0.5rem;  /* Default border radius */
}

/* Dark Mode */
.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;

  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;

  --popover: 222.2 84% 4.9%;
  --popover-foreground: 210 40% 98%;

  --primary: 210 40% 98%;
  --primary-foreground: 222.2 47.4% 11.2%;

  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;

  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;

  --accent: 217.2 32.6% 17.5%;
  --accent-foreground: 210 40% 98%;

  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;

  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 212.7 26.8% 83.9%;
}
```

**포커 특화 색상**:
```css
:root {
  /* Chip colors (semantic) */
  --poker-chip-white: 0 0% 100%;
  --poker-chip-red: 0 84% 60%;
  --poker-chip-green: 142 71% 45%;
  --poker-chip-black: 0 0% 9%;
  --poker-chip-purple: 270 50% 40%;

  /* Card suits */
  --poker-suit-heart: 0 84% 60%;
  --poker-suit-diamond: 0 84% 60%;
  --poker-suit-club: 0 0% 9%;
  --poker-suit-spade: 0 0% 9%;

  /* Highlights */
  --highlight-typo-correction: 48 96% 53%;  /* Yellow */
  --highlight-match: 142 71% 45%;  /* Green */
}
```

### 5.2 타이포그래피

**폰트 패밀리**:
```css
:root {
  --font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI",
               "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans",
               "Droid Sans", "Helvetica Neue", sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", "Consolas",
               "Monaco", "Courier New", monospace;
}
```

**폰트 크기 스케일** (Tailwind-compatible):
```css
.text-xs   { font-size: 0.75rem;  line-height: 1rem;    }  /* 12px */
.text-sm   { font-size: 0.875rem; line-height: 1.25rem; }  /* 14px */
.text-base { font-size: 1rem;     line-height: 1.5rem;  }  /* 16px */
.text-lg   { font-size: 1.125rem; line-height: 1.75rem; }  /* 18px */
.text-xl   { font-size: 1.25rem;  line-height: 1.75rem; }  /* 20px */
.text-2xl  { font-size: 1.5rem;   line-height: 2rem;    }  /* 24px */
.text-3xl  { font-size: 1.875rem; line-height: 2.25rem; }  /* 30px */
```

**컴포넌트별 폰트 크기**:
```css
/* SearchInput */
.search-input {
  font-size: 1rem;      /* 16px - prevents zoom on iOS */
  line-height: 1.5rem;
  font-weight: 400;
}

/* SuggestionItem */
.suggestion-item {
  font-size: 0.875rem;  /* 14px */
  line-height: 1.25rem;
  font-weight: 400;
}

/* SourceBadge */
.source-badge {
  font-size: 0.75rem;   /* 12px */
  line-height: 1rem;
  font-weight: 500;
}

/* KeyboardHints */
.keyboard-hints {
  font-size: 0.75rem;   /* 12px */
  line-height: 1rem;
  font-weight: 400;
  font-family: var(--font-mono);
}
```

### 5.3 간격 (Spacing)

**Tailwind spacing scale** 사용:
```css
.space-1  { margin/padding: 0.25rem; }  /* 4px */
.space-2  { margin/padding: 0.5rem;  }  /* 8px */
.space-3  { margin/padding: 0.75rem; }  /* 12px */
.space-4  { margin/padding: 1rem;    }  /* 16px */
.space-5  { margin/padding: 1.25rem; }  /* 20px */
.space-6  { margin/padding: 1.5rem;  }  /* 24px */
.space-8  { margin/padding: 2rem;    }  /* 32px */
.space-10 { margin/padding: 2.5rem;  }  /* 40px */
.space-12 { margin/padding: 3rem;    }  /* 48px */
```

**컴포넌트 간격 가이드**:
```css
/* SearchInput internal padding */
.search-input {
  padding: 12px 48px 12px 16px;  /* top right bottom left */
}

/* Dropdown gap from input */
.dropdown-container {
  margin-top: 8px;  /* space-2 */
}

/* SuggestionItem padding */
.suggestion-item {
  padding: 12px 16px;  /* space-3 space-4 */
}

/* Dropdown internal spacing */
.dropdown-content {
  padding: 8px;  /* space-2 */
  gap: 4px;      /* space-1 between items */
}
```

### 5.4 Border Radius

```css
:root {
  --radius-sm: 0.25rem;  /* 4px - badges, small buttons */
  --radius-md: 0.375rem; /* 6px - input fields */
  --radius-lg: 0.5rem;   /* 8px - cards, dropdowns */
  --radius-xl: 0.75rem;  /* 12px - modals */
  --radius-full: 9999px; /* Fully rounded (pills) */
}

/* Component-specific */
.search-input {
  border-radius: var(--radius-lg);  /* 8px */
}

.dropdown {
  border-radius: var(--radius-lg);  /* 8px */
}

.suggestion-item {
  border-radius: var(--radius-md);  /* 6px */
}

.badge {
  border-radius: var(--radius-full);  /* Pill shape */
}
```

### 5.5 Shadows

```css
:root {
  /* Dropdown shadow (elevated) */
  --shadow-dropdown:
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);

  /* Card shadow (subtle) */
  --shadow-card:
    0 1px 3px 0 rgba(0, 0, 0, 0.1),
    0 1px 2px 0 rgba(0, 0, 0, 0.06);

  /* Focus ring */
  --shadow-focus:
    0 0 0 3px rgba(59, 130, 246, 0.5);
}

/* Component application */
.dropdown {
  box-shadow: var(--shadow-dropdown);
}

.search-input:focus {
  box-shadow: var(--shadow-focus);
}
```

### 5.6 포커 특화 디자인 요소

#### 5.6.1 카드 아이콘

```tsx
// Card suit icons
const CardSuitIcon: React.FC<{ suit: "heart" | "diamond" | "club" | "spade" }> = ({ suit }) => {
  const icons = {
    heart: "♥️",
    diamond: "♦️",
    club: "♣️",
    spade: "♠️"
  };

  const colors = {
    heart: "text-red-600",
    diamond: "text-red-600",
    club: "text-gray-900 dark:text-gray-100",
    spade: "text-gray-900 dark:text-gray-100"
  };

  return (
    <span className={`text-lg ${colors[suit]}`}>
      {icons[suit]}
    </span>
  );
};
```

#### 5.6.2 Chip 색상 배지

```tsx
// Pot size color indicator
function getPotSizeColor(potBB: number): string {
  if (potBB < 50) return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100";
  if (potBB < 100) return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100";
  if (potBB < 200) return "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100";
  return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100";
}

// Usage
<Badge className={getPotSizeColor(hand.potBB)}>
  {hand.potBB} BB
</Badge>
```

#### 5.6.3 액션 라벨 색상

```tsx
const actionColors = {
  fold: "bg-gray-100 text-gray-800",
  call: "bg-blue-100 text-blue-800",
  raise: "bg-purple-100 text-purple-800",
  "all-in": "bg-red-100 text-red-800",
  check: "bg-green-100 text-green-800"
};

<Badge className={actionColors[hand.heroAction]}>
  {hand.heroAction.toUpperCase()}
</Badge>
```

---

## 6. 접근성

### 6.1 WCAG 2.1 AA 준수 체크리스트

#### 6.1.1 지각성 (Perceivable)

- [x] **텍스트 대비**: 최소 4.5:1 (일반 텍스트), 3:1 (큰 텍스트)
- [x] **비텍스트 콘텐츠**: 모든 아이콘에 aria-label 제공
- [x] **컬러만으로 정보 전달 금지**: 오타 수정 시 아이콘(✨) + 텍스트 함께 제공
- [x] **반응형 텍스트**: 200% 확대 시에도 레이아웃 유지

**색상 대비 체크**:
```css
/* Light mode */
--foreground: 222.2 84% 4.9%;    /* #0a0a14 */
--background: 0 0% 100%;         /* #ffffff */
/* Contrast ratio: 20.17:1 ✅ (WCAG AAA) */

/* Selected item */
--accent-foreground: 222.2 47.4% 11.2%;  /* #0f172a */
--accent: 210 40% 96.1%;                 /* #f1f5f9 */
/* Contrast ratio: 12.63:1 ✅ (WCAG AAA) */
```

#### 6.1.2 조작성 (Operable)

- [x] **키보드 접근**: 모든 기능 키보드로 조작 가능
- [x] **포커스 표시**: 명확한 focus indicator (3px blue ring)
- [x] **시간 제한 없음**: 자동완성 타이머 없음 (사용자 속도 존중)
- [x] **Skip to content**: Ctrl+K로 검색바 바로 이동

**Focus Indicator**:
```css
.search-input:focus-visible,
.suggestion-item:focus-visible {
  outline: 3px solid hsl(var(--ring));
  outline-offset: 2px;
  border-radius: var(--radius-md);
}

/* Remove default outline */
*:focus {
  outline: none;
}
*:focus-visible {
  outline: 3px solid hsl(var(--ring));
  outline-offset: 2px;
}
```

#### 6.1.3 이해성 (Understandable)

- [x] **명확한 레이블**: 모든 입력 필드에 `<label>` 또는 `aria-label` 제공
- [x] **에러 메시지**: 구체적 오류 설명 제공
- [x] **예측 가능한 동작**: 동일한 아이콘은 동일한 동작
- [x] **입력 도움말**: placeholder + keyboard hints 제공

**ARIA Labels**:
```tsx
<input
  type="text"
  id="search-input"
  aria-label="Search poker hands, players, and tags"
  aria-describedby="search-help"
  aria-autocomplete="list"
  aria-controls="autocomplete-dropdown"
  aria-expanded={isOpen}
  aria-activedescendant={selectedIndex >= 0 ? `suggestion-${selectedIndex}` : undefined}
/>

<div id="search-help" className="sr-only">
  Type at least 2 characters to get suggestions
</div>
```

#### 6.1.4 견고성 (Robust)

- [x] **유효한 HTML**: W3C 마크업 검증
- [x] **ARIA 속성**: 올바른 role, state, property 사용
- [x] **스크린 리더 테스트**: NVDA, JAWS, VoiceOver 테스트

**ARIA Roles**:
```tsx
<div
  role="combobox"
  aria-haspopup="listbox"
  aria-expanded={isOpen}
>
  <input
    role="searchbox"
    aria-autocomplete="list"
    aria-controls="suggestions-list"
  />

  {isOpen && (
    <ul
      id="suggestions-list"
      role="listbox"
      aria-label="Search suggestions"
    >
      {suggestions.map((suggestion, index) => (
        <li
          key={index}
          id={`suggestion-${index}`}
          role="option"
          aria-selected={index === selectedIndex}
        >
          {suggestion}
        </li>
      ))}
    </ul>
  )}
</div>
```

### 6.2 스크린 리더 지원

#### 6.2.1 Live Regions

검색 결과 변경 시 스크린 리더 알림:

```tsx
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  className="sr-only"
>
  {isLoading && "Loading suggestions..."}
  {!isLoading && total > 0 && `${total} suggestions found`}
  {!isLoading && total === 0 && "No suggestions found"}
</div>
```

#### 6.2.2 동적 콘텐츠 알림

```tsx
// 오타 수정 시
<div role="status" aria-live="assertive" className="sr-only">
  Did you mean: {correctedQuery}
</div>

// Rate limit 초과 시
<div role="alert" aria-live="assertive" className="sr-only">
  Rate limit exceeded. Please wait 60 seconds.
</div>
```

### 6.3 Skip Links

```tsx
<a
  href="#search-input"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-primary focus:text-primary-foreground focus:px-4 focus:py-2 focus:rounded"
>
  Skip to search
</a>
```

### 6.4 Focus Management

드롭다운 열릴 때 첫 항목으로 포커스 이동:

```typescript
useEffect(() => {
  if (isOpen && suggestions.length > 0) {
    // Move focus to first suggestion
    const firstItem = dropdownRef.current?.querySelector('[role="option"]');
    (firstItem as HTMLElement)?.focus();
  }
}, [isOpen, suggestions]);
```

---

## 7. 반응형 디자인

### 7.1 Breakpoints

```css
/* Tailwind default breakpoints */
/* Mobile first approach */

/* xs: Extra small (default, no prefix) */
@media (min-width: 0px) {
  /* Base mobile styles */
}

/* sm: Small devices (landscape phones, 640px+) */
@media (min-width: 640px) {
  /* ... */
}

/* md: Medium devices (tablets, 768px+) */
@media (min-width: 768px) {
  /* ... */
}

/* lg: Large devices (desktops, 1024px+) */
@media (min-width: 1024px) {
  /* ... */
}

/* xl: Extra large devices (large desktops, 1280px+) */
@media (min-width: 1280px) {
  /* ... */
}

/* 2xl: 2X Large devices (1536px+) */
@media (min-width: 1536px) {
  /* ... */
}
```

### 7.2 컴포넌트별 반응형 설정

#### 7.2.1 SearchInput

```css
/* Mobile (default) */
.search-input {
  width: 100%;
  max-width: 100%;
  padding: 12px 48px 12px 16px;
  font-size: 16px;  /* Prevents zoom on iOS */
}

/* Tablet (768px+) */
@media (min-width: 768px) {
  .search-input {
    max-width: 600px;
    padding: 14px 56px 14px 20px;
  }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
  .search-input {
    max-width: 720px;
    padding: 16px 64px 16px 24px;
  }
}
```

**Tailwind 버전**:
```tsx
<input
  className="w-full max-w-full md:max-w-[600px] lg:max-w-[720px]
             px-4 pr-12 py-3 md:px-5 md:pr-14 lg:px-6 lg:pr-16
             text-base rounded-lg"
  type="text"
  placeholder="Search poker hands..."
/>
```

#### 7.2.2 AutocompleteDropdown

```css
/* Mobile (default) */
.dropdown {
  width: 100vw;  /* Full width */
  left: 0;
  right: 0;
  max-height: 60vh;  /* Don't cover entire screen */
}

/* Tablet (768px+) */
@media (min-width: 768px) {
  .dropdown {
    width: auto;  /* Match input width */
    left: auto;
    right: auto;
    max-height: 400px;
  }
}
```

**Tailwind 버전**:
```tsx
<div
  className="w-screen md:w-auto left-0 right-0 md:left-auto md:right-auto
             max-h-[60vh] md:max-h-[400px]"
>
  {/* Dropdown content */}
</div>
```

#### 7.2.3 SuggestionItem

```css
/* Mobile (default) */
.suggestion-item {
  padding: 12px 16px;
  font-size: 14px;
  min-height: 48px;  /* Larger touch target */
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
  .suggestion-item {
    padding: 10px 16px;
    font-size: 14px;
    min-height: 40px;  /* Smaller for mouse */
  }
}
```

### 7.3 Touch Target Sizes

**WCAG 2.5.5 준수**: 최소 44x44px (모바일)

```css
/* Mobile touch targets */
.touch-target {
  min-width: 44px;
  min-height: 44px;
  padding: 12px;
}

/* Desktop mouse targets (smaller OK) */
@media (min-width: 1024px) and (pointer: fine) {
  .touch-target {
    min-width: 32px;
    min-height: 32px;
    padding: 8px;
  }
}
```

**Tailwind 버전**:
```tsx
<button
  className="min-w-[44px] min-h-[44px] p-3 lg:min-w-8 lg:min-h-8 lg:p-2"
  aria-label="Clear search"
>
  <XIcon />
</button>
```

### 7.4 모바일 최적화

#### 7.4.1 iOS Zoom 방지

```css
/* iOS Safari zooms when font-size < 16px */
input[type="text"] {
  font-size: 16px !important;  /* Never smaller on mobile */
}

@media (min-width: 768px) {
  input[type="text"] {
    font-size: 14px;  /* Can be smaller on desktop */
  }
}
```

#### 7.4.2 Safe Area Insets (iPhone notch)

```css
.search-container {
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
  padding-top: env(safe-area-inset-top);
}
```

#### 7.4.3 Mobile-First Grid

```tsx
// SearchResults grid
<div className="
  grid
  grid-cols-1          /* Mobile: 1 column */
  sm:grid-cols-2       /* Tablet: 2 columns */
  lg:grid-cols-3       /* Desktop: 3 columns */
  xl:grid-cols-4       /* Large desktop: 4 columns */
  gap-4 sm:gap-6 lg:gap-8
">
  {results.map(hand => <HandCard key={hand.id} {...hand} />)}
</div>
```

### 7.5 Orientation Changes

```typescript
function useOrientation() {
  const [isLandscape, setIsLandscape] = useState(
    window.matchMedia("(orientation: landscape)").matches
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia("(orientation: landscape)");
    const handler = (e: MediaQueryListEvent) => setIsLandscape(e.matches);

    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  return { isLandscape, isPortrait: !isLandscape };
}

// Usage
const { isLandscape } = useOrientation();

<AutocompleteDropdown
  maxHeight={isLandscape ? "40vh" : "60vh"}  // Shorter in landscape
/>
```

---

## 8. 성능 요구사항

### 8.1 성능 목표

| 메트릭 | 목표 | 측정 방법 |
|--------|------|----------|
| **Initial Load** | <3초 | Lighthouse Performance Score ≥90 |
| **Autocomplete Response** | <500ms | API call + rendering |
| **First Contentful Paint (FCP)** | <1.8초 | Lighthouse |
| **Largest Contentful Paint (LCP)** | <2.5초 | Lighthouse |
| **Cumulative Layout Shift (CLS)** | <0.1 | Lighthouse |
| **First Input Delay (FID)** | <100ms | Lighthouse |
| **Time to Interactive (TTI)** | <3.8초 | Lighthouse |
| **60 FPS 스크롤** | 100% | DevTools Performance |

### 8.2 번들 크기 최적화

**Target Bundle Sizes**:
```
Total Initial Load:    < 200 KB (gzipped)
├── React + ReactDOM:  ~ 45 KB
├── Next.js Runtime:   ~ 80 KB
├── Components:        ~ 50 KB
└── Utilities:         ~ 25 KB

Code Splitting:
├── /search page:      ~ 150 KB (includes autocomplete)
├── /hand/[id] page:   ~ 120 KB (hand detail)
└── Shared chunks:     ~ 80 KB
```

**구현 전략**:

```typescript
// Dynamic imports for heavy components
const VideoPlayer = dynamic(() => import("@/components/VideoPlayer"), {
  loading: () => <Skeleton className="w-full h-[400px]" />,
  ssr: false  // Don't render on server
});

const FilterSidebar = dynamic(() => import("@/components/FilterSidebar"), {
  loading: () => <FilterSkeleton />
});
```

### 8.3 이미지 최적화

```tsx
import Image from "next/image";

// Thumbnail images
<Image
  src={hand.thumbnailUrl}
  alt={`${hand.heroName} vs ${hand.villainName}`}
  width={400}
  height={225}
  placeholder="blur"
  blurDataURL={hand.blurDataURL}  // Low-quality placeholder
  loading="lazy"  // Lazy load below fold
  sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 25vw"
/>
```

**WebP/AVIF 변환**:
```typescript
// next.config.js
module.exports = {
  images: {
    formats: ['image/avif', 'image/webp'],  // Modern formats first
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  }
};
```

### 8.4 API 호출 최적화

#### 8.4.1 요청 Debouncing

```typescript
// Already covered in Section 4.3
const debouncedQuery = useDebounce(query, 300);
```

#### 8.4.2 Request Cancellation

```typescript
function useAutocomplete(query: string) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // Cancel previous request
    abortControllerRef.current?.abort();

    // Create new abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;

    if (query.length >= 2) {
      fetchSuggestions(query, controller.signal)
        .then(setSuggestions)
        .catch(err => {
          if (err.name !== 'AbortError') {
            console.error(err);
          }
        });
    }

    return () => controller.abort();
  }, [query]);

  return suggestions;
}
```

#### 8.4.3 Response Caching

```typescript
// In-memory cache (simple)
const cache = new Map<string, { suggestions: string[], timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000;  // 5 minutes

async function fetchWithCache(query: string): Promise<string[]> {
  const cached = cache.get(query);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.suggestions;  // Return cached
  }

  const suggestions = await fetch(`/api/autocomplete?q=${query}`)
    .then(res => res.json())
    .then(data => data.suggestions);

  cache.set(query, { suggestions, timestamp: Date.now() });
  return suggestions;
}
```

### 8.5 렌더링 최적화

#### 8.5.1 React.memo

```typescript
const SuggestionItem = React.memo<SuggestionItemProps>(
  ({ text, query, isSelected, onClick }) => {
    return (
      <div
        className={cn("suggestion-item", { selected: isSelected })}
        onClick={onClick}
      >
        {highlightMatch(text, query)}
      </div>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison
    return (
      prevProps.text === nextProps.text &&
      prevProps.isSelected === nextProps.isSelected
    );
  }
);
```

#### 8.5.2 Virtual Scrolling (100+ 결과 시)

```typescript
import { useVirtualizer } from "@tanstack/react-virtual";

function SuggestionList({ suggestions }: { suggestions: string[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: suggestions.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40,  // Each item ~40px
    overscan: 5  // Render 5 extra items
  });

  return (
    <div ref={parentRef} style={{ height: "400px", overflow: "auto" }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: "relative" }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`
            }}
          >
            <SuggestionItem text={suggestions[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 8.6 Core Web Vitals 최적화

#### 8.6.1 LCP (Largest Contentful Paint) < 2.5s

```typescript
// Preload critical resources
<Head>
  <link rel="preconnect" href="https://api.example.com" />
  <link rel="dns-prefetch" href="https://api.example.com" />
  <link rel="preload" href="/fonts/Inter-Regular.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
</Head>
```

#### 8.6.2 CLS (Cumulative Layout Shift) < 0.1

```css
/* Reserve space for dropdown */
.search-container {
  min-height: 600px;  /* Input + dropdown height */
}

/* Fixed dimensions for images */
img {
  width: 400px;
  height: 225px;  /* 16:9 aspect ratio */
}
```

#### 8.6.3 FID (First Input Delay) < 100ms

```typescript
// Use requestIdleCallback for non-critical tasks
useEffect(() => {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      // Prefetch next page data
      prefetchHandDetails(nextHandId);
    });
  }
}, [nextHandId]);
```

---

## 9. 에러 핸들링

### 9.1 에러 분류

| 에러 타입 | HTTP 코드 | 원인 | 사용자 메시지 | 복구 방법 |
|---------|----------|------|-------------|----------|
| **Validation Error** | 422 | 입력 검증 실패 | "Invalid characters in query" | 입력 수정 |
| **Rate Limit** | 429 | 요청 제한 초과 | "Too many requests. Wait 60s" | 대기 후 재시도 |
| **Network Error** | - | 네트워크 끊김 | "Check your connection" | 재시도 버튼 |
| **Server Error** | 500 | 백엔드 장애 | "Service temporarily unavailable" | 자동 재시도 |
| **Timeout** | - | 5초 초과 | "Request timed out" | 재시도 버튼 |

### 9.2 에러 UI 컴포넌트

#### 9.2.1 ValidationError

```tsx
<AutocompleteDropdown isOpen={true}>
  <div className="p-4 text-center">
    <AlertCircle className="w-12 h-12 mx-auto text-yellow-500 mb-2" />
    <h3 className="font-semibold text-sm">Invalid Query</h3>
    <p className="text-xs text-muted-foreground mt-1">
      Only alphanumeric characters, spaces, and hyphens are allowed.
    </p>
    <p className="text-xs text-destructive mt-2">
      Forbidden characters: <code className="bg-muted px-1">@#$%</code>
    </p>
  </div>
</AutocompleteDropdown>
```

#### 9.2.2 RateLimitError

```tsx
function RateLimitError({ retryAfterSeconds }: { retryAfterSeconds: number }) {
  const [countdown, setCountdown] = useState(retryAfterSeconds);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="p-4 text-center">
      <Clock className="w-12 h-12 mx-auto text-orange-500 mb-2" />
      <h3 className="font-semibold text-sm">Too Many Requests</h3>
      <p className="text-xs text-muted-foreground mt-1">
        Please wait <strong>{countdown}s</strong> before trying again.
      </p>
      <Progress value={(retryAfterSeconds - countdown) / retryAfterSeconds * 100} className="mt-3" />
    </div>
  );
}
```

#### 9.2.3 NetworkError

```tsx
function NetworkError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="p-4 text-center">
      <WifiOff className="w-12 h-12 mx-auto text-red-500 mb-2" />
      <h3 className="font-semibold text-sm">Connection Error</h3>
      <p className="text-xs text-muted-foreground mt-1">
        Unable to reach the server. Check your internet connection.
      </p>
      <Button
        onClick={onRetry}
        variant="outline"
        size="sm"
        className="mt-3"
      >
        <RefreshCw className="w-4 h-4 mr-2" />
        Retry
      </Button>
    </div>
  );
}
```

#### 9.2.4 NoResults

```tsx
function NoResults({ query }: { query: string }) {
  return (
    <div className="p-6 text-center">
      <Search className="w-16 h-16 mx-auto text-muted-foreground/50 mb-3" />
      <h3 className="font-semibold text-base">No suggestions found</h3>
      <p className="text-sm text-muted-foreground mt-2">
        We couldn't find any results for "<strong>{query}</strong>"
      </p>

      <div className="mt-4 space-y-2 text-left">
        <p className="text-xs font-semibold text-muted-foreground">💡 Try:</p>
        <ul className="text-xs text-muted-foreground space-y-1 pl-4">
          <li>• Checking your spelling</li>
          <li>• Using player names (e.g., "Phil Ivey")</li>
          <li>• Using poker terms (e.g., "bluff", "hero call")</li>
          <li>• Using tournament names (e.g., "WSOP 2024")</li>
        </ul>
      </div>
    </div>
  );
}
```

### 9.3 에러 처리 로직

```typescript
function useAutocompleteWithError(query: string) {
  const [state, setState] = useState<{
    suggestions: string[];
    error: Error | null;
    isLoading: boolean;
  }>({
    suggestions: [],
    error: null,
    isLoading: false
  });

  const fetchSuggestions = async (q: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`/api/autocomplete?q=${encodeURIComponent(q)}`, {
        signal: AbortSignal.timeout(5000)  // 5초 타임아웃
      });

      if (response.status === 422) {
        throw new ValidationError("Invalid query format");
      }

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get("Retry-After") || "60");
        throw new RateLimitError(retryAfter);
      }

      if (!response.ok) {
        throw new ServerError(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setState({ suggestions: data.suggestions, error: null, isLoading: false });

    } catch (error) {
      if (error instanceof DOMException && error.name === "TimeoutError") {
        setState(prev => ({
          ...prev,
          error: new TimeoutError("Request timed out"),
          isLoading: false
        }));
      } else if (error instanceof TypeError) {
        setState(prev => ({
          ...prev,
          error: new NetworkError("Network error"),
          isLoading: false
        }));
      } else {
        setState(prev => ({ ...prev, error: error as Error, isLoading: false }));
      }
    }
  };

  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery.length >= 2) {
      fetchSuggestions(debouncedQuery);
    }
  }, [debouncedQuery]);

  return { ...state, retry: () => fetchSuggestions(debouncedQuery) };
}
```

### 9.4 Graceful Degradation

API 실패 시 로컬 캐시 사용:

```typescript
function useAutocompleteWithFallback(query: string) {
  const { suggestions, error, isLoading } = useAutocompleteWithError(query);
  const [cachedSuggestions, setCachedSuggestions] = useState<string[]>([]);

  // 성공 시 캐시 업데이트
  useEffect(() => {
    if (suggestions.length > 0) {
      setCachedSuggestions(suggestions);
      localStorage.setItem(`autocomplete:${query}`, JSON.stringify(suggestions));
    }
  }, [suggestions, query]);

  // 에러 시 로컬 캐시 사용
  if (error && cachedSuggestions.length === 0) {
    const cached = localStorage.getItem(`autocomplete:${query}`);
    if (cached) {
      return {
        suggestions: JSON.parse(cached),
        error: null,
        isLoading: false,
        isFromCache: true
      };
    }
  }

  return { suggestions, error, isLoading, isFromCache: false };
}
```

---

## 10. 구현 가이드라인

### 10.1 기술 스택

**Frontend Framework**:
- **Morphic UI** (Next.js 15 + React 19)
- **Vercel AI SDK** 4.3.6 (Generative UI)
- **TypeScript** 5.3+
- **Tailwind CSS** 3.4.1

**UI Components**:
- **shadcn/ui** (Radix UI primitives)
- **Framer Motion** (animations)
- **Lucide React** (icons)

**State Management**:
- **Zustand** (global state, if needed)
- **React Query** (server state, caching)

**Testing**:
- **Jest** (unit tests)
- **React Testing Library** (component tests)
- **Playwright** (E2E tests)

### 10.2 프로젝트 구조

```
frontend/
├── app/
│   ├── (search)/
│   │   ├── page.tsx                  # Main search page
│   │   └── layout.tsx
│   ├── hand/
│   │   └── [id]/
│   │       └── page.tsx              # Hand detail page
│   └── layout.tsx
│
├── components/
│   ├── ui/                           # shadcn/ui primitives
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── badge.tsx
│   │   ├── skeleton.tsx
│   │   └── ...
│   │
│   ├── search/                       # Search-specific components
│   │   ├── SearchBar.tsx
│   │   ├── AutocompleteDropdown.tsx
│   │   ├── SuggestionItem.tsx
│   │   ├── SourceBadge.tsx
│   │   ├── KeyboardHints.tsx
│   │   └── NoResults.tsx
│   │
│   ├── hand/                         # Hand display components
│   │   ├── HandCard.tsx
│   │   ├── VideoPlayer.tsx
│   │   └── PlayerInfo.tsx
│   │
│   └── layout/
│       ├── Header.tsx
│       ├── Footer.tsx
│       └── Navigation.tsx
│
├── hooks/
│   ├── useAutocomplete.ts            # Autocomplete logic
│   ├── useDebounce.ts                # Debouncing
│   ├── useKeyboardNavigation.ts      # Keyboard handling
│   ├── useClickOutside.ts            # Click outside handler
│   └── useOrientation.ts             # Screen orientation
│
├── lib/
│   ├── api/
│   │   ├── autocomplete.ts           # API client
│   │   └── hands.ts
│   ├── utils.ts                      # Utility functions
│   └── cn.ts                         # Class name merger
│
├── types/
│   ├── autocomplete.ts               # TypeScript interfaces
│   ├── hand.ts
│   └── api.ts
│
└── styles/
    └── globals.css                   # Global styles
```

### 10.3 개발 시작하기

#### 10.3.1 설치

```bash
# Clone repository
git clone https://github.com/your-org/archive-mam-frontend.git
cd archive-mam-frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

#### 10.3.2 환경 변수

```.env.local
# API Endpoint
NEXT_PUBLIC_API_URL=http://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_MOCK_DATA=false
NEXT_PUBLIC_ENABLE_ANALYTICS=true

# Performance
NEXT_PUBLIC_DEBOUNCE_MS=300
NEXT_PUBLIC_API_TIMEOUT_MS=5000
```

#### 10.3.3 shadcn/ui 설정

```bash
# Initialize shadcn/ui
npx shadcn-ui@latest init

# Add components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add command  # For autocomplete
```

### 10.4 핵심 컴포넌트 구현 예시

#### 10.4.1 SearchBar.tsx

```typescript
"use client";

import React, { useState, useRef } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { AutocompleteDropdown } from "./AutocompleteDropdown";
import { useAutocomplete } from "@/hooks/useAutocomplete";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useClickOutside } from "@/hooks/useClickOutside";

export function SearchBar() {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { suggestions, isLoading, error } = useAutocomplete(query);
  const { selectedIndex, setSelectedIndex } = useKeyboardNavigation(
    suggestions,
    (suggestion) => {
      setQuery(suggestion);
      setIsOpen(false);
      // Execute search
    },
    () => setIsOpen(false)
  );

  useClickOutside(dropdownRef, () => setIsOpen(false));

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    if (e.target.value.length >= 2) {
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  };

  const handleClear = () => {
    setQuery("");
    setIsOpen(false);
    inputRef.current?.focus();
  };

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />

        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          placeholder="Search poker hands, players, tags..."
          className="pl-12 pr-12 h-12 text-base rounded-lg"
          aria-label="Search poker archive"
          aria-autocomplete="list"
          aria-controls="autocomplete-dropdown"
          aria-expanded={isOpen}
          aria-activedescendant={
            selectedIndex >= 0 ? `suggestion-${selectedIndex}` : undefined
          }
        />

        {isLoading && (
          <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 animate-spin text-muted-foreground" />
        )}

        {!isLoading && query && (
          <button
            onClick={handleClear}
            className="absolute right-4 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center rounded-full hover:bg-muted transition-colors"
            aria-label="Clear search"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {isOpen && (
        <AutocompleteDropdown
          ref={dropdownRef}
          suggestions={suggestions}
          query={query}
          selectedIndex={selectedIndex}
          onSelectSuggestion={(suggestion) => {
            setQuery(suggestion);
            setIsOpen(false);
          }}
          error={error}
        />
      )}
    </div>
  );
}
```

#### 10.4.2 useAutocomplete.ts

```typescript
import { useState, useEffect } from "react";
import { useDebounce } from "./useDebounce";

interface AutocompleteState {
  suggestions: string[];
  isLoading: boolean;
  error: Error | null;
  source: "bigquery_cache" | "vertex_ai" | "hybrid";
  responseTimeMs: number;
}

export function useAutocomplete(query: string) {
  const [state, setState] = useState<AutocompleteState>({
    suggestions: [],
    isLoading: false,
    error: null,
    source: "bigquery_cache",
    responseTimeMs: 0
  });

  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setState(prev => ({ ...prev, suggestions: [], isLoading: false }));
      return;
    }

    const abortController = new AbortController();

    const fetchSuggestions = async () => {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      const startTime = performance.now();

      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/autocomplete?q=${encodeURIComponent(debouncedQuery)}&limit=5`,
          { signal: abortController.signal }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const responseTimeMs = performance.now() - startTime;

        setState({
          suggestions: data.suggestions,
          isLoading: false,
          error: null,
          source: data.source,
          responseTimeMs
        });
      } catch (error) {
        if (error instanceof Error && error.name !== "AbortError") {
          setState(prev => ({
            ...prev,
            isLoading: false,
            error: error as Error
          }));
        }
      }
    };

    fetchSuggestions();

    return () => abortController.abort();
  }, [debouncedQuery]);

  return state;
}
```

### 10.5 테스트 전략

#### 10.5.1 Unit Tests (Jest)

```typescript
// __tests__/hooks/useDebounce.test.ts
import { renderHook, waitFor } from "@testing-library/react";
import { useDebounce } from "@/hooks/useDebounce";

describe("useDebounce", () => {
  it("debounces value changes", async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "test", delay: 300 } }
    );

    expect(result.current).toBe("test");

    rerender({ value: "new value", delay: 300 });
    expect(result.current).toBe("test");  // Still old value

    await waitFor(() => expect(result.current).toBe("new value"), {
      timeout: 400
    });
  });
});
```

#### 10.5.2 Component Tests (React Testing Library)

```typescript
// __tests__/components/SearchBar.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SearchBar } from "@/components/search/SearchBar";

describe("SearchBar", () => {
  it("shows dropdown when typing", async () => {
    render(<SearchBar />);

    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "Phil" } });

    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });
  });

  it("highlights matching characters", async () => {
    render(<SearchBar />);

    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "Phil" } });

    await waitFor(() => {
      const highlighted = screen.getByText("Phil", { selector: "mark" });
      expect(highlighted).toHaveClass("bg-yellow-200");
    });
  });
});
```

#### 10.5.3 E2E Tests (Playwright)

```typescript
// e2e/autocomplete.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Autocomplete", () => {
  test("should show suggestions on typing", async ({ page }) => {
    await page.goto("/search");

    const searchInput = page.getByRole("searchbox");
    await searchInput.fill("Phil");

    await expect(page.getByRole("listbox")).toBeVisible();
    await expect(page.getByText("Phil Ivey")).toBeVisible();
  });

  test("keyboard navigation works", async ({ page }) => {
    await page.goto("/search");

    const searchInput = page.getByRole("searchbox");
    await searchInput.fill("Phil");

    await page.keyboard.press("ArrowDown");
    await expect(page.getByRole("option", { selected: true })).toHaveText("Phil Ivey");

    await page.keyboard.press("Enter");
    await expect(searchInput).toHaveValue("Phil Ivey");
  });
});
```

### 10.6 배포

#### 10.6.1 Vercel 배포

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to production
vercel --prod

# Environment variables (set in Vercel dashboard)
NEXT_PUBLIC_API_URL=https://api.poker-archive.com
```

#### 10.6.2 성능 모니터링

```typescript
// app/layout.tsx
import { Analytics } from "@vercel/analytics/react";
import { SpeedInsights } from "@vercel/speed-insights/next";

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
```

---

## 11. 부록

### 11.1 체크리스트 (구현 전 확인)

#### Phase 1: 기본 구조
- [ ] Next.js 15 + React 19 프로젝트 생성
- [ ] shadcn/ui 초기화
- [ ] Tailwind CSS 설정
- [ ] 환경 변수 설정 (.env.local)
- [ ] 프로젝트 구조 생성

#### Phase 2: 컴포넌트 구현
- [ ] SearchBar 컴포넌트
- [ ] AutocompleteDropdown 컴포넌트
- [ ] SuggestionItem 컴포넌트
- [ ] SourceBadge 컴포넌트
- [ ] 에러 컴포넌트 (ValidationError, RateLimitError, NetworkError, NoResults)

#### Phase 3: 기능 구현
- [ ] useAutocomplete 훅
- [ ] useDebounce 훅
- [ ] useKeyboardNavigation 훅
- [ ] useClickOutside 훅
- [ ] API 클라이언트 (autocomplete.ts)

#### Phase 4: 스타일링
- [ ] Light/Dark 모드 구현
- [ ] 포커 특화 색상 적용
- [ ] 반응형 디자인 (Mobile/Tablet/Desktop)
- [ ] 애니메이션 (Framer Motion)

#### Phase 5: 접근성
- [ ] ARIA 속성 추가
- [ ] 키보드 네비게이션 테스트
- [ ] 스크린 리더 테스트
- [ ] 색상 대비 검증

#### Phase 6: 성능 최적화
- [ ] 이미지 최적화 (WebP/AVIF)
- [ ] 코드 스플리팅
- [ ] React.memo 적용
- [ ] Lighthouse 테스트 (Performance ≥90)

#### Phase 7: 테스트
- [ ] Unit 테스트 (Jest)
- [ ] Component 테스트 (React Testing Library)
- [ ] E2E 테스트 (Playwright)
- [ ] Cross-browser 테스트

#### Phase 8: 배포
- [ ] Vercel 배포
- [ ] 환경 변수 설정
- [ ] Analytics 설정
- [ ] Performance 모니터링

### 11.2 참고 자료

**공식 문서**:
- [Next.js 15 Docs](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)

**접근성**:
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)

**성능**:
- [Web Vitals](https://web.dev/vitals/)
- [Lighthouse Scoring](https://web.dev/performance-scoring/)

### 11.3 용어 사전

| 용어 | 설명 |
|-----|-----|
| **Debouncing** | 연속된 이벤트를 지연시켜 마지막 이벤트만 처리 |
| **Skeleton UI** | 콘텐츠 로딩 중 표시되는 placeholder UI |
| **Focus Indicator** | 키보드로 선택된 요소를 시각적으로 표시 |
| **ARIA** | Accessible Rich Internet Applications (접근성 표준) |
| **LCP** | Largest Contentful Paint (가장 큰 콘텐츠 렌더링 시간) |
| **CLS** | Cumulative Layout Shift (누적 레이아웃 이동) |
| **FID** | First Input Delay (첫 입력 지연) |

---

**문서 종료**

**다음 단계**: [Task 0.2 - 컴포넌트 구현 시작](../0002-tasks-autocomplete-frontend.md)

**문의**: aiden.kim@ggproduction.net
