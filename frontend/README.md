# 포커 아카이브 검색 - 프론트엔드

Next.js 16 + React 19 기반 프론트엔드 애플리케이션

---

## 빠른 시작

### 개발 서버 실행

```bash
npm run dev
# 또는
yarn dev
# 또는
pnpm dev
```

브라우저에서 [http://localhost:9001](http://localhost:9001) 접속 (포트는 설정에 따라 다름)

페이지 수정은 `src/app/page.tsx` 파일을 편집하면 자동으로 반영됩니다.

---

## 프로젝트 구조

```
frontend/
├── src/
│   ├── app/                # App Router (Next.js 14+)
│   │   ├── page.tsx        # 메인 페이지
│   │   └── layout.tsx      # 레이아웃
│   ├── components/         # React 컴포넌트
│   │   ├── archive/        # 아카이브 관련 컴포넌트
│   │   ├── filters/        # 필터 컴포넌트
│   │   ├── hand-detail/    # 핸드 상세 컴포넌트
│   │   ├── hands/          # 핸드 목록 컴포넌트
│   │   ├── search/         # 검색 컴포넌트
│   │   ├── ui/            # 기본 UI 컴포넌트 (shadcn/ui)
│   │   └── video/         # 비디오 플레이어 컴포넌트
│   ├── lib/               # 유틸리티 및 API 클라이언트
│   │   ├── api/           # API 호출 함수
│   │   ├── hooks/         # Custom React Hooks
│   │   └── utils.ts       # 유틸리티 함수
│   └── types/             # TypeScript 타입 정의
├── public/                # 정적 파일
├── e2e/                   # Playwright E2E 테스트
└── tests/                 # 유닛 테스트
```

---

## 개발 가이드

### 환경 변수 설정

`.env.local` 파일 생성:

```bash
NEXT_PUBLIC_API_URL=http://localhost:9000
NEXT_PUBLIC_ENV=development
```

### 테스트 실행

```bash
# 유닛 테스트 (Vitest)
npm test

# E2E 테스트 (Playwright)
npm run e2e

# 커버리지
npm run test:coverage
```

### 타입 체크

```bash
npm run type-check
```

### 린트

```bash
npm run lint
```

### 빌드

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 확인
npm start
```

---

## 주요 기술 스택

- **프레임워크**: Next.js 16 (App Router)
- **UI 라이브러리**: React 19
- **언어**: TypeScript 5
- **스타일링**: Tailwind CSS 4
- **UI 컴포넌트**: shadcn/ui
- **상태 관리**: React Hooks (useState, useEffect 등)
- **테스트**: Vitest (유닛), Playwright (E2E)

---

## Next.js 배우기

Next.js에 대해 더 알아보려면:

- [Next.js 문서](https://nextjs.org/docs) - Next.js 기능 및 API 학습
- [Next.js 튜토리얼](https://nextjs.org/learn) - 인터랙티브 튜토리얼

---

## Vercel 배포

Next.js 앱을 배포하는 가장 쉬운 방법은 [Vercel 플랫폼](https://vercel.com/new)을 사용하는 것입니다.

자세한 내용은 [Next.js 배포 문서](https://nextjs.org/docs/app/building-your-application/deploying)를 참조하세요.

### 빠른 배포

```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
vercel

# 프로덕션 배포
vercel --prod
```

---

## 트러블슈팅

### 포트 충돌

기본 포트(9001)가 사용 중인 경우:

```bash
npm run dev -- -p 9002
```

### 모듈 해결 오류

`@/` 경로가 작동하지 않는 경우:

```bash
# node_modules 삭제 후 재설치
rm -rf node_modules
npm install
```

### Hydration 오류

Server Component에서 브라우저 API를 사용하는 경우 `'use client'` 지시어를 파일 상단에 추가하세요.

---

## 프로젝트 문서

- **사용자 가이드**: [docs/README.md](../docs/README.md)
- **빠른 시작**: [docs/QUICKSTART.md](../docs/QUICKSTART.md)
- **문제 해결**: [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)
- **개발자 가이드**: [CLAUDE.md](../CLAUDE.md)

---

**버전**: v5.0.0
**최종 업데이트**: 2025-11-20
