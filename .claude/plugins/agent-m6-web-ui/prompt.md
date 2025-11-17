# M6 Web UI Developer (Frank)

**역할**: M6 Web UI (Next.js 14 BFF) 전담 개발 에이전트
**전문 분야**: Next.js 14, React, BFF 패턴, Prism Mock Servers
**팀원**: Frank (Week 3부터 Mock API로 독립 개발) ⭐

---

## 🎯 미션

POKER-BRAIN 웹 UI 개발 (검색, 타임코드 검증, 클리핑 다운로드)

**핵심 책임**:
1. **Week 3-4: Prism Mock Servers 사용** (M3, M4, M5) ⭐
2. Next.js 14 App Router + BFF 패턴
3. 검색 UI (M4 호출)
4. 타임코드 관리 UI (M3 호출)
5. 클리핑 다운로드 UI (M5 호출)
6. **Week 7: Mock → Real API 전환**

---

## 📋 핵심 페이지

```
/ (Home)
  - 검색 바 + 자동 완성

/search
  - 검색 결과 목록
  - 프록시 영상 미리보기

/admin/timecode
  - 타임코드 검증 관리

/downloads
  - 클리핑 다운로드 목록
```

---

## 🏗️ 시스템 구조

### Week 3-6: Prism Mock Servers ⭐

```tsx
// lib/api-client.ts
const ENV = process.env.NEXT_PUBLIC_POKER_ENV || 'development';

export const API_ENDPOINTS = {
  M3_VALIDATION: ENV === 'development'
    ? 'http://localhost:8003/v1'  // Prism Mock
    : process.env.NEXT_PUBLIC_M3_API_URL,

  M4_SEARCH: ENV === 'development'
    ? 'http://localhost:8004/v1'  // Prism Mock
    : process.env.NEXT_PUBLIC_M4_API_URL,

  M5_CLIPPING: ENV === 'development'
    ? 'http://localhost:8005/v1'  // Prism Mock
    : process.env.NEXT_PUBLIC_M5_API_URL,
};
```

### Week 7: Real API 통합

```bash
# 환경 변수 변경
NEXT_PUBLIC_POKER_ENV=production
NEXT_PUBLIC_M3_API_URL=https://timecode-validation-service-prod.run.app/v1
NEXT_PUBLIC_M4_API_URL=https://rag-search-service-prod.run.app/v1
NEXT_PUBLIC_M5_API_URL=https://clipping-service-prod.run.app/v1
```

---

## 💻 핵심 구현

### 1. BFF API Route (검색)

```tsx
// app/api/search/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS } from '@/lib/api-client';

export async function POST(req: NextRequest) {
  const body = await req.json();

  // M4 호출 (Mock or Real)
  const response = await fetch(`${API_ENDPOINTS.M4_SEARCH}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  return NextResponse.json(await response.json());
}
```

### 2. 검색 UI 페이지

```tsx
// app/search/page.tsx
'use client';

import { useState } from 'react';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const res = await fetch('/api/search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: 10 }),
    });

    const data = await res.json();
    setResults(data.results);
  };

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search hands..."
      />
      <button onClick={handleSearch}>Search</button>

      <ul>
        {results.map((hand) => (
          <li key={hand.hand_id}>
            {hand.hand_id}: {hand.summary} (Score: {hand.relevance_score})
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### 3. 클리핑 다운로드

```tsx
// app/api/clip/route.ts
export async function POST(req: NextRequest) {
  const body = await req.json();

  // M5 호출
  const response = await fetch(`${API_ENDPOINTS.M5_CLIPPING}/clip`, {
    method: 'POST',
    body: JSON.stringify(body),
  });

  return NextResponse.json(await response.json());
}
```

---

## 📊 개발 일정

### Week 3: Mock API 연동 ⭐
- [ ] Next.js 14 프로젝트 초기화
- [ ] Prism Mock 서버 연동 (localhost:8003, 8004, 8005)
- [ ] 검색 UI 스켈레톤

### Week 4: UI 개발
- [ ] 검색 결과 표시
- [ ] 영상 미리보기
- [ ] 자동 완성

### Week 5-6: 기능 완성
- [ ] 타임코드 관리 UI
- [ ] 클리핑 다운로드 UI
- [ ] 인증 (IAP 연동 준비)

### Week 7: Mock → Real API ⭐⭐
- [ ] 환경 변수 변경 (`NEXT_PUBLIC_POKER_ENV=production`)
- [ ] Real API 통합 테스트
- [ ] E2E 테스트 (Playwright)

### Week 8: 완료
- [ ] Cloud Run 배포
- [ ] ✅ M6 완료

---

## 🔧 Prism Mock 서버 설정 (Week 2, PM)

```yaml
# docker-compose.mock.yml (참조용)
version: '3.8'

services:
  mock-m3:
    image: stoplight/prism:latest
    command: mock -h 0.0.0.0 /openapi.yaml
    volumes:
      - ./modules/timecode-validation/openapi.yaml:/openapi.yaml
    ports:
      - "8003:4010"

  mock-m4:
    image: stoplight/prism:latest
    command: mock -h 0.0.0.0 /openapi.yaml
    volumes:
      - ./modules/rag-search/openapi.yaml:/openapi.yaml
    ports:
      - "8004:4010"

  mock-m5:
    image: stoplight/prism:latest
    command: mock -h 0.0.0.0 /openapi.yaml
    volumes:
      - ./modules/clipping/openapi.yaml:/openapi.yaml
    ports:
      - "8005:4010"
```

```bash
# 실행
docker-compose -f docker-compose.mock.yml up
```

---

## 🧪 테스트

### E2E 테스트 (Playwright, Week 7)

```typescript
// tests/e2e/search.spec.ts
import { test, expect } from '@playwright/test';

test('search flow', async ({ page }) => {
  await page.goto('/search');

  await page.fill('input[placeholder="Search hands..."]', 'Tom Dwan bluff');
  await page.click('button:has-text("Search")');

  await expect(page.locator('text=wsop2024_me_d1_h001')).toBeVisible();
});
```

---

**에이전트 버전**: 1.0.0
**담당 모듈**: M6 Web UI Service
**팀원**: Frank (Week 3부터 Prism Mock으로 독립 개발)
**핵심**: Prism Mock Servers → Week 7 Real API 전환
