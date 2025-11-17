# Mock API 설정 가이드

**목적**: Week 3-6 병렬 개발 지원
**작성일**: 2025-11-17
**버전**: 1.0.0

---

## 1. Mock API 전략

### 1.1 왜 Mock API가 필요한가?

**문제**: 모듈 간 의존성으로 인한 개발 블로킹

```
M6 (Frank) → M4 API 필요
    └─ M4 (David)가 Week 5까지 개발 중
    └─ M6는 Week 3부터 시작해야 함
```

**해결**: Mock API 서버로 독립 개발

---

## 2. Prism (OpenAPI Mock Server)

### 2.1 설치

```bash
npm install -g @stoplight/prism-cli
```

### 2.2 실행

```bash
# M4 Mock API
prism mock modules/rag-search/openapi.yaml --port 8004

# M5 Mock API
prism mock modules/clipping/openapi.yaml --port 8005

# M3 Mock API
prism mock modules/timecode-validation/openapi.yaml --port 8003
```

### 2.3 M6에서 사용

```tsx
// src/app/api/search/route.ts
const API_BASE = process.env.M4_SEARCH_API_URL || 'http://localhost:8004';

export async function POST(req: NextRequest) {
  const response = await fetch(`${API_BASE}/v1/search`, {
    method: 'POST',
    body: JSON.stringify(await req.json()),
  });
  return NextResponse.json(await response.json());
}
```

**장점**:
- ✅ OpenAPI 스펙 기반 자동 응답
- ✅ 예시 데이터 자동 생성
- ✅ 스펙 변경 시 즉시 반영

---

## 3. Docker Compose (통합 Mock 환경)

### 3.1 docker-compose.mock.yml

```yaml
version: '3.8'

services:
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

  mock-m3:
    image: stoplight/prism:latest
    command: mock -h 0.0.0.0 /openapi.yaml
    volumes:
      - ./modules/timecode-validation/openapi.yaml:/openapi.yaml
    ports:
      - "8003:4010"
```

### 3.2 실행

```bash
docker-compose -f docker-compose.mock.yml up
```

---

## 4. Pub/Sub Emulator (M5용)

### 4.1 설치

```bash
gcloud components install pubsub-emulator
```

### 4.2 실행

```bash
gcloud beta emulators pubsub start --project=gg-poker
```

### 4.3 환경 변수

```bash
export PUBSUB_EMULATOR_HOST=localhost:8085
```

### 4.4 M6에서 사용

```tsx
// M6 → Pub/Sub Emulator
import { PubSub } from '@google-cloud/pubsub';

const pubsub = new PubSub({
  projectId: 'gg-poker',
  apiEndpoint: process.env.PUBSUB_EMULATOR_HOST || undefined,
});

await pubsub.topic('clipping-requests').publish(Buffer.from(JSON.stringify({
  hand_id: 'wsop2024_me_d3_h154',
  nas_video_path: '/nas/poker/...',
  start_seconds: 12255,
  end_seconds: 12405,
})));
```

---

## 5. Mock 데이터 커스터마이징

### 5.1 Prism Dynamic Responses

```yaml
# modules/rag-search/openapi.yaml
responses:
  '200':
    content:
      application/json:
        examples:
          tom_dwan:
            summary: Tom Dwan 검색 결과
            value:
              results:
                - hand_id: "wsop2008_me_d3_h154"
                  summary: "Tom Dwan, J4o, river bluff"
                  relevance_score: 0.94
```

**Prism는 examples를 순차적으로 반환**

---

## 6. Mock → Real API 전환

### 6.1 환경 변수 전환

```bash
# .env.local (개발)
M4_SEARCH_API_URL=http://localhost:8004  # Mock

# .env.production
M4_SEARCH_API_URL=https://rag-search-service-prod.run.app  # Real
```

### 6.2 자동 전환 로직

```tsx
// lib/api-client.ts
const IS_MOCK = process.env.NODE_ENV === 'development' && !process.env.USE_REAL_API;

export const API_ENDPOINTS = {
  M4_SEARCH: IS_MOCK ? 'http://localhost:8004' : process.env.M4_SEARCH_API_URL,
  M5_CLIPPING: IS_MOCK ? 'http://localhost:8005' : process.env.M5_CLIPPING_API_URL,
};
```

---

## 7. Mock API 타임라인

| Week | Mock API | Real API |
|------|----------|----------|
| 1-2  | 구축 | - |
| 3-4  | M6 개발 (Mock M4, M5) | M1, M2 개발 |
| 5-6  | M6 개발 계속 | M4, M5 개발 |
| 7    | M6 → Real API 전환 | 통합 테스트 |
| 8+   | Mock 제거 | Production |

---

**작성자**: microservices-pm (AI Agent)
**최종 업데이트**: 2025-11-17
