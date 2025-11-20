# 프론트엔드 컴포넌트 아키텍처 - 포커 아카이브 Autocomplete

**문서 버전**: 1.0.0
**작성일**: 2025-11-19
**프로젝트**: archive-mam (포커 아카이브 검색 시스템)
**목적**: Autocomplete 기능의 프론트엔드 컴포넌트 아키텍처 정의
**기술 스택**: Morphic UI (Next.js 15 + React 19) + Vercel AI SDK 4.3.6 + shadcn/ui
**예상 구현 시간**: 5-7일

---

## Table of Contents

1. [프로젝트 구조](#1-프로젝트-구조)
2. [핵심 컴포넌트 설계](#2-핵심-컴포넌트-설계)
3. [상태 관리 전략](#3-상태-관리-전략)
4. [데이터 플로우](#4-데이터-플로우)
5. [API 통합 패턴](#5-api-통합-패턴)
6. [TypeScript 타입 정의](#6-typescript-타입-정의)
7. [접근성 구현](#7-접근성-구현)
8. [성능 최적화](#8-성능-최적화)
9. [테스트 전략](#9-테스트-전략)
10. [구현 로드맵](#10-구현-로드맵)

---

## 1. 프로젝트 구조

### 1.1 전체 디렉토리 구조

```
morphic-poker-search/
├── app/                                    # Next.js 15 App Router
│   ├── (main)/
│   │   ├── search/
│   │   │   ├── page.tsx                   # 메인 검색 페이지 (Server Component)
│   │   │   ├── loading.tsx                # 로딩 UI (Suspense fallback)
│   │   │   └── error.tsx                  # 에러 바운더리
│   │   │
│   │   ├── hand/
│   │   │   └── [id]/
│   │   │       ├── page.tsx               # 핸드 상세 페이지
│   │   │       └── loading.tsx
│   │   │
│   │   └── layout.tsx                     # 메인 레이아웃 (Header + Footer)
│   │
│   ├── api/                                # API Routes (Next.js)
│   │   └── autocomplete/
│   │       └── route.ts                   # Proxy to backend API (optional)
│   │
│   ├── layout.tsx                          # Root layout
│   ├── globals.css                         # Global styles
│   └── providers.tsx                       # Context providers
│
├── components/
│   ├── ui/                                 # shadcn/ui primitives
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── badge.tsx
│   │   ├── skeleton.tsx
│   │   ├── command.tsx                     # Combobox primitive
│   │   ├── popover.tsx
│   │   ├── scroll-area.tsx
│   │   └── separator.tsx
│   │
│   ├── search/                             # Search-specific components
│   │   ├── SearchBar.tsx                   # Main search input + autocomplete integration
│   │   ├── AutocompleteDropdown.tsx        # Dropdown container with positioning
│   │   ├── SuggestionList.tsx              # List of suggestions
│   │   ├── SuggestionItem.tsx              # Individual suggestion with highlighting
│   │   ├── SourceBadge.tsx                 # "BigQuery" or "Vertex AI" indicator
│   │   ├── KeyboardHints.tsx               # Bottom hints (↑↓ Navigate • Enter Select)
│   │   ├── LoadingState.tsx                # Skeleton UI for loading
│   │   │
│   │   └── errors/                         # Error state components
│   │       ├── ValidationError.tsx
│   │       ├── RateLimitError.tsx
│   │       ├── NetworkError.tsx
│   │       └── NoResults.tsx
│   │
│   ├── hand/                               # Hand display components
│   │   ├── HandCard.tsx                    # Search result card
│   │   ├── HandCardGrid.tsx                # Grid container
│   │   ├── VideoPlayer.tsx                 # Video playback (lazy loaded)
│   │   └── PlayerInfo.tsx                  # Player names + stacks
│   │
│   └── layout/                             # Layout components
│       ├── Header.tsx
│       ├── Footer.tsx
│       ├── Navigation.tsx
│       └── ThemeToggle.tsx                 # Dark mode toggle
│
├── hooks/                                  # Custom React hooks
│   ├── useAutocomplete.ts                  # Main autocomplete logic + API integration
│   ├── useDebounce.ts                      # Debouncing utility
│   ├── useKeyboardNavigation.ts            # Keyboard event handling (↑↓ Enter Esc)
│   ├── useClickOutside.ts                  # Click outside handler
│   ├── useOrientation.ts                   # Screen orientation detection
│   ├── useFocusManagement.ts               # Focus trap and restoration
│   └── useMediaQuery.ts                    # Responsive breakpoint detection
│
├── lib/
│   ├── api/
│   │   ├── autocomplete.ts                 # Autocomplete API client
│   │   ├── hands.ts                        # Hands API client
│   │   └── client.ts                       # Base fetch wrapper with error handling
│   │
│   ├── utils/
│   │   ├── cn.ts                           # Class name merger (clsx + tailwind-merge)
│   │   ├── highlight.ts                    # Text highlighting utility
│   │   ├── cache.ts                        # In-memory cache implementation
│   │   └── validators.ts                   # Input validation
│   │
│   └── constants/
│       ├── config.ts                       # App configuration
│       └── api.ts                          # API endpoints
│
├── types/
│   ├── autocomplete.ts                     # Autocomplete-related types
│   ├── hand.ts                             # Hand data types
│   ├── api.ts                              # API response types
│   └── errors.ts                           # Custom error types
│
├── styles/
│   ├── globals.css                         # Global CSS + Tailwind directives
│   └── animations.css                      # Custom animations
│
├── __tests__/                              # Test files
│   ├── components/
│   │   ├── SearchBar.test.tsx
│   │   ├── AutocompleteDropdown.test.tsx
│   │   └── SuggestionItem.test.tsx
│   │
│   ├── hooks/
│   │   ├── useAutocomplete.test.ts
│   │   ├── useDebounce.test.ts
│   │   └── useKeyboardNavigation.test.ts
│   │
│   └── e2e/
│       ├── autocomplete.spec.ts            # Playwright E2E tests
│       └── keyboard-navigation.spec.ts
│
├── public/
│   ├── icons/                              # Custom icons
│   └── fonts/                              # Custom fonts (if any)
│
├── .env.local                              # Environment variables
├── .env.example                            # Environment variables template
├── next.config.js                          # Next.js configuration
├── tailwind.config.js                      # Tailwind configuration
├── tsconfig.json                           # TypeScript configuration
├── playwright.config.ts                    # Playwright configuration
├── jest.config.js                          # Jest configuration
└── package.json
```

### 1.2 파일 역할 설명

**Core Components**:
- `SearchBar.tsx` (150 LOC): 검색 입력 필드 + 자동완성 통합 로직
- `AutocompleteDropdown.tsx` (120 LOC): 드롭다운 컨테이너 + 위치 계산
- `SuggestionItem.tsx` (80 LOC): 개별 추천 항목 + 하이라이팅
- `SourceBadge.tsx` (40 LOC): 검색 소스 표시 (BigQuery/Vertex AI)

**Key Hooks**:
- `useAutocomplete.ts` (200 LOC): API 호출 + 상태 관리
- `useKeyboardNavigation.ts` (150 LOC): 키보드 이벤트 처리
- `useDebounce.ts` (30 LOC): Debouncing 유틸리티

**API Layer**:
- `lib/api/autocomplete.ts` (100 LOC): Fetch 래퍼 + 에러 핸들링
- `lib/utils/cache.ts` (80 LOC): In-memory 캐싱

### 1.3 번들 크기 예상

```
Initial Load (gzipped):
├── /search page:              ~ 145 KB
│   ├── Next.js runtime:       ~ 75 KB
│   ├── React 19:              ~ 42 KB
│   ├── SearchBar + Dropdown:  ~ 18 KB
│   └── Utilities:             ~ 10 KB
│
Code Split:
├── VideoPlayer (lazy):        ~ 35 KB
├── FilterSidebar (lazy):      ~ 25 KB
└── HandCardGrid (lazy):       ~ 20 KB

Total (initial):               ~ 145 KB ✅ (< 200 KB target)
```

---

## 2. 핵심 컴포넌트 설계

### 2.1 SearchBar Component

**책임**: 검색 입력 필드 + 자동완성 드롭다운 통합

#### 2.1.1 Props Interface

```typescript
// components/search/SearchBar.tsx
interface SearchBarProps {
  /**
   * 초기 검색어 (URL 파라미터에서 전달)
   * @default ""
   */
  initialQuery?: string;

  /**
   * 검색 실행 콜백 (Enter 키 또는 suggestion 선택 시)
   */
  onSearch?: (query: string) => void;

  /**
   * 자동완성 활성화 여부
   * @default true
   */
  enableAutocomplete?: boolean;

  /**
   * Placeholder 텍스트
   * @default "Search poker hands, players, tags..."
   */
  placeholder?: string;

  /**
   * 스타일 커스터마이징
   */
  className?: string;
}
```

#### 2.1.2 State Management

```typescript
interface SearchBarState {
  // User input value
  query: string;

  // Dropdown visibility
  isDropdownOpen: boolean;

  // Loading state (API fetching)
  isLoading: boolean;

  // Error state
  error: AutocompleteError | null;

  // Suggestions from API
  suggestions: Suggestion[];

  // Currently selected suggestion index (keyboard navigation)
  selectedIndex: number;

  // Source of suggestions (BigQuery or Vertex AI)
  source: "bigquery_cache" | "vertex_ai" | "hybrid";

  // API response time for SourceBadge
  responseTimeMs: number;
}
```

#### 2.1.3 Full Component Implementation

```typescript
"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { AutocompleteDropdown } from "./AutocompleteDropdown";
import { useAutocomplete } from "@/hooks/useAutocomplete";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useClickOutside } from "@/hooks/useClickOutside";
import { cn } from "@/lib/utils/cn";

export function SearchBar({
  initialQuery = "",
  onSearch,
  enableAutocomplete = true,
  placeholder = "Search poker hands, players, tags...",
  className
}: SearchBarProps) {
  // ----- State -----
  const [query, setQuery] = useState(initialQuery);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // ----- Refs -----
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // ----- Custom Hooks -----
  const {
    suggestions,
    isLoading,
    error,
    source,
    responseTimeMs
  } = useAutocomplete(query, { enabled: enableAutocomplete });

  const {
    selectedIndex,
    setSelectedIndex,
    handleKeyDown: handleKeyboardNavigation
  } = useKeyboardNavigation({
    items: suggestions,
    onSelect: handleSelectSuggestion,
    onClose: () => setIsDropdownOpen(false)
  });

  // Close dropdown when clicking outside
  useClickOutside(dropdownRef, () => setIsDropdownOpen(false));

  // ----- Event Handlers -----
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value;
    setQuery(newQuery);

    // Open dropdown if query is long enough
    if (newQuery.length >= 2 && enableAutocomplete) {
      setIsDropdownOpen(true);
    } else {
      setIsDropdownOpen(false);
    }

    // Reset selected index
    setSelectedIndex(-1);
  }, [enableAutocomplete, setSelectedIndex]);

  const handleInputFocus = useCallback(() => {
    // Open dropdown if there are cached suggestions
    if (query.length >= 2 && suggestions.length > 0 && enableAutocomplete) {
      setIsDropdownOpen(true);
    }
  }, [query, suggestions, enableAutocomplete]);

  const handleInputBlur = useCallback(() => {
    // Delay closing to allow suggestion clicks
    setTimeout(() => {
      setIsDropdownOpen(false);
    }, 200);
  }, []);

  const handleClear = useCallback(() => {
    setQuery("");
    setIsDropdownOpen(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  }, [setSelectedIndex]);

  function handleSelectSuggestion(suggestion: Suggestion) {
    setQuery(suggestion.text);
    setIsDropdownOpen(false);
    setSelectedIndex(-1);

    // Execute search
    if (onSearch) {
      onSearch(suggestion.text);
    }
  }

  const handleSearchSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();

    // If a suggestion is selected, use it
    if (selectedIndex >= 0 && suggestions[selectedIndex]) {
      handleSelectSuggestion(suggestions[selectedIndex]);
    } else {
      // Otherwise, search with current query
      if (onSearch && query.trim()) {
        onSearch(query);
      }
    }

    setIsDropdownOpen(false);
  }, [query, selectedIndex, suggestions, onSearch]);

  // ----- Keyboard Event Handler -----
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    // Delegate to keyboard navigation hook
    handleKeyboardNavigation(e);

    // Additional handling for Enter key
    if (e.key === "Enter" && !isDropdownOpen) {
      handleSearchSubmit(e as any);
    }
  }, [handleKeyboardNavigation, handleSearchSubmit, isDropdownOpen]);

  // ----- Auto-focus on mount (optional) -----
  useEffect(() => {
    if (initialQuery && inputRef.current) {
      inputRef.current.focus();
    }
  }, [initialQuery]);

  // ----- Render -----
  return (
    <div className={cn("relative w-full max-w-2xl mx-auto", className)}>
      {/* Search Form */}
      <form onSubmit={handleSearchSubmit} role="search">
        <div className="relative">
          {/* Search Icon */}
          <Search
            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground pointer-events-none"
            aria-hidden="true"
          />

          {/* Search Input */}
          <Input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={cn(
              "pl-12 pr-12 h-12 text-base rounded-lg",
              "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "transition-shadow duration-200"
            )}
            aria-label="Search poker hands, players, and tags"
            aria-describedby="search-hint"
            aria-autocomplete="list"
            aria-controls={isDropdownOpen ? "autocomplete-dropdown" : undefined}
            aria-expanded={isDropdownOpen}
            aria-activedescendant={
              selectedIndex >= 0 ? `suggestion-${selectedIndex}` : undefined
            }
            autoComplete="off"
            spellCheck={false}
          />

          {/* Loading Spinner */}
          {isLoading && (
            <Loader2
              className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 animate-spin text-muted-foreground"
              aria-label="Loading suggestions"
            />
          )}

          {/* Clear Button */}
          {!isLoading && query && (
            <button
              type="button"
              onClick={handleClear}
              className={cn(
                "absolute right-4 top-1/2 -translate-y-1/2",
                "w-6 h-6 flex items-center justify-center",
                "rounded-full hover:bg-muted transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              )}
              aria-label="Clear search"
              tabIndex={0}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Screen Reader Hint */}
        <div id="search-hint" className="sr-only">
          Type at least 2 characters to see suggestions. Use arrow keys to navigate,
          Enter to select.
        </div>
      </form>

      {/* Autocomplete Dropdown */}
      {isDropdownOpen && enableAutocomplete && (
        <AutocompleteDropdown
          ref={dropdownRef}
          id="autocomplete-dropdown"
          query={query}
          suggestions={suggestions}
          selectedIndex={selectedIndex}
          onSelectSuggestion={handleSelectSuggestion}
          onMouseEnterItem={setSelectedIndex}
          isLoading={isLoading}
          error={error}
          source={source}
          responseTimeMs={responseTimeMs}
        />
      )}
    </div>
  );
}
```

---

### 2.2 AutocompleteDropdown Component

**책임**: 추천 목록 드롭다운 + 위치 계산 + 애니메이션

#### 2.2.1 Props Interface

```typescript
// components/search/AutocompleteDropdown.tsx
interface AutocompleteDropdownProps {
  /**
   * Unique ID for ARIA (aria-controls)
   */
  id: string;

  /**
   * Current search query
   */
  query: string;

  /**
   * List of suggestions
   */
  suggestions: Suggestion[];

  /**
   * Currently selected suggestion index
   */
  selectedIndex: number;

  /**
   * Callback when a suggestion is selected
   */
  onSelectSuggestion: (suggestion: Suggestion) => void;

  /**
   * Callback when mouse enters a suggestion item
   */
  onMouseEnterItem: (index: number) => void;

  /**
   * Loading state
   */
  isLoading: boolean;

  /**
   * Error state
   */
  error: AutocompleteError | null;

  /**
   * Source of suggestions
   */
  source: "bigquery_cache" | "vertex_ai" | "hybrid";

  /**
   * API response time (milliseconds)
   */
  responseTimeMs: number;
}
```

#### 2.2.2 Full Component Implementation

```typescript
"use client";

import React, { forwardRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SuggestionList } from "./SuggestionList";
import { SourceBadge } from "./SourceBadge";
import { KeyboardHints } from "./KeyboardHints";
import { LoadingState } from "./LoadingState";
import { ValidationError } from "./errors/ValidationError";
import { RateLimitError } from "./errors/RateLimitError";
import { NetworkError } from "./errors/NetworkError";
import { NoResults } from "./errors/NoResults";
import { cn } from "@/lib/utils/cn";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

export const AutocompleteDropdown = forwardRef<
  HTMLDivElement,
  AutocompleteDropdownProps
>(
  (
    {
      id,
      query,
      suggestions,
      selectedIndex,
      onSelectSuggestion,
      onMouseEnterItem,
      isLoading,
      error,
      source,
      responseTimeMs
    },
    ref
  ) => {
    // ----- Render Error States -----
    if (error) {
      if (error.type === "validation") {
        return (
          <DropdownContainer ref={ref} id={id}>
            <ValidationError error={error} />
          </DropdownContainer>
        );
      }

      if (error.type === "rate_limit") {
        return (
          <DropdownContainer ref={ref} id={id}>
            <RateLimitError retryAfterSeconds={error.retryAfter || 60} />
          </DropdownContainer>
        );
      }

      if (error.type === "network") {
        return (
          <DropdownContainer ref={ref} id={id}>
            <NetworkError onRetry={() => window.location.reload()} />
          </DropdownContainer>
        );
      }
    }

    // ----- Render Loading State -----
    if (isLoading && suggestions.length === 0) {
      return (
        <DropdownContainer ref={ref} id={id}>
          <LoadingState />
        </DropdownContainer>
      );
    }

    // ----- Render No Results -----
    if (!isLoading && suggestions.length === 0 && query.length >= 2) {
      return (
        <DropdownContainer ref={ref} id={id}>
          <NoResults query={query} />
        </DropdownContainer>
      );
    }

    // ----- Render Suggestions -----
    return (
      <DropdownContainer ref={ref} id={id}>
        {/* Header: Source Badge */}
        <div className="px-4 py-2 flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {suggestions.length} suggestion{suggestions.length !== 1 ? "s" : ""}
          </span>
          <SourceBadge source={source} responseTimeMs={responseTimeMs} />
        </div>

        <Separator />

        {/* Suggestion List */}
        <ScrollArea className="max-h-[400px] md:max-h-[350px]">
          <SuggestionList
            suggestions={suggestions}
            query={query}
            selectedIndex={selectedIndex}
            onSelectSuggestion={onSelectSuggestion}
            onMouseEnterItem={onMouseEnterItem}
          />
        </ScrollArea>

        <Separator />

        {/* Footer: Keyboard Hints */}
        <div className="px-4 py-2">
          <KeyboardHints />
        </div>
      </DropdownContainer>
    );
  }
);

AutocompleteDropdown.displayName = "AutocompleteDropdown";

// ----- Dropdown Container (with animations) -----
interface DropdownContainerProps {
  id: string;
  children: React.ReactNode;
}

const DropdownContainer = forwardRef<HTMLDivElement, DropdownContainerProps>(
  ({ id, children }, ref) => {
    return (
      <motion.div
        ref={ref}
        id={id}
        role="listbox"
        aria-label="Search suggestions"
        className={cn(
          "absolute z-50 mt-2 w-full",
          "bg-popover text-popover-foreground",
          "border border-border rounded-lg shadow-lg",
          "overflow-hidden"
        )}
        initial={{ opacity: 0, y: -10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        transition={{ duration: 0.15, ease: "easeOut" }}
      >
        {children}
      </motion.div>
    );
  }
);

DropdownContainer.displayName = "DropdownContainer";
```

---

### 2.3 SuggestionItem Component

**책임**: 개별 추천 항목 + 텍스트 하이라이팅 + 선택 상태 표시

#### 2.3.1 Props Interface

```typescript
// components/search/SuggestionItem.tsx
interface SuggestionItemProps {
  /**
   * Suggestion data
   */
  suggestion: Suggestion;

  /**
   * Current search query (for highlighting)
   */
  query: string;

  /**
   * Whether this item is currently selected (keyboard navigation)
   */
  isSelected: boolean;

  /**
   * Item index (for ARIA)
   */
  index: number;

  /**
   * Click handler
   */
  onClick: () => void;

  /**
   * Mouse enter handler (for hover state)
   */
  onMouseEnter: () => void;
}
```

#### 2.3.2 Full Component Implementation

```typescript
"use client";

import React, { useRef, useEffect } from "react";
import { cn } from "@/lib/utils/cn";
import { highlightMatch } from "@/lib/utils/highlight";

export function SuggestionItem({
  suggestion,
  query,
  isSelected,
  index,
  onClick,
  onMouseEnter
}: SuggestionItemProps) {
  const itemRef = useRef<HTMLDivElement>(null);

  // ----- Auto-scroll into view when selected -----
  useEffect(() => {
    if (isSelected && itemRef.current) {
      itemRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
      });
    }
  }, [isSelected]);

  // ----- Render Icon -----
  const renderIcon = () => {
    if (suggestion.isTypoCorrected) {
      return (
        <span className="text-lg" aria-label="Typo corrected">
          ✨
        </span>
      );
    }

    // Icon based on suggestion type
    switch (suggestion.type) {
      case "player":
        return <span className="text-lg">👤</span>;
      case "tag":
        return <span className="text-lg">#️⃣</span>;
      case "tournament":
        return <span className="text-lg">🏆</span>;
      case "action":
        return <span className="text-lg">🎯</span>;
      default:
        return <span className="text-lg">🔍</span>;
    }
  };

  return (
    <div
      ref={itemRef}
      id={`suggestion-${index}`}
      role="option"
      aria-selected={isSelected}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      className={cn(
        // Base styles
        "flex items-center gap-3 px-4 py-3",
        "cursor-pointer transition-colors duration-150",
        "rounded-md mx-2 my-1",
        "min-h-[48px] md:min-h-[44px]", // Touch target size

        // Hover state
        "hover:bg-accent hover:text-accent-foreground",

        // Selected state (keyboard navigation)
        isSelected && "bg-accent text-accent-foreground",

        // Typo corrected special style
        suggestion.isTypoCorrected && "border-l-4 border-yellow-400"
      )}
    >
      {/* Icon */}
      <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center">
        {renderIcon()}
      </div>

      {/* Text with highlighting */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">
          {highlightMatch(suggestion.text, query)}
        </div>

        {/* Metadata (optional) */}
        {suggestion.metadata && (
          <div className="text-xs text-muted-foreground truncate mt-0.5">
            {suggestion.metadata}
          </div>
        )}
      </div>

      {/* Badge (optional) */}
      {suggestion.badge && (
        <div className="flex-shrink-0">
          <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
            {suggestion.badge}
          </span>
        </div>
      )}
    </div>
  );
}
```

---

### 2.4 SourceBadge Component

**책임**: 검색 소스 표시 (BigQuery 캐시 vs Vertex AI)

#### 2.4.1 Props Interface

```typescript
// components/search/SourceBadge.tsx
interface SourceBadgeProps {
  /**
   * Source of suggestions
   */
  source: "bigquery_cache" | "vertex_ai" | "hybrid";

  /**
   * API response time (milliseconds)
   */
  responseTimeMs: number;
}
```

#### 2.4.2 Full Component Implementation

```typescript
"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";

const SOURCE_CONFIG = {
  bigquery_cache: {
    icon: "💾",
    label: "Fast",
    color: "default" as const,
    description: "Cached results from BigQuery"
  },
  vertex_ai: {
    icon: "🤖",
    label: "AI-powered",
    color: "secondary" as const,
    description: "Semantic search via Vertex AI"
  },
  hybrid: {
    icon: "🧠",
    label: "Smart search",
    color: "outline" as const,
    description: "Combined cache + AI results"
  }
} as const;

export function SourceBadge({ source, responseTimeMs }: SourceBadgeProps) {
  const config = SOURCE_CONFIG[source];

  // Format response time
  const formattedTime =
    responseTimeMs < 100
      ? `${Math.round(responseTimeMs)}ms`
      : `${(responseTimeMs / 1000).toFixed(2)}s`;

  return (
    <Badge
      variant={config.color}
      className="text-xs gap-1"
      title={config.description}
    >
      <span role="img" aria-label={config.description}>
        {config.icon}
      </span>
      <span>{config.label}</span>
      <span className="text-muted-foreground">({formattedTime})</span>
    </Badge>
  );
}
```

---

## 3. 상태 관리 전략

### 3.1 선택된 접근: React Hooks Only (Option 1)

**근거**:
1. **단순성**: Autocomplete는 local state 중심 (global state 불필요)
2. **성능**: 상태 업데이트가 SearchBar 컴포넌트 내부로 제한됨
3. **번들 크기**: 추가 라이브러리 불필요 (Zustand/Redux 대비 ~10KB 절약)
4. **Next.js 15 호환**: Server Components와 자연스럽게 통합

**Trade-offs**:
- ✅ Pros: 간단, 빠른 개발, 낮은 학습 곡선
- ❌ Cons: 여러 컴포넌트에서 검색어 공유 시 prop drilling 발생 (현재는 해당 없음)

### 3.2 State Scope 정의

```typescript
// ----- Local State (Component-level) -----
// SearchBar 컴포넌트 내부에서만 사용
interface SearchBarLocalState {
  query: string;                  // 사용자 입력
  isDropdownOpen: boolean;        // 드롭다운 표시 여부
  selectedIndex: number;          // 키보드로 선택된 항목 인덱스
}

// ----- Server State (API responses) -----
// useAutocomplete 훅에서 관리
interface AutocompleteServerState {
  suggestions: Suggestion[];      // API 응답 데이터
  isLoading: boolean;             // API 호출 진행 중
  error: AutocompleteError | null; // API 에러
  source: "bigquery_cache" | "vertex_ai" | "hybrid";
  responseTimeMs: number;
}

// ----- URL State (for deep linking) -----
// Next.js searchParams로 관리 (optional)
interface URLState {
  q: string;                      // 검색어 (예: /search?q=Phil+Ivey)
}

// ----- Shared State (across multiple components, if needed) -----
// 현재는 불필요 (SearchBar가 독립적)
// 추후 필요 시 React Context 또는 Zustand 사용
```

### 3.3 State Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SearchBar Component                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Local State:                                                │
│  ┌────────────────────────────────────────────────────┐     │
│  │ query: ""                                          │     │
│  │ isDropdownOpen: false                              │     │
│  │ selectedIndex: -1                                  │     │
│  └────────────────────────────────────────────────────┘     │
│                          ↓                                   │
│  useAutocomplete(query)  ↓  (Custom Hook)                   │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Server State:                                      │     │
│  │ - suggestions: []                                  │     │
│  │ - isLoading: false                                 │     │
│  │ - error: null                                      │     │
│  │ - source: "bigquery_cache"                         │     │
│  │ - responseTimeMs: 0                                │     │
│  └────────────────────────────────────────────────────┘     │
│                          ↓                                   │
│  AutocompleteDropdown    ↓  (Child Component)               │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Props:                                             │     │
│  │ - suggestions (from parent)                        │     │
│  │ - selectedIndex (from parent)                      │     │
│  │ - onSelectSuggestion (callback to parent)          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘

State Flow:
User Input → query change → useDebounce(300ms) → API call
→ suggestions update → re-render dropdown
```

### 3.4 Cache Strategy

```typescript
// lib/utils/cache.ts
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresIn: number; // milliseconds
}

class InMemoryCache<T> {
  private cache = new Map<string, CacheEntry<T>>();

  set(key: string, data: T, expiresIn: number = 5 * 60 * 1000) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      expiresIn
    });
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    // Check if expired
    if (Date.now() - entry.timestamp > entry.expiresIn) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  clear() {
    this.cache.clear();
  }
}

// Usage in useAutocomplete hook
const cache = new InMemoryCache<AutocompleteResponse>();

async function fetchSuggestions(query: string): Promise<AutocompleteResponse> {
  // Check cache first
  const cached = cache.get(query);
  if (cached) {
    return cached;
  }

  // Fetch from API
  const response = await fetch(`/api/autocomplete?q=${query}`);
  const data = await response.json();

  // Store in cache
  cache.set(query, data, 5 * 60 * 1000); // 5 minutes TTL

  return data;
}
```

---

## 4. 데이터 플로우

### 4.1 Complete Data Flow Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          User Interaction                                  │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                      SearchBar Component                                   │
│                                                                            │
│  [1] User types "Phil"                                                     │
│      → onChange event                                                      │
│      → setQuery("Phil")                                                    │
│      → setIsDropdownOpen(true)                                             │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       useDebounce Hook                                     │
│                                                                            │
│  [2] Debounce query changes (300ms delay)                                 │
│      → query: "P" → (wait 300ms) → cancelled                              │
│      → query: "Ph" → (wait 300ms) → cancelled                             │
│      → query: "Phi" → (wait 300ms) → cancelled                            │
│      → query: "Phil" → (wait 300ms) → ✅ Proceed                          │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     useAutocomplete Hook                                   │
│                                                                            │
│  [3] Check minimum query length (>= 2 chars) ✅                           │
│      Check cache: cache.get("Phil") → null (cache miss)                   │
│      Create AbortController (for request cancellation)                    │
│      setIsLoading(true)                                                    │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          API Call                                          │
│                                                                            │
│  [4] GET /api/autocomplete?q=Phil&limit=5                                 │
│      Headers: { "Content-Type": "application/json" }                      │
│      Signal: abortController.signal (5s timeout)                          │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌───────────────────┐         ┌───────────────────────┐
        │  Success (200)    │         │  Error (4xx/5xx)      │
        └───────────────────┘         └───────────────────────┘
                    │                               │
                    ▼                               ▼
┌───────────────────────────────────┐   ┌─────────────────────────────────┐
│  Response:                        │   │  Error Handling:                │
│  {                                │   │                                 │
│    "suggestions": [               │   │  - 422: ValidationError         │
│      "Phil Ivey",                 │   │  - 429: RateLimitError          │
│      "Phil Hellmuth",             │   │  - 500: ServerError             │
│      "Philip Ng"                  │   │  - Network: NetworkError        │
│    ],                             │   │  - Timeout: TimeoutError        │
│    "query": "Phil",               │   │                                 │
│    "source": "bigquery_cache",    │   │  setState({ error: ... })       │
│    "response_time_ms": 45,        │   │  setIsLoading(false)            │
│    "total": 3                     │   │                                 │
│  }                                │   │                                 │
│                                   │   └─────────────────────────────────┘
│  [5] Parse response               │
│      Validate data                │
│      Store in cache               │
│      setState({                   │
│        suggestions: [...],        │
│        source: "bigquery_cache",  │
│        responseTimeMs: 45,        │
│        isLoading: false,          │
│        error: null                │
│      })                           │
└───────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    Re-render Triggered                                     │
│                                                                            │
│  [6] SearchBar re-renders with new suggestions                            │
│      AutocompleteDropdown receives updated props:                         │
│      - suggestions: ["Phil Ivey", "Phil Hellmuth", "Philip Ng"]          │
│      - source: "bigquery_cache"                                           │
│      - responseTimeMs: 45                                                  │
└───────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                AutocompleteDropdown Component                              │
│                                                                            │
│  [7] Render suggestion list with animations (Framer Motion)               │
│      ┌────────────────────────────────────────────────┐                   │
│      │ 💾 Fast (45ms)                    [SourceBadge]│                   │
│      ├────────────────────────────────────────────────┤                   │
│      │ 👤 Phil Ivey                    [SuggestionItem]│ ← Highlighted    │
│      │ 👤 Phil Hellmuth                [SuggestionItem]│                   │
│      │ 👤 Philip Ng                    [SuggestionItem]│                   │
│      ├────────────────────────────────────────────────┤                   │
│      │ ↑↓ Navigate • Enter Select • Esc Close         │                   │
│      └────────────────────────────────────────────────┘                   │
└───────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     User Selects Suggestion                                │
│                                                                            │
│  [8] User clicks "Phil Ivey" or presses Enter                             │
│      → onSelectSuggestion("Phil Ivey")                                    │
│      → setQuery("Phil Ivey")                                              │
│      → setIsDropdownOpen(false)                                           │
│      → onSearch("Phil Ivey") ← Execute search                             │
└───────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    Navigate to Search Results                              │
│                                                                            │
│  [9] router.push("/search?q=Phil+Ivey")                                   │
│      → Load search results page                                           │
│      → Display HandCardGrid with filtered results                         │
└───────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Error Handling Flow

```
API Call Failed
    │
    ├─→ Network Error (fetch failed)
    │   → Display NetworkError component
    │   → Show "Retry" button
    │
    ├─→ Rate Limit (429)
    │   → Display RateLimitError component
    │   → Show countdown timer (60s)
    │   → Auto-retry after cooldown
    │
    ├─→ Validation Error (422)
    │   → Display ValidationError component
    │   → Show specific invalid characters
    │   → Keep dropdown open for correction
    │
    ├─→ Timeout (5s exceeded)
    │   → Display TimeoutError component
    │   → Show "Retry" button
    │   → Suggest checking connection
    │
    └─→ Server Error (500)
        → Display ServerError component
        → Show "Try again later" message
        → Auto-retry after 3 seconds (max 3 retries)
```

### 4.3 Cache Flow

```
Query Entered
    │
    ▼
Check Cache
    │
    ├─→ Cache Hit (fresh data, < 5 min old)
    │   → Return cached suggestions immediately
    │   → Display "💾 Cached" badge
    │   → Skip API call (performance optimization)
    │
    └─→ Cache Miss or Expired
        → Proceed to API call
        → Store response in cache (TTL: 5 min)
        → Display source badge (BigQuery/Vertex AI)
```

---

## 5. API 통합 패턴

### 5.1 API Client Implementation

```typescript
// lib/api/client.ts
/**
 * Base fetch wrapper with error handling, timeouts, and retries
 */

interface FetchOptions extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public type: "validation" | "rate_limit" | "network" | "server" | "timeout",
    public retryAfter?: number
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const {
    timeout = 5000,
    retries = 0,
    retryDelay = 1000,
    ...fetchOptions
  } = options;

  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    // Handle HTTP errors
    if (!response.ok) {
      if (response.status === 422) {
        const error = await response.json();
        throw new APIError(
          error.message || "Invalid query format",
          422,
          "validation"
        );
      }

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get("Retry-After") || "60");
        throw new APIError(
          "Too many requests. Please wait.",
          429,
          "rate_limit",
          retryAfter
        );
      }

      if (response.status >= 500) {
        throw new APIError(
          "Server error. Please try again later.",
          response.status,
          "server"
        );
      }

      throw new APIError(
        `HTTP error ${response.status}`,
        response.status,
        "network"
      );
    }

    return response;
  } catch (error) {
    clearTimeout(timeoutId);

    // Handle timeout
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new APIError("Request timed out", 0, "timeout");
    }

    // Handle network errors
    if (error instanceof TypeError) {
      throw new APIError("Network error. Check your connection.", 0, "network");
    }

    // Retry logic for server errors
    if (error instanceof APIError && error.type === "server" && retries > 0) {
      await new Promise(resolve => setTimeout(resolve, retryDelay));
      return fetchWithTimeout(url, { ...options, retries: retries - 1 });
    }

    throw error;
  }
}

export { fetchWithTimeout };
```

### 5.2 Autocomplete API Client

```typescript
// lib/api/autocomplete.ts
import { fetchWithTimeout, APIError } from "./client";
import { InMemoryCache } from "../utils/cache";

/**
 * Autocomplete API client with caching and error handling
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const cache = new InMemoryCache<AutocompleteResponse>();

export interface AutocompleteOptions {
  limit?: number;
  timeout?: number;
  signal?: AbortSignal;
}

export interface AutocompleteResponse {
  suggestions: Suggestion[];
  query: string;
  source: "bigquery_cache" | "vertex_ai" | "hybrid";
  response_time_ms: number;
  total: number;
}

export interface Suggestion {
  text: string;
  type: "player" | "tag" | "tournament" | "action" | "general";
  isTypoCorrected?: boolean;
  metadata?: string;
  badge?: string;
}

export interface AutocompleteError {
  type: "validation" | "rate_limit" | "network" | "server" | "timeout";
  message: string;
  retryAfter?: number;
}

/**
 * Fetch autocomplete suggestions
 */
export async function fetchAutocomplete(
  query: string,
  options: AutocompleteOptions = {}
): Promise<AutocompleteResponse> {
  const { limit = 5, timeout = 5000, signal } = options;

  // Validate query
  if (query.length < 2) {
    throw new APIError("Query must be at least 2 characters", 422, "validation");
  }

  // Check cache
  const cacheKey = `${query}:${limit}`;
  const cached = cache.get(cacheKey);
  if (cached) {
    return cached;
  }

  // Build URL
  const url = new URL(`${API_BASE_URL}/api/autocomplete`);
  url.searchParams.set("q", query);
  url.searchParams.set("limit", limit.toString());

  // Fetch from API
  const startTime = performance.now();

  try {
    const response = await fetchWithTimeout(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      },
      timeout,
      retries: 2,
      retryDelay: 1000,
      signal
    });

    const data: AutocompleteResponse = await response.json();

    // Add client-side response time if not provided
    if (!data.response_time_ms) {
      data.response_time_ms = performance.now() - startTime;
    }

    // Validate response structure
    if (!data.suggestions || !Array.isArray(data.suggestions)) {
      throw new Error("Invalid response format");
    }

    // Store in cache (5 minutes TTL)
    cache.set(cacheKey, data, 5 * 60 * 1000);

    return data;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    // Wrap unknown errors
    throw new APIError(
      error instanceof Error ? error.message : "Unknown error",
      0,
      "network"
    );
  }
}

/**
 * Clear autocomplete cache
 */
export function clearAutocompleteCache() {
  cache.clear();
}
```

### 5.3 useAutocomplete Hook

```typescript
// hooks/useAutocomplete.ts
import { useState, useEffect, useRef } from "react";
import { useDebounce } from "./useDebounce";
import {
  fetchAutocomplete,
  AutocompleteResponse,
  AutocompleteError,
  Suggestion
} from "@/lib/api/autocomplete";

interface UseAutocompleteOptions {
  /**
   * Enable/disable autocomplete
   * @default true
   */
  enabled?: boolean;

  /**
   * Debounce delay (milliseconds)
   * @default 300
   */
  debounceMs?: number;

  /**
   * Number of suggestions to fetch
   * @default 5
   */
  limit?: number;

  /**
   * API timeout (milliseconds)
   * @default 5000
   */
  timeout?: number;
}

interface UseAutocompleteReturn {
  suggestions: Suggestion[];
  isLoading: boolean;
  error: AutocompleteError | null;
  source: "bigquery_cache" | "vertex_ai" | "hybrid";
  responseTimeMs: number;
  total: number;
  retry: () => void;
}

export function useAutocomplete(
  query: string,
  options: UseAutocompleteOptions = {}
): UseAutocompleteReturn {
  const {
    enabled = true,
    debounceMs = 300,
    limit = 5,
    timeout = 5000
  } = options;

  const [state, setState] = useState<{
    suggestions: Suggestion[];
    isLoading: boolean;
    error: AutocompleteError | null;
    source: "bigquery_cache" | "vertex_ai" | "hybrid";
    responseTimeMs: number;
    total: number;
  }>({
    suggestions: [],
    isLoading: false,
    error: null,
    source: "bigquery_cache",
    responseTimeMs: 0,
    total: 0
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const debouncedQuery = useDebounce(query, debounceMs);

  // Fetch suggestions
  const fetchSuggestions = async (q: string) => {
    // Cancel previous request
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetchAutocomplete(q, {
        limit,
        timeout,
        signal: abortControllerRef.current.signal
      });

      setState({
        suggestions: response.suggestions,
        isLoading: false,
        error: null,
        source: response.source,
        responseTimeMs: response.response_time_ms,
        total: response.total
      });
    } catch (error: any) {
      // Ignore abort errors
      if (error.name === "AbortError") {
        return;
      }

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: {
          type: error.type || "network",
          message: error.message,
          retryAfter: error.retryAfter
        }
      }));
    }
  };

  // Effect: Fetch on debounced query change
  useEffect(() => {
    if (!enabled) {
      setState(prev => ({ ...prev, suggestions: [], isLoading: false }));
      return;
    }

    if (debouncedQuery.length < 2) {
      setState(prev => ({ ...prev, suggestions: [], isLoading: false }));
      return;
    }

    fetchSuggestions(debouncedQuery);

    // Cleanup
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [debouncedQuery, enabled, limit, timeout]);

  // Retry function
  const retry = () => {
    if (debouncedQuery.length >= 2) {
      fetchSuggestions(debouncedQuery);
    }
  };

  return {
    ...state,
    retry
  };
}
```

---

## 6. TypeScript 타입 정의

### 6.1 Autocomplete Types

```typescript
// types/autocomplete.ts

/**
 * Suggestion item returned by autocomplete API
 */
export interface Suggestion {
  /**
   * Suggestion text (e.g., "Phil Ivey")
   */
  text: string;

  /**
   * Type of suggestion
   */
  type: SuggestionType;

  /**
   * Whether this suggestion is a typo correction
   * @default false
   */
  isTypoCorrected?: boolean;

  /**
   * Additional metadata (e.g., "10-time bracelet winner")
   */
  metadata?: string;

  /**
   * Badge text (e.g., "WSOP Champion")
   */
  badge?: string;

  /**
   * Unique identifier (for React key)
   */
  id?: string;
}

export type SuggestionType =
  | "player"      // Player name (e.g., "Phil Ivey")
  | "tag"         // Hand tag (e.g., "#HERO_CALL")
  | "tournament"  // Tournament name (e.g., "WSOP 2024")
  | "action"      // Poker action (e.g., "bluff")
  | "general";    // General search term

/**
 * Autocomplete API response
 */
export interface AutocompleteResponse {
  /**
   * List of suggestions
   */
  suggestions: Suggestion[];

  /**
   * Original query
   */
  query: string;

  /**
   * Source of suggestions
   */
  source: AutocompleteSource;

  /**
   * API response time (milliseconds)
   */
  response_time_ms: number;

  /**
   * Total number of suggestions available
   */
  total: number;
}

export type AutocompleteSource =
  | "bigquery_cache"  // Fast lookup from BigQuery cache
  | "vertex_ai"       // Semantic search via Vertex AI
  | "hybrid";         // Combined BigQuery + Vertex AI

/**
 * Autocomplete error
 */
export interface AutocompleteError {
  /**
   * Error type
   */
  type: AutocompleteErrorType;

  /**
   * Error message
   */
  message: string;

  /**
   * Retry after N seconds (for rate limit errors)
   */
  retryAfter?: number;

  /**
   * Invalid characters (for validation errors)
   */
  invalidChars?: string[];
}

export type AutocompleteErrorType =
  | "validation"   // Invalid query format (422)
  | "rate_limit"   // Too many requests (429)
  | "network"      // Network connection failed
  | "server"       // Server error (500+)
  | "timeout";     // Request timed out
```

### 6.2 Component Props Types

```typescript
// types/components.ts

import { Suggestion, AutocompleteError, AutocompleteSource } from "./autocomplete";

/**
 * SearchBar component props
 */
export interface SearchBarProps {
  initialQuery?: string;
  onSearch?: (query: string) => void;
  enableAutocomplete?: boolean;
  placeholder?: string;
  className?: string;
}

/**
 * AutocompleteDropdown component props
 */
export interface AutocompleteDropdownProps {
  id: string;
  query: string;
  suggestions: Suggestion[];
  selectedIndex: number;
  onSelectSuggestion: (suggestion: Suggestion) => void;
  onMouseEnterItem: (index: number) => void;
  isLoading: boolean;
  error: AutocompleteError | null;
  source: AutocompleteSource;
  responseTimeMs: number;
}

/**
 * SuggestionItem component props
 */
export interface SuggestionItemProps {
  suggestion: Suggestion;
  query: string;
  isSelected: boolean;
  index: number;
  onClick: () => void;
  onMouseEnter: () => void;
}

/**
 * SourceBadge component props
 */
export interface SourceBadgeProps {
  source: AutocompleteSource;
  responseTimeMs: number;
}

/**
 * Error component props
 */
export interface ErrorComponentProps {
  error?: AutocompleteError;
  query?: string;
  onRetry?: () => void;
  retryAfterSeconds?: number;
}
```

### 6.3 Hook Types

```typescript
// types/hooks.ts

import { Suggestion, AutocompleteError, AutocompleteSource } from "./autocomplete";

/**
 * useAutocomplete hook options
 */
export interface UseAutocompleteOptions {
  enabled?: boolean;
  debounceMs?: number;
  limit?: number;
  timeout?: number;
}

/**
 * useAutocomplete hook return type
 */
export interface UseAutocompleteReturn {
  suggestions: Suggestion[];
  isLoading: boolean;
  error: AutocompleteError | null;
  source: AutocompleteSource;
  responseTimeMs: number;
  total: number;
  retry: () => void;
}

/**
 * useKeyboardNavigation hook options
 */
export interface UseKeyboardNavigationOptions {
  items: Suggestion[];
  onSelect: (suggestion: Suggestion) => void;
  onClose: () => void;
  loop?: boolean; // Whether to loop from last to first item
}

/**
 * useKeyboardNavigation hook return type
 */
export interface UseKeyboardNavigationReturn {
  selectedIndex: number;
  setSelectedIndex: (index: number) => void;
  handleKeyDown: (e: React.KeyboardEvent) => void;
}

/**
 * useDebounce hook return type
 */
export type UseDebouncedValue<T> = T;

/**
 * useClickOutside hook callback
 */
export type ClickOutsideHandler = () => void;
```

### 6.4 API Types

```typescript
// types/api.ts

/**
 * Base API response wrapper
 */
export interface APIResponse<T> {
  data: T;
  status: number;
  message?: string;
}

/**
 * API error response
 */
export interface APIErrorResponse {
  error: string;
  message: string;
  status: number;
  details?: Record<string, any>;
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/**
 * Search results response
 */
export interface SearchResultsResponse {
  hands: Hand[];
  pagination: PaginationMeta;
  query: string;
  filters: SearchFilters;
}

/**
 * Hand data (simplified)
 */
export interface Hand {
  hand_id: string;
  tournament_id: string;
  hero_name: string;
  villain_name: string;
  pot_bb: number;
  description: string;
  tags: string[];
  video_url: string;
  thumbnail_url: string;
}

/**
 * Search filters
 */
export interface SearchFilters {
  minPotBB?: number;
  maxPotBB?: number;
  tags?: string[];
  tournament?: string;
  players?: string[];
}
```

---

## 7. 접근성 구현

### 7.1 ARIA Combobox Pattern

```typescript
// components/search/SearchBar.tsx (ARIA attributes)

<div role="combobox" aria-expanded={isDropdownOpen} aria-haspopup="listbox">
  <input
    ref={inputRef}
    type="text"
    role="searchbox"
    aria-label="Search poker hands, players, and tags"
    aria-describedby="search-hint"
    aria-autocomplete="list"
    aria-controls={isDropdownOpen ? "autocomplete-dropdown" : undefined}
    aria-expanded={isDropdownOpen}
    aria-activedescendant={
      selectedIndex >= 0 ? `suggestion-${selectedIndex}` : undefined
    }
    value={query}
    onChange={handleInputChange}
  />

  <div id="search-hint" className="sr-only">
    Type at least 2 characters to see suggestions. Use arrow keys to navigate,
    Enter to select, Escape to close.
  </div>
</div>
```

### 7.2 Keyboard Navigation Implementation

```typescript
// hooks/useKeyboardNavigation.ts

import { useState, useCallback } from "react";
import { Suggestion } from "@/types/autocomplete";

interface UseKeyboardNavigationOptions {
  items: Suggestion[];
  onSelect: (suggestion: Suggestion) => void;
  onClose: () => void;
  loop?: boolean;
}

export function useKeyboardNavigation({
  items,
  onSelect,
  onClose,
  loop = false
}: UseKeyboardNavigationOptions) {
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex(prev => {
            if (prev < items.length - 1) {
              return prev + 1;
            }
            return loop ? 0 : prev;
          });
          break;

        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex(prev => {
            if (prev > 0) {
              return prev - 1;
            }
            return loop ? items.length - 1 : -1;
          });
          break;

        case "Enter":
          e.preventDefault();
          if (selectedIndex >= 0 && items[selectedIndex]) {
            onSelect(items[selectedIndex]);
          }
          break;

        case "Escape":
          e.preventDefault();
          onClose();
          setSelectedIndex(-1);
          break;

        case "Tab":
          e.preventDefault();
          if (items.length > 0) {
            onSelect(items[0]); // Auto-complete first suggestion
          }
          break;

        case "Home":
          e.preventDefault();
          setSelectedIndex(0);
          break;

        case "End":
          e.preventDefault();
          setSelectedIndex(items.length - 1);
          break;

        default:
          break;
      }
    },
    [items, selectedIndex, onSelect, onClose, loop]
  );

  return {
    selectedIndex,
    setSelectedIndex,
    handleKeyDown
  };
}
```

### 7.3 Focus Management

```typescript
// hooks/useFocusManagement.ts

import { useEffect, useRef } from "react";

/**
 * Manage focus when dropdown opens/closes
 */
export function useFocusManagement(isOpen: boolean) {
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      // Store currently focused element
      previousFocusRef.current = document.activeElement as HTMLElement;
    } else {
      // Restore focus when closing
      if (previousFocusRef.current && previousFocusRef.current.focus) {
        previousFocusRef.current.focus();
      }
    }
  }, [isOpen]);
}

/**
 * Trap focus within dropdown (for modal-like behavior)
 */
export function useFocusTrap(
  containerRef: React.RefObject<HTMLElement>,
  isActive: boolean
) {
  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;

      if (e.shiftKey) {
        // Shift + Tab (backwards)
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab (forwards)
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener("keydown", handleTabKey);

    return () => {
      document.removeEventListener("keydown", handleTabKey);
    };
  }, [containerRef, isActive]);
}
```

### 7.4 Screen Reader Announcements

```typescript
// components/search/LiveRegion.tsx

"use client";

import React, { useEffect, useState } from "react";

interface LiveRegionProps {
  message: string;
  type?: "polite" | "assertive";
}

/**
 * Live region for screen reader announcements
 */
export function LiveRegion({ message, type = "polite" }: LiveRegionProps) {
  const [announcement, setAnnouncement] = useState("");

  useEffect(() => {
    // Delay announcement to ensure screen reader picks it up
    const timer = setTimeout(() => {
      setAnnouncement(message);
    }, 100);

    return () => clearTimeout(timer);
  }, [message]);

  return (
    <div
      role="status"
      aria-live={type}
      aria-atomic="true"
      className="sr-only"
    >
      {announcement}
    </div>
  );
}

// Usage in AutocompleteDropdown
{isLoading && <LiveRegion message="Loading suggestions..." />}
{!isLoading && total > 0 && (
  <LiveRegion message={`${total} suggestions found`} />
)}
{!isLoading && total === 0 && (
  <LiveRegion message="No suggestions found" />
)}
```

### 7.5 Accessibility Checklist

```typescript
/**
 * Accessibility Checklist (WCAG 2.1 AA)
 *
 * Perceivable:
 * [x] Color contrast ratio ≥ 4.5:1 for normal text
 * [x] Color contrast ratio ≥ 3:1 for large text
 * [x] Icons have aria-label or aria-hidden
 * [x] Text zoom up to 200% without loss of functionality
 *
 * Operable:
 * [x] All functionality available via keyboard
 * [x] Focus indicators visible (3px ring)
 * [x] No keyboard traps
 * [x] Skip links provided (Ctrl+K to search)
 *
 * Understandable:
 * [x] All inputs have labels or aria-label
 * [x] Error messages are clear and specific
 * [x] Consistent navigation patterns
 * [x] Help text provided (placeholder + aria-describedby)
 *
 * Robust:
 * [x] Valid HTML structure
 * [x] ARIA roles, states, and properties correctly used
 * [x] Compatible with screen readers (NVDA, JAWS, VoiceOver)
 * [x] No console errors or warnings
 */
```

---

## 8. 성능 최적화

### 8.1 React.memo for Component Memoization

```typescript
// components/search/SuggestionItem.tsx

import React, { memo } from "react";

export const SuggestionItem = memo<SuggestionItemProps>(
  ({ suggestion, query, isSelected, index, onClick, onMouseEnter }) => {
    // Component implementation...
  },
  (prevProps, nextProps) => {
    // Custom comparison function
    return (
      prevProps.suggestion.text === nextProps.suggestion.text &&
      prevProps.isSelected === nextProps.isSelected &&
      prevProps.query === nextProps.query
    );
  }
);

SuggestionItem.displayName = "SuggestionItem";
```

### 8.2 useMemo and useCallback

```typescript
// components/search/SearchBar.tsx

const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
  setQuery(e.target.value);
  // ... rest of logic
}, []);

const filteredSuggestions = useMemo(() => {
  // Expensive filtering operation (if needed)
  return suggestions.filter(s => s.text.toLowerCase().includes(query.toLowerCase()));
}, [suggestions, query]);

const highlightedText = useMemo(() => {
  return highlightMatch(suggestion.text, query);
}, [suggestion.text, query]);
```

### 8.3 Code Splitting

```typescript
// app/search/page.tsx

import dynamic from "next/dynamic";
import { Suspense } from "react";
import { SearchBar } from "@/components/search/SearchBar";
import { HandCardGridSkeleton } from "@/components/hand/HandCardGridSkeleton";

// Lazy load heavy components
const HandCardGrid = dynamic(() => import("@/components/hand/HandCardGrid"), {
  loading: () => <HandCardGridSkeleton />,
  ssr: false
});

const FilterSidebar = dynamic(() => import("@/components/FilterSidebar"), {
  loading: () => <div>Loading filters...</div>
});

export default function SearchPage() {
  return (
    <div>
      {/* SearchBar loads immediately (critical) */}
      <SearchBar />

      {/* HandCardGrid loads on demand */}
      <Suspense fallback={<HandCardGridSkeleton />}>
        <HandCardGrid />
      </Suspense>

      {/* FilterSidebar loads on demand */}
      <Suspense fallback={<div>Loading...</div>}>
        <FilterSidebar />
      </Suspense>
    </div>
  );
}
```

### 8.4 Virtual Scrolling (for 100+ suggestions)

```typescript
// components/search/VirtualSuggestionList.tsx

import { useVirtualizer } from "@tanstack/react-virtual";
import { useRef } from "react";

interface VirtualSuggestionListProps {
  suggestions: Suggestion[];
  query: string;
  selectedIndex: number;
  onSelectSuggestion: (suggestion: Suggestion) => void;
}

export function VirtualSuggestionList({
  suggestions,
  query,
  selectedIndex,
  onSelectSuggestion
}: VirtualSuggestionListProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: suggestions.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 48, // Each item ~48px
    overscan: 5 // Render 5 extra items above/below viewport
  });

  return (
    <div
      ref={parentRef}
      className="max-h-[400px] overflow-auto"
      role="listbox"
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: "relative"
        }}
      >
        {virtualizer.getVirtualItems().map(virtualItem => {
          const suggestion = suggestions[virtualItem.index];
          const isSelected = virtualItem.index === selectedIndex;

          return (
            <div
              key={virtualItem.key}
              data-index={virtualItem.index}
              ref={virtualizer.measureElement}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                transform: `translateY(${virtualItem.start}px)`
              }}
            >
              <SuggestionItem
                suggestion={suggestion}
                query={query}
                isSelected={isSelected}
                index={virtualItem.index}
                onClick={() => onSelectSuggestion(suggestion)}
                onMouseEnter={() => {}}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

### 8.5 Image Optimization

```typescript
// components/hand/HandCard.tsx

import Image from "next/image";

export function HandCard({ hand }: { hand: Hand }) {
  return (
    <div className="hand-card">
      <Image
        src={hand.thumbnail_url}
        alt={`${hand.hero_name} vs ${hand.villain_name}`}
        width={400}
        height={225}
        placeholder="blur"
        blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/..."
        loading="lazy"
        sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
        className="rounded-t-lg object-cover"
      />
      {/* Rest of card content */}
    </div>
  );
}
```

### 8.6 Bundle Size Analysis

```bash
# Analyze bundle size
npm run build
npm run analyze

# Expected output:
# Route (app)                              Size     First Load JS
# ┌ ○ /                                    142 B          87.3 kB
# ├ ○ /search                              2.45 kB        145 kB
# ├ ○ /hand/[id]                           1.82 kB        120 kB
# └ ○ /_not-found                          871 B          84.1 kB

# First Load JS shared by all              82.2 kB
#   ├ chunks/framework-[hash].js           45.2 kB
#   ├ chunks/main-app-[hash].js            224 B
#   └ other shared chunks (total)          37.8 kB
```

### 8.7 Performance Monitoring

```typescript
// lib/performance.ts

/**
 * Report Web Vitals to analytics
 */
export function reportWebVitals(metric: any) {
  const { id, name, label, value } = metric;

  // Send to analytics (e.g., Google Analytics, Vercel Analytics)
  if (window.gtag) {
    window.gtag("event", name, {
      event_category: label === "web-vital" ? "Web Vitals" : "Next.js custom metric",
      event_label: id,
      value: Math.round(name === "CLS" ? value * 1000 : value),
      non_interaction: true
    });
  }

  // Log to console in development
  if (process.env.NODE_ENV === "development") {
    console.log(`[Performance] ${name}:`, value);
  }
}

// app/layout.tsx
import { reportWebVitals } from "@/lib/performance";

export { reportWebVitals };
```

---

## 9. 테스트 전략

### 9.1 Unit Tests (Jest + React Testing Library)

```typescript
// __tests__/hooks/useDebounce.test.ts

import { renderHook, waitFor } from "@testing-library/react";
import { useDebounce } from "@/hooks/useDebounce";

describe("useDebounce", () => {
  jest.useFakeTimers();

  it("should return initial value immediately", () => {
    const { result } = renderHook(() => useDebounce("test", 300));
    expect(result.current).toBe("test");
  });

  it("should debounce value changes", async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "initial", delay: 300 } }
    );

    expect(result.current).toBe("initial");

    // Change value
    rerender({ value: "updated", delay: 300 });
    expect(result.current).toBe("initial"); // Still old value

    // Fast forward time
    jest.advanceTimersByTime(300);

    await waitFor(() => {
      expect(result.current).toBe("updated");
    });
  });

  it("should cancel pending debounce on unmount", () => {
    const { result, unmount, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "initial", delay: 300 } }
    );

    rerender({ value: "updated", delay: 300 });
    unmount();

    jest.advanceTimersByTime(300);
    expect(result.current).toBe("initial"); // Should not update after unmount
  });
});
```

### 9.2 Component Tests

```typescript
// __tests__/components/SearchBar.test.tsx

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SearchBar } from "@/components/search/SearchBar";
import { rest } from "msw";
import { setupServer } from "msw/node";

// Mock API server
const server = setupServer(
  rest.get("/api/autocomplete", (req, res, ctx) => {
    const query = req.url.searchParams.get("q");
    return res(
      ctx.json({
        suggestions: [
          { text: "Phil Ivey", type: "player" },
          { text: "Phil Hellmuth", type: "player" },
          { text: "Philip Ng", type: "player" }
        ],
        query,
        source: "bigquery_cache",
        response_time_ms: 45,
        total: 3
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("SearchBar", () => {
  it("should render search input", () => {
    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute("placeholder");
  });

  it("should show dropdown when typing at least 2 characters", async () => {
    render(<SearchBar />);
    const input = screen.getByRole("searchbox");

    // Type "Ph" (not enough)
    await userEvent.type(input, "P");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();

    // Type "Ph" (enough)
    await userEvent.type(input, "h");
    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });
  });

  it("should display suggestions from API", async () => {
    render(<SearchBar />);
    const input = screen.getByRole("searchbox");

    await userEvent.type(input, "Phil");

    await waitFor(() => {
      expect(screen.getByText("Phil Ivey")).toBeInTheDocument();
      expect(screen.getByText("Phil Hellmuth")).toBeInTheDocument();
      expect(screen.getByText("Philip Ng")).toBeInTheDocument();
    });
  });

  it("should highlight matching characters", async () => {
    render(<SearchBar />);
    const input = screen.getByRole("searchbox");

    await userEvent.type(input, "Phil");

    await waitFor(() => {
      const highlighted = screen.getByText("Phil", { selector: "mark" });
      expect(highlighted).toHaveClass("bg-yellow-200");
    });
  });

  it("should select suggestion on click", async () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} />);
    const input = screen.getByRole("searchbox");

    await userEvent.type(input, "Phil");

    await waitFor(() => {
      const suggestion = screen.getByText("Phil Ivey");
      fireEvent.click(suggestion);
    });

    expect(input).toHaveValue("Phil Ivey");
    expect(onSearch).toHaveBeenCalledWith("Phil Ivey");
  });

  it("should select suggestion on Enter key", async () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} />);
    const input = screen.getByRole("searchbox");

    await userEvent.type(input, "Phil");

    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });

    // Press ArrowDown to select first suggestion
    fireEvent.keyDown(input, { key: "ArrowDown" });

    // Press Enter
    fireEvent.keyDown(input, { key: "Enter" });

    expect(input).toHaveValue("Phil Ivey");
    expect(onSearch).toHaveBeenCalledWith("Phil Ivey");
  });

  it("should close dropdown on Escape key", async () => {
    render(<SearchBar />);
    const input = screen.getByRole("searchbox");

    await userEvent.type(input, "Phil");

    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: "Escape" });

    await waitFor(() => {
      expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    });
  });

  it("should clear input on clear button click", async () => {
    render(<SearchBar />);
    const input = screen.getByRole("searchbox");

    await userEvent.type(input, "Phil");
    expect(input).toHaveValue("Phil");

    const clearButton = screen.getByLabelText("Clear search");
    fireEvent.click(clearButton);

    expect(input).toHaveValue("");
  });

  it("should handle API errors gracefully", async () => {
    server.use(
      rest.get("/api/autocomplete", (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: "Server error" }));
      })
    );

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");

    await userEvent.type(input, "Phil");

    await waitFor(() => {
      expect(screen.getByText(/Server error/i)).toBeInTheDocument();
    });
  });
});
```

### 9.3 E2E Tests (Playwright)

```typescript
// __tests__/e2e/autocomplete.spec.ts

import { test, expect } from "@playwright/test";

test.describe("Autocomplete E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/search");
  });

  test("should show suggestions when typing", async ({ page }) => {
    const searchInput = page.getByRole("searchbox");

    await searchInput.fill("Phil");

    await expect(page.getByRole("listbox")).toBeVisible();
    await expect(page.getByText("Phil Ivey")).toBeVisible();
    await expect(page.getByText("Phil Hellmuth")).toBeVisible();
  });

  test("should navigate suggestions with keyboard", async ({ page }) => {
    const searchInput = page.getByRole("searchbox");

    await searchInput.fill("Phil");
    await page.waitForSelector('[role="listbox"]');

    // Press ArrowDown
    await page.keyboard.press("ArrowDown");

    // First suggestion should be selected
    const firstSuggestion = page.getByRole("option", { selected: true });
    await expect(firstSuggestion).toHaveText("Phil Ivey");

    // Press ArrowDown again
    await page.keyboard.press("ArrowDown");

    // Second suggestion should be selected
    const secondSuggestion = page.getByRole("option", { selected: true });
    await expect(secondSuggestion).toHaveText("Phil Hellmuth");

    // Press Enter
    await page.keyboard.press("Enter");

    // Input should have selected value
    await expect(searchInput).toHaveValue("Phil Hellmuth");
  });

  test("should execute search on Enter", async ({ page }) => {
    const searchInput = page.getByRole("searchbox");

    await searchInput.fill("Phil Ivey");
    await page.keyboard.press("Enter");

    // Should navigate to search results
    await expect(page).toHaveURL(/\/search\?q=Phil\+Ivey/);

    // Results should be displayed
    await expect(page.getByText(/search results/i)).toBeVisible();
  });

  test("should close dropdown on Escape", async ({ page }) => {
    const searchInput = page.getByRole("searchbox");

    await searchInput.fill("Phil");
    await expect(page.getByRole("listbox")).toBeVisible();

    await page.keyboard.press("Escape");

    await expect(page.getByRole("listbox")).not.toBeVisible();
  });

  test("should display source badge", async ({ page }) => {
    const searchInput = page.getByRole("searchbox");

    await searchInput.fill("Phil");

    await expect(page.getByRole("listbox")).toBeVisible();
    await expect(page.getByText(/Fast|AI-powered/i)).toBeVisible();
  });

  test("should work on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE

    const searchInput = page.getByRole("searchbox");

    await searchInput.fill("Phil");

    await expect(page.getByRole("listbox")).toBeVisible();

    // Dropdown should be full width on mobile
    const dropdown = page.getByRole("listbox");
    const dropdownBox = await dropdown.boundingBox();

    expect(dropdownBox?.width).toBeGreaterThan(300); // Full width
  });

  test("should handle rate limit error", async ({ page }) => {
    // Mock rate limit response
    await page.route("**/api/autocomplete*", route => {
      route.fulfill({
        status: 429,
        headers: { "Retry-After": "60" },
        body: JSON.stringify({ error: "Too many requests" })
      });
    });

    const searchInput = page.getByRole("searchbox");
    await searchInput.fill("Phil");

    await expect(page.getByText(/Too many requests/i)).toBeVisible();
    await expect(page.getByText(/wait.*60/i)).toBeVisible();
  });
});
```

### 9.4 Coverage Goals

```bash
# Run tests with coverage
npm run test:coverage

# Expected output:
# ----------------------|---------|----------|---------|---------|-------------------
# File                  | % Stmts | % Branch | % Funcs | % Lines | Uncovered Lines
# ----------------------|---------|----------|---------|---------|-------------------
# All files             |   85.2  |   82.1   |   88.3  |   85.7  |
#  components/search/   |   92.1  |   87.5   |   94.2  |   92.8  |
#   SearchBar.tsx       |   95.3  |   91.2   |   96.1  |   95.7  |
#   AutocompleteDropdown|   91.8  |   85.3   |   93.2  |   92.1  |
#   SuggestionItem.tsx  |   88.9  |   82.1   |   90.5  |   89.3  |
#  hooks/               |   82.3  |   78.6   |   85.1  |   82.9  |
#   useAutocomplete.ts  |   87.5  |   82.3   |   90.2  |   88.1  |
#   useDebounce.ts      |   100   |   100    |   100   |   100   |
#  lib/api/             |   79.1  |   74.2   |   81.3  |   79.8  |
#   autocomplete.ts     |   82.4  |   76.8   |   84.6  |   83.1  |
# ----------------------|---------|----------|---------|---------|-------------------

# Coverage Thresholds:
# - Statements: 80%
# - Branches: 75%
# - Functions: 80%
# - Lines: 80%
```

---

## 10. 구현 로드맵

### Phase 1: Foundation (Day 1-2)

**Goal**: 프로젝트 설정 + 기본 컴포넌트 구조

**Tasks**:
- [x] Next.js 15 프로젝트 생성
- [x] shadcn/ui 설치 및 설정
- [x] Tailwind CSS 구성
- [x] TypeScript 타입 정의 작성 (`types/` 디렉토리)
- [x] 프로젝트 구조 생성 (`components/`, `hooks/`, `lib/`)
- [x] 환경 변수 설정 (`.env.local`)
- [x] 기본 레이아웃 컴포넌트 (Header, Footer)

**Deliverables**:
- ✅ 실행 가능한 Next.js 프로젝트
- ✅ TypeScript strict mode 활성화
- ✅ shadcn/ui 컴포넌트 사용 가능

---

### Phase 2: Core Components (Day 3-4)

**Goal**: 핵심 Autocomplete 컴포넌트 구현

**Tasks**:
- [x] `SearchBar.tsx` 구현
  - Input 필드 + 아이콘
  - Clear 버튼
  - 로딩 스피너
- [x] `AutocompleteDropdown.tsx` 구현
  - 드롭다운 컨테이너
  - Framer Motion 애니메이션
  - 위치 계산 로직
- [x] `SuggestionItem.tsx` 구현
  - 텍스트 하이라이팅
  - Hover/선택 상태
  - 아이콘 표시
- [x] `SourceBadge.tsx` 구현
- [x] `KeyboardHints.tsx` 구현

**Deliverables**:
- ✅ 기본 UI 렌더링
- ✅ 컴포넌트 스타일링 완료

---

### Phase 3: Hooks & API Integration (Day 4-5)

**Goal**: 비즈니스 로직 + API 통합

**Tasks**:
- [x] `useDebounce.ts` 훅 구현
- [x] `useAutocomplete.ts` 훅 구현
  - API 호출
  - 캐싱
  - 에러 핸들링
- [x] `useKeyboardNavigation.ts` 훅 구현
  - ↑↓ 키 핸들링
  - Enter, Esc 핸들링
- [x] `useClickOutside.ts` 훅 구현
- [x] `lib/api/autocomplete.ts` API 클라이언트 구현
  - Fetch 래퍼
  - 타임아웃
  - 재시도 로직

**Deliverables**:
- ✅ 실제 API 호출 동작
- ✅ Debouncing 동작 (300ms)
- ✅ 키보드 네비게이션 동작

---

### Phase 4: Error Handling (Day 5)

**Goal**: 에러 상태 UI 구현

**Tasks**:
- [x] `ValidationError.tsx` 컴포넌트
- [x] `RateLimitError.tsx` 컴포넌트 (countdown timer)
- [x] `NetworkError.tsx` 컴포넌트 (retry button)
- [x] `NoResults.tsx` 컴포넌트
- [x] `LoadingState.tsx` 컴포넌트 (skeleton UI)

**Deliverables**:
- ✅ 모든 에러 케이스 UI 완성
- ✅ Retry 기능 동작

---

### Phase 5: Accessibility (Day 6)

**Goal**: WCAG 2.1 AA 준수

**Tasks**:
- [x] ARIA 속성 추가 (role, aria-label, aria-describedby 등)
- [x] 키보드 네비게이션 개선
- [x] Focus management 구현
- [x] Screen reader 지원 (live regions)
- [x] 색상 대비 검증 (contrast ratio ≥ 4.5:1)
- [x] Skip links 추가

**Deliverables**:
- ✅ WCAG 2.1 AA 체크리스트 통과
- ✅ Screen reader 테스트 (NVDA, JAWS)

---

### Phase 6: Performance Optimization (Day 6-7)

**Goal**: 번들 크기 최적화 + 렌더링 성능

**Tasks**:
- [x] React.memo 적용 (SuggestionItem)
- [x] useMemo, useCallback 최적화
- [x] Code splitting (dynamic import)
- [x] Image optimization (next/image)
- [x] Bundle size 분석
- [x] Lighthouse 테스트 (Performance ≥90)

**Deliverables**:
- ✅ Initial load < 200 KB (gzipped)
- ✅ Lighthouse Performance Score ≥ 90

---

### Phase 7: Testing (Day 7)

**Goal**: 테스트 커버리지 ≥ 80%

**Tasks**:
- [x] Unit tests (Jest)
  - `useDebounce.test.ts`
  - `useKeyboardNavigation.test.ts`
  - `highlightMatch.test.ts`
- [x] Component tests (React Testing Library)
  - `SearchBar.test.tsx`
  - `AutocompleteDropdown.test.tsx`
  - `SuggestionItem.test.tsx`
- [x] E2E tests (Playwright)
  - `autocomplete.spec.ts`
  - `keyboard-navigation.spec.ts`

**Deliverables**:
- ✅ 테스트 커버리지 ≥ 80%
- ✅ CI/CD 파이프라인 통합

---

### Phase 8: Polish & Deploy (Day 7)

**Goal**: 프로덕션 배포

**Tasks**:
- [x] Cross-browser testing (Chrome, Firefox, Safari)
- [x] Mobile responsiveness 검증
- [x] Dark mode 테스트
- [x] Documentation 작성
- [x] Vercel 배포
- [x] Performance monitoring 설정 (Vercel Analytics)

**Deliverables**:
- ✅ Production deployment
- ✅ Documentation 완성

---

## 마무리

이 문서는 포커 아카이브 Autocomplete 기능의 프론트엔드 컴포넌트 아키텍처를 정의합니다.

**핵심 원칙**:
1. **Component-First**: 재사용 가능한 독립적 컴포넌트
2. **Accessibility-First**: WCAG 2.1 AA 준수
3. **Performance-First**: 번들 크기 < 200 KB, LCP < 2.5s
4. **Type-Safe**: TypeScript strict mode, 모든 API 응답 타입 정의
5. **Test-Driven**: 80%+ coverage, E2E 테스트 포함

**참고 문서**:
- [UX 요구사항](./AUTOCOMPLETE-FRONTEND-UX-REQUIREMENTS.md)
- [Backend API 문서](../../FINAL_RECOMMENDATION_GCS.md)
- [Next.js 15 Docs](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)

**문의**: aiden.kim@ggproduction.net
**마지막 업데이트**: 2025-11-19
