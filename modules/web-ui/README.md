# M6: Web UI Service (BFF)

**담당**: Frontend Engineer (Frank)
**버전**: 1.0.0
**배포**: Cloud Run 또는 Vercel
**Tech Stack**: Next.js 14 (App Router) + shadcn/ui

---

## 개요

사용자 인터페이스 및 Backend for Frontend (BFF) API입니다.

### 주요 기능

- ✅ 포커 핸드 검색 UI
- ✅ 프록시 영상 미리보기
- ✅ 클립 다운로드 요청
- ✅ 즐겨찾기 관리
- ✅ 관리자 대시보드 (Phase 0 진행률)

---

## 페이지 구조

```
/                    → 검색 페이지
/search?q=...        → 검색 결과
/hand/[hand_id]      → 핸드 상세 + 미리보기
/downloads           → 내 다운로드 목록
/favorites           → 즐겨찾기
/admin               → 관리자 대시보드
```

---

## BFF 패턴

```
Browser (React) → Next.js API Routes (BFF)
    ↓
BFF → M4 (RAG Search)
BFF → M5 (Clipping)
BFF → M3 (Admin)
    ↓
Browser ← JSON Response
```

**BFF 역할**:
- Service Account 인증 관리
- 에러 핸들링
- 사용자 컨텍스트 추가
- 응답 변환

---

## API 스펙

**OpenAPI 3.0**: `openapi.yaml`

### 주요 엔드포인트

```bash
# 검색 (BFF → M4)
POST /api/search

# 다운로드 (BFF → M5)
POST /api/download

# 상태 조회
GET /api/download/{clip_request_id}/status

# 즐겨찾기
GET/POST/DELETE /api/favorites

# 관리자 대시보드
GET /api/admin/validation/stats
```

---

## 로컬 개발

### Next.js 프로젝트 초기화

```bash
npx create-next-app@latest web-ui \
  --typescript \
  --tailwind \
  --app \
  --src-dir

cd web-ui
npm install
```

### 필수 패키지 설치

```bash
npm install \
  @tanstack/react-query \
  @radix-ui/react-dialog \
  @radix-ui/react-dropdown-menu \
  shadcn-ui \
  react-player \
  axios
```

### shadcn/ui 초기화

```bash
npx shadcn-ui@latest init

npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
```

---

## 핵심 컴포넌트

### 검색 폼

```tsx
// src/app/page.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function HomePage() {
  const [query, setQuery] = useState('');

  const handleSearch = async () => {
    const res = await fetch('/api/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    // 결과 표시
  };

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-4xl font-bold mb-6">POKER-BRAIN</h1>
      <div className="flex gap-2">
        <Input
          placeholder="Tom Dwan 블러프..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button onClick={handleSearch}>검색</Button>
      </div>
    </div>
  );
}
```

### BFF API Route (검색)

```tsx
// src/app/api/search/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { query, filters } = await req.json();

  // M4 RAG Search Service 호출
  const response = await fetch('https://rag-search-service-prod.run.app/v1/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${await getServiceToken()}`,
    },
    body: JSON.stringify({ query, filters, limit: 20 }),
  });

  const results = await response.json();

  // 사용자 컨텍스트 추가 (즐겨찾기 여부)
  const userEmail = req.headers.get('x-goog-authenticated-user-email');
  const favorites = await getFavorites(userEmail);

  results.results.forEach((hand: any) => {
    hand.is_favorite = favorites.includes(hand.hand_id);
  });

  return NextResponse.json(results);
}

async function getServiceToken() {
  // Service Account 토큰 생성
  const { GoogleAuth } = require('google-auth-library');
  const auth = new GoogleAuth();
  const client = await auth.getClient();
  const token = await client.getAccessToken();
  return token.token;
}
```

### 비디오 미리보기

```tsx
// src/components/VideoPreview.tsx
'use client';

import ReactPlayer from 'react-player';

export function VideoPreview({ proxyUrl }: { proxyUrl: string }) {
  return (
    <div className="w-full aspect-video rounded-lg overflow-hidden">
      <ReactPlayer
        url={proxyUrl}
        controls
        width="100%"
        height="100%"
      />
    </div>
  );
}
```

### 다운로드 버튼 (Polling)

```tsx
// src/components/DownloadButton.tsx
'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

export function DownloadButton({ handId }: { handId: string }) {
  const [status, setStatus] = useState<'idle' | 'queued' | 'processing' | 'completed'>('idle');
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [clipRequestId, setClipRequestId] = useState<string | null>(null);

  const requestDownload = async () => {
    const res = await fetch('/api/download', {
      method: 'POST',
      body: JSON.stringify({ hand_id: handId }),
    });
    const data = await res.json();
    setClipRequestId(data.clip_request_id);
    setStatus('queued');
  };

  useEffect(() => {
    if (!clipRequestId || status === 'completed') return;

    const interval = setInterval(async () => {
      const res = await fetch(`/api/download/${clipRequestId}/status`);
      const data = await res.json();

      setStatus(data.status);

      if (data.status === 'completed') {
        setDownloadUrl(data.download_url);
        clearInterval(interval);
      }
    }, 5000); // 5초 간격 폴링

    return () => clearInterval(interval);
  }, [clipRequestId, status]);

  if (status === 'completed' && downloadUrl) {
    return <Button asChild><a href={downloadUrl} download>다운로드</a></Button>;
  }

  if (status === 'queued' || status === 'processing') {
    return <Button disabled>{status === 'queued' ? '대기 중...' : '생성 중...'}</Button>;
  }

  return <Button onClick={requestDownload}>클립 다운로드</Button>;
}
```

---

## 배포

### Vercel (권장)

```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
vercel --prod
```

### Cloud Run

```bash
# Dockerfile 생성
cat > Dockerfile << 'EOF'
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "start"]
EOF

# 배포
gcloud run deploy web-ui \
  --source . \
  --region us-central1 \
  --memory 2Gi
```

---

## 환경 변수

```env
# .env.local
M4_SEARCH_API_URL=https://rag-search-service-prod.run.app
M5_CLIPPING_API_URL=https://clipping-service-prod.run.app
M3_VALIDATION_API_URL=https://timecode-validation-service-prod.run.app

GOOGLE_CLOUD_PROJECT=gg-poker
```

---

**담당자**: aiden.kim@ggproduction.net
**최종 업데이트**: 2025-11-17
