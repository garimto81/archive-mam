# CLAUDE.md - 개발자 가이드

이 파일은 Claude Code(claude.ai/code)가 이 저장소에서 작업할 때 참조하는 가이드입니다.

**저장소**: archive-mam (ATI 메타데이터 기반 포커 핸드 검색 시스템)
**버전**: v5.0.0
**구현 상태**: Phase 2 완료 (Backend + Frontend), Phase 3 진행 중 (Video Archive UI)
**주 언어**: 한글 (기술 용어는 영문 유지)
**아키텍처**: Vertex AI Vector Search + BigQuery + Qwen3-8B + Next.js 16 + React 19

## ⚠️ 문서 관리 원칙

**문서 추가 생성 금지**:
- ✅ **기존 문서 업데이트**: README.md, CLAUDE.md, docs/ 폴더 내 문서 수정
- ❌ **새 문서 생성 금지**: 별도의 분석 문서, 생태계 문서, 요약 문서 생성 금지
- 📁 **정보 통합**: 모든 정보는 기존 문서에 섹션으로 추가
- 🎯 **목적**: 문서 파편화 방지, 유지보수 용이성 향상

**예외 사항**:
- PRD 문서 (`tasks/prds/`)
- 코드 파일 (`.py`, `.ts`, `.tsx` 등)
- 설정 파일 (`.json`, `.yaml`, `.env.example` 등)

---

## 🌐 GGProduction 영상 처리 생태계

**이 프로젝트는 3개 연결된 프로젝트 중 2번째입니다 (인과관계 순서):**

```
[0. qwen_hand_analysis]  Gemini AI 핸드 분석 (데이터 생성)
   - Gemini 2.5 Flash로 영상 분석
   - 핸드 메타데이터 자동 생성
   - Firestore/BigQuery 저장
        ↓
[1. archive-mam] ⭐      검색 & 아카이빙 (현재 프로젝트)
   - AI 자연어 검색 (Vertex AI)
   - 포커 핸드 학습 시스템
   - Next.js 16 프론트엔드
        ↓
[2. man_subclip]         영상 편집 플랫폼 (데이터 활용)
   - HLS Proxy 렌더링
   - 타임코드 미리보기
   - 원본 품질 서브클립 추출
```

**프로젝트 위치**:
- `../qwen_hand_analysis/` - Gemini 기반 영상 분석
- `./` (현재) - Phase 2 완료, Phase 3 진행 중
- `../man_subclip/` - 개발 중 (70%)

**인과관계 (Causal Chain)**:
0. **qwen_hand_analysis**: 원본 영상 → Gemini 분석 → 핸드 메타데이터 생성 (Firestore/BigQuery)
1. **archive-mam**: 메타데이터 소비 → Vertex AI 임베딩 → 검색 인덱스 → 사용자에게 핸드 검색 제공
2. **man_subclip**: 검색된 핸드 → HLS Proxy 렌더링 → 타임코드 기반 서브클립 추출

### 프로젝트별 상세 정보

#### 0️⃣ qwen_hand_analysis (데이터 생성)
**위치**: `../qwen_hand_analysis/`
**목적**: Gemini AI로 포커 영상에서 핸드 히스토리 자동 추출
**기술**: FastAPI + Gemini 2.5 Flash + Firestore + BigQuery
**상태**: v0.6.0 (Phase 6 완료)
**출력**: 구조화된 핸드 메타데이터 (hand_id, description, hero/villain, pot_bb, tags, timestamp 등)

#### 1️⃣ archive-mam (현재 프로젝트 ⭐)
**위치**: `./` (현재 디렉토리)
**목적**: AI 자연어 검색 시스템
**기술**: FastAPI + Next.js 16 + Vertex AI + BigQuery + Qwen3-8B
**상태**: v5.0.0 (Phase 2 완료, Phase 3 진행 중)
**입력**: qwen_hand_analysis의 메타데이터 (필수 의존성)
**출력**: 검색 UI + RAG 답변

#### 2️⃣ man_subclip (검색 결과 활용)
**위치**: `../man_subclip/`
**목적**: HLS 스트리밍 기반 영상 편집 및 서브클립 추출
**기술**: FastAPI + React 18 + ffmpeg + Video.js
**상태**: v4.0.0 (백엔드 100%, 프론트엔드 40%)
**입력**: archive-mam 검색 결과 (선택적 연계) 또는 수동 타임코드 입력
**출력**: HLS Proxy + 서브클립 영상

### 상세 의존성

**0 → 1 (필수 의존성 ⭐)**:
- archive-mam은 qwen_hand_analysis가 생성한 메타데이터 없이는 검색 불가
- qwen_hand_analysis의 분석 품질이 archive-mam의 검색 정확도에 직접 영향
- 핵심 데이터: hand_id, description, hero_name, villain_name, pot_bb, tags, video_url, timestamp

**1 → 2 (선택적 연계)**:
- man_subclip은 archive-mam의 검색 결과를 활용하여 편집 대상 선정 가능
- 검색으로 찾은 핸드를 바로 편집/공유 가능 (UX 향상)
- man_subclip 단독 사용도 가능 (수동 타임코드 입력)

**0 ↔ 2 (간접 연결)**:
- 직접적 데이터 교환 없음
- 둘 다 동일한 원본 영상 파일 처리
- 결과물을 archive-mam이 통합하여 사용

### 통합 시나리오 예시

**사용자 워크플로우: "Phil Ivey 블러프 검색"**

```
1. [사용자] archive-mam 접속 (http://localhost:9001)
2. [사용자] 검색: "Phil Ivey가 Tom Dwan을 상대로 블러프한 핸드"
3. [archive-mam]
   - Vertex AI 임베딩 생성
   - Vector Search로 유사 핸드 검색
   - BigQuery에서 메타데이터 조회 (qwen_hand_analysis가 생성한 데이터)
4. [archive-mam] 검색 결과 반환
   - 핸드 5개 (유사도 순)
   - 각 핸드: 메타데이터 + 서브클립 URL + 썸네일
5. [사용자] 결과 클릭 → 서브클립 재생 (man_subclip HLS Proxy)
6. [사용자] RAG 요청: "이 핸드에서 Phil Ivey의 전략은?"
   - Qwen3-8B로 답변 생성
```

---

## 프로젝트 상태 (중요)

**✅ 완료**:
- Phase 1: GCS → Cloud Functions → BigQuery 파이프라인
- Phase 1.5: Vertex AI 임베딩 생성 및 GCS 저장
- Phase 2: RAG 기능이 있는 FastAPI 백엔드 (v1.3.0)
- Phase 2: TypeScript 기반 Next.js 16 프론트엔드
- Vertex AI Vector Search 인덱스 배포
- Qwen3-8B LLM 통합 (Ollama)

**🚧 진행 중**:
- Phase 3: Video Archive Management UI
- Vercel + Cloud Run 프로덕션 배포

**📁 현재 코드 구조**:
- `frontend/` - **활성** Next.js 16 + React 19 + TypeScript (Vercel 배포)
- `backend/app/` - **활성** RAG 기능이 있는 FastAPI v1.3.0 (Cloud Run 배포)
- `cloud_functions/index_metadata/` - **활성** ETL 파이프라인
- `app/` 및 `app.legacy/` - **사용 중단** PostgreSQL 기반 코드 (사용 금지)

---

## 핵심 아키텍처 (현재 구현)

### 풀스택 아키텍처

```
[사용자 브라우저] ←→ [Next.js 16 프론트엔드 (Vercel)]
                      ↓ API 호출
                 [FastAPI 백엔드 (Cloud Run)]
                   ↙          ↘
    [Vertex AI Search]    [BigQuery]
           ↓                  ↓
    [Vector Index]      [핸드 메타데이터]
                          ↙
                   [GCS 영상]
```

### 데이터 흐름 (ETL 파이프라인)

```
[ATI 분석] → [GCS JSON 업로드]
    ↓ Pub/Sub 트리거 (<1초)
[Cloud Functions Gen2]
  1. JSON 파싱 및 스키마 검증
  2. BigQuery 삽입
  3. Vertex AI 임베딩 생성 (768차원)
  4. 임베딩을 GCS embeddings/에 저장
    ↓
[BigQuery: poker_archive.hands] + [GCS: embeddings/*.json]
    ↓
[Vertex AI Vector Search Index]
  - 하이브리드 검색 (BM25 + Vector + RRF)
  - TextEmbedding-004 모델
```

### API 아키텍처

**프론트엔드** (`frontend/src/lib/api/`):
- `client.ts` - 타임아웃/재시도 기능이 있는 기본 fetch 래퍼
- `search.ts` - 검색 API 클라이언트
- `hands.ts` - 핸드 상세 정보 API 클라이언트
- `autocomplete.ts` - 자동완성 제안
- `video.ts` - 비디오 URL 생성 (GCS signed URLs)

**백엔드** (`backend/app/api/`):
- `search.py` - Vertex AI 벡터 검색
- `hands.py` - BigQuery 핸드 상세 정보
- `rag.py` - Qwen3-8B RAG
- `autocomplete.py` - 검색 제안 (v5.0 신규)

---

## 개발 명령어

### 로컬 개발 환경 설정

**1. 백엔드 (FastAPI)**:
```bash
# 백엔드 디렉토리로 이동
cd backend

# Python 가상 환경
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 의존성 설치
pip install -r ../requirements-poc.txt

# 환경 변수 파일 복사
copy ..\.env.poc .env

# 서버 실행
uvicorn app.main:app --reload --port 9000

# 헬스 체크
curl http://localhost:9000/health
```

**2. Ollama 설정 (RAG 기능 필수)**:
```bash
# Ollama 설치
# 다운로드: https://ollama.ai

# Qwen3-8B 모델 다운로드
ollama pull qwen3:8b

# 확인
ollama list
```

**3. 프론트엔드 (Next.js 16 + React 19)**:
```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치
npm install

# 환경 변수 파일 복사
copy .env.example .env.local  # Windows
cp .env.example .env.local    # Mac/Linux

# .env.local 편집하여 백엔드 URL 설정
# NEXT_PUBLIC_API_URL=http://localhost:9000

# 개발 서버 시작
npm run dev
# 브라우저: http://localhost:9001

# 테스트 실행 (유닛 + 통합)
npm test

# 커버리지 포함 테스트
npm run test:coverage

# E2E 테스트 (Playwright)
npm run e2e

# E2E 테스트 UI 모드 (인터랙티브)
npm run e2e:ui

# 타입 체크
npm run type-check

# 프로덕션 빌드
npm run build

# 프로덕션 서버 로컬 실행
npm run start
```

**4. GCP 설정**:
```bash
# 프로젝트 설정
export GCP_PROJECT=gg-poker-dev
gcloud config set project $GCP_PROJECT

# 인증
gcloud auth application-default login

# API 활성화 (아직 안 했다면)
gcloud services enable \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  cloudfunctions.googleapis.com \
  storage.googleapis.com
```

### 테스트

**API 테스트**:
```bash
# 검색 API
curl "http://localhost:9000/api/search?query=Phil%20Ivey%20bluff&top_k=5"

# 핸드 상세 정보
curl "http://localhost:9000/api/hands/wsop_2023_hand_0001"

# RAG API
curl -X POST "http://localhost:9000/api/rag" \
  -H "Content-Type: application/json" \
  -d '{"query": "Phil Ivey의 블러프 전략은?", "top_k": 5, "use_thinking_mode": true}'
```

**통합 테스트**:
```bash
# 전체 파이프라인 테스트 (루트에서)
bash test_integration.sh

# BigQuery 데이터 확인
python check_bigquery.py

# BigQuery 쿼리
python query_bigquery.py
```

### Cloud Functions 배포

```bash
cd cloud_functions/index_metadata

# 배포 (자동 권한 설정)
bash deploy.sh

# 또는 처음부터 전체 설정
cd ../..
bash complete_setup.sh

# 배포 테스트
bash test_deployment.sh
```

### Vertex AI 인덱스 관리

```bash
# 인덱스 생성 (처음만)
python scripts/vertex-ai/create_index.py

# 인덱스 엔드포인트 배포
python scripts/vertex-ai/deploy_index.py

# 임베딩 업로드
python scripts/vertex-ai/upload_embeddings.py
```

---

## 주요 파일 및 용도

### 활성 프론트엔드 (v5.0.0)

**핵심 애플리케이션**:
- `frontend/src/app/page.tsx` - 홈페이지 (루트 경로 `/`)
- `frontend/src/app/search/page.tsx` - 검색 페이지 경로 (`/search`)
- `frontend/src/components/ErrorBoundary.tsx` - 전역 에러 바운더리

**API 레이어** (`frontend/src/lib/api/`):
- `client.ts` - 타임아웃/재시도/에러 처리가 있는 기본 fetch 래퍼
- `search.ts` - 검색 API 클라이언트
- `hands.ts` - 핸드 상세 정보 API 클라이언트
- `autocomplete.ts` - 자동완성 제안
- `video.ts` - 비디오 URL 생성

**컴포넌트** (`frontend/src/components/`):
- `search/` - 검색 UI 컴포넌트 (SearchBar, SearchResults, Pagination 등)
- `hands/` - 핸드 카드 컴포넌트 (HandCard, HandThumbnail, HandMetadata 등)
- `filters/` - 필터 패널 컴포넌트 (FilterPanel, ActiveFilters, CardSelector)
- `video/` - 비디오 플레이어 컴포넌트 (VideoPlayer, HandTimeline, VideoControls)
- `ui/` - shadcn/ui 컴포넌트 (Button, Input, Badge, Dialog 등)

**상태 관리** (`frontend/src/hooks/`):
- `useSearchResults.ts` - 검색 결과 상태
- `useFilters.ts` - 필터 상태 관리
- `useInfiniteScroll.ts` - 무한 스크롤 페이지네이션
- `useDebounce.ts` - 검색 입력 디바운스
- `useVideoUrl.ts` - 만료 기능이 있는 비디오 URL 관리

**타입** (`frontend/src/types/`):
- `api.ts` - API 요청/응답 타입
- `hand.ts` - 핸드 메타데이터 타입
- `video.ts` - 비디오 플레이어 타입
- `errors.ts` - 커스텀 에러 클래스
- `autocomplete.ts` - 자동완성 타입

**테스트**:
- `vitest.config.ts` - Vitest 설정 (유닛 테스트)
- `playwright.config.ts` - Playwright 설정 (E2E 테스트)
- `frontend/e2e/` - E2E 테스트 파일

**설정**:
- `frontend/package.json` - 의존성 및 스크립트
- `frontend/tsconfig.json` - TypeScript 설정
- `frontend/vercel.json` - Vercel 배포 설정
- `frontend/.env.example` - 환경 변수 템플릿

### 활성 백엔드 (v1.3.0)

- `backend/app/main.py` - CORS 및 헬스 체크가 있는 FastAPI 진입점
- `backend/app/config.py` - 환경 변수 설정 (.env.poc에서 읽음)
- `backend/app/models.py` - API 요청/응답용 Pydantic 모델
- `backend/app/api/search.py` - 벡터 검색 API (Vertex AI)
- `backend/app/api/hands.py` - 핸드 상세 정보 API (BigQuery)
- `backend/app/api/rag.py` - Qwen3-8B RAG API
- `backend/app/api/autocomplete.py` - 자동완성 API (v5.0 신규)
- `backend/app/services/vertex_search.py` - Vertex AI Vector Search 클라이언트
- `backend/app/services/bigquery.py` - BigQuery 클라이언트
- `backend/app/services/llm_service.py` - LLM 서비스 (Ollama/HuggingFace)

### ETL 파이프라인 (Cloud Functions)

- `cloud_functions/index_metadata/main.py` - GCS 트리거 함수 (323줄)
  - ATI 메타데이터 스키마 검증
  - BigQuery에 삽입
  - Vertex AI로 임베딩 생성
  - 임베딩을 GCS에 저장
- `cloud_functions/index_metadata/requirements.txt` - 의존성
- `cloud_functions/index_metadata/deploy.sh` - 배포 스크립트

### 스키마 및 데이터

- `tasks/schemas/ati_metadata_schema.json` - ATI 메타데이터 JSON 스키마
- `tasks/schemas/bigquery_schema.json` - BigQuery 테이블 스키마 (27개 필드)
- `mock_data/synthetic_ati/*.json` - 100개 합성 테스트 샘플
- `.env.poc` - 환경 변수 (backend/.env로 복사)

### 배포 스크립트

- `complete_setup.sh` - 전체 GCP 인프라 설정
- `create_bigquery_table.sh` - BigQuery 테이블 생성
- `fix_permissions.sh` - Eventarc/Pub/Sub 권한 수정
- `deploy-cloud-run.sh` - FastAPI를 Cloud Run에 배포

### 문서

**사용자 문서 (docs/)**:
- `docs/README.md` - 프로젝트 개요 및 시작 가이드
- `docs/QUICKSTART.md` - 5분 빠른 시작 가이드
- `docs/TROUBLESHOOTING.md` - 일반적인 문제 및 해결 방법

**참조 문서 (tasks/)**:
- `tasks/prds/` - PRD 문서
- `tasks/schemas/` - 데이터 스키마
- `tasks/references/` - 참조 자료

### 사용 중단 코드 (수정 금지)

- `app/` - v3.0.0 PostgreSQL 기반 코드 (참조용으로만 보관)
- `app.legacy/` - 사용 중단된 코드 백업

---

## 환경 변수

### 백엔드 (`.env.poc`)

**중요 변수**:
```bash
# GCP
GCP_PROJECT=gg-poker-dev
GCP_REGION=us-central1

# BigQuery
BQ_DATASET=poker_archive_dev
BQ_TABLE_HAND_SUMMARY=hand_summary

# Vertex AI
VERTEX_AI_INDEX_ENDPOINT=projects/45067711104/locations/us-central1/indexEndpoints/3557757943715725312
VERTEX_AI_DEPLOYED_INDEX_ID=poker_hands_deployed
SEARCH_TYPE=hybrid  # hybrid | vector

# LLM (Ollama를 통한 Qwen3-8B)
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen3:8b
LLM_THINKING_MODE=true

# 기능 플래그
ENABLE_MOCK_MODE=false  # true: mock_data/ 사용, false: 실제 GCP 사용
```

**Mock 모드**: GCP 자격 증명 없이 로컬에서 테스트하려면 `ENABLE_MOCK_MODE=true`로 설정하세요. 백엔드는 `mock_data/synthetic_ati/`의 합성 데이터를 사용합니다.

### 프론트엔드 (`.env.local`)

**필수 변수**:
```bash
# 백엔드 API 엔드포인트
NEXT_PUBLIC_API_URL=http://localhost:9000

# 환경
NEXT_PUBLIC_ENV=development

# 기능 플래그 (선택)
NEXT_PUBLIC_ENABLE_MOCK_DATA=false
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_DEBUG=true
```

**프로덕션 변수** (Vercel 대시보드에서 설정):
```bash
NEXT_PUBLIC_API_URL=https://api.gg-poker-prod.run.app
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_DEBUG=false
```

**중요**:
- 모든 프론트엔드 환경 변수는 브라우저에서 접근하려면 `NEXT_PUBLIC_` 접두사가 필요합니다
- `.env.local`을 git에 커밋하지 마세요 (`.gitignore`에 있음)
- 새 개발자를 위한 템플릿으로 `.env.example` 사용

---

## 일반적인 개발 작업

### 프론트엔드: 새 페이지 추가

**예시**: 새로운 `/hands/:id` 페이지 추가

```bash
# 1. 페이지 파일 생성
mkdir -p frontend/src/app/hands
touch frontend/src/app/hands/[id]/page.tsx

# 2. 페이지 컴포넌트 구현
```

```tsx
// frontend/src/app/hands/[id]/page.tsx
import { HandDetail } from '@/components/hands/HandDetail';

export default async function HandPage({ params }: { params: { id: string } }) {
  return <HandDetail handId={params.id} />;
}
```

### 프론트엔드: 새 컴포넌트 추가

**예시**: 재사용 가능한 새 컴포넌트 생성

```bash
# 1. 컴포넌트 파일 생성
mkdir -p frontend/src/components/my-feature
touch frontend/src/components/my-feature/MyComponent.tsx

# 2. 테스트 파일 생성 (1:1 페어링 필수)
touch frontend/src/components/my-feature/MyComponent.test.tsx
```

```tsx
// frontend/src/components/my-feature/MyComponent.tsx
import { cn } from '@/lib/utils';

interface MyComponentProps {
  title: string;
  className?: string;
}

export function MyComponent({ title, className }: MyComponentProps) {
  return <div className={cn('p-4', className)}>{title}</div>;
}
```

```tsx
// frontend/src/components/my-feature/MyComponent.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders title', () => {
    render(<MyComponent title="Test" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

### 프론트엔드: API 클라이언트 추가

**예시**: 새 API 엔드포인트 클라이언트 추가

```typescript
// frontend/src/lib/api/my-feature.ts
import { fetchWithRetry, buildUrl } from './client';
import { ENV } from '@/lib/constants/config';

export interface MyFeatureResponse {
  data: string[];
}

export async function getMyFeature(id: string): Promise<MyFeatureResponse> {
  const url = buildUrl(`${ENV.API_URL}/api/my-feature/${id}`);
  return fetchWithRetry<MyFeatureResponse>(url);
}
```

### 백엔드: 새 API 엔드포인트 추가

**예시**: `backend/app/api/`에 새 엔드포인트 추가

```python
# backend/app/api/new_feature.py
from fastapi import APIRouter, HTTPException
from app.models import NewFeatureRequest, NewFeatureResponse

router = APIRouter()

@router.post("/new-feature", response_model=NewFeatureResponse)
async def new_feature(request: NewFeatureRequest):
    # 구현
    return NewFeatureResponse(...)

# backend/app/main.py
from app.api import new_feature
app.include_router(new_feature.router, prefix="/api", tags=["NewFeature"])
```

### BigQuery 스키마 수정

**⚠️ 중요**: BigQuery 스키마 변경은 조정이 필요합니다:

1. `tasks/schemas/bigquery_schema.json` 업데이트
2. `cloud_functions/index_metadata/main.py` 변환 로직 업데이트
3. 새 BigQuery 테이블 생성 또는 컬럼 추가 (기존 수정 불가)
4. `backend/app/models.py` Pydantic 모델 업데이트
5. 먼저 합성 데이터로 테스트

### Cloud Functions 업데이트

```bash
# 코드 편집
vim cloud_functions/index_metadata/main.py

# 로컬 테스트 (선택)
functions-framework --target=process_ati_metadata --debug

# 배포
cd cloud_functions/index_metadata
bash deploy.sh

# 로그 확인
gcloud functions logs read index-ati-metadata \
  --gen2 \
  --region=us-central1 \
  --limit=50
```

### RAG 파이프라인 테스트

```bash
# 터미널 1: Ollama 시작
ollama serve

# 터미널 2: 백엔드 실행
cd backend
uvicorn app.main:app --reload --port 9000

# 터미널 3: RAG 테스트
curl -X POST http://localhost:9000/api/rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Phil Ivey가 톰 드완을 상대로 블러프한 핸드를 찾아줘",
    "top_k": 5,
    "use_thinking_mode": true
  }'
```

---

## 코드 작성 가이드라인

### TypeScript/React 스타일 (프론트엔드)

- **TypeScript**: Strict 모드 활성화, 항상 타입 어노테이션 사용
- **React**: 함수형 컴포넌트와 훅 사용 (클래스 컴포넌트 사용 금지)
- **Next.js**: App Router 사용 (Pages Router 아님)
  - 페이지는 `frontend/src/app/`에 배치
  - 기본적으로 Server Components 사용
  - 필요할 때만 `'use client'` 지시어 추가 (상태, 효과, 브라우저 API)
- **네이밍**:
  - 컴포넌트: PascalCase (`SearchBar.tsx`)
  - 훅: camelCase에 `use` 접두사 (`useSearchResults.ts`)
  - 유틸: camelCase (`formatDate.ts`)
  - 타입: PascalCase 인터페이스 (`HandMetadata`)
- **Import 별칭**: 상대 경로 대신 항상 `@/` 사용
  - ✅ `import { cn } from '@/lib/utils'`
  - ❌ `import { cn } from '../../lib/utils'`
- **컴포넌트 구조**:
  ```tsx
  // 1. Import (React, 서드파티, 로컬)
  import { useState } from 'react';
  import { Button } from '@/components/ui/button';

  // 2. Types/Interfaces
  interface MyComponentProps {
    title: string;
  }

  // 3. Component
  export function MyComponent({ title }: MyComponentProps) {
    // 4. Hooks
    const [state, setState] = useState('');

    // 5. Handlers
    const handleClick = () => {};

    // 6. Render
    return <div>{title}</div>;
  }
  ```
- **테스트**: 모든 컴포넌트는 반드시 해당하는 `.test.tsx` 파일이 있어야 함
- **스타일링**: Tailwind CSS 유틸리티 클래스 사용, 조건부 클래스는 `cn()` 사용
- **에러 처리**: 항상 API 호출을 try-catch로 감싸고, 커스텀 에러 클래스 사용

### Python 스타일 (백엔드)

- Python 3.11+
- 타입 힌트 필수 (mypy로 강제)
- 데이터 검증에 Pydantic 사용
- PEP 8 준수 (`black` 포맷터 사용)
- 구조화된 로깅 사용 (structlog)

### API 설계

- RESTful 규칙
- HTTP 상태 코드 올바르게 사용 (200, 404, 422, 500)
- 타입 안전성을 위해 Pydantic 모델 반환 (백엔드)
- TypeScript 타입 반환 (프론트엔드)
- 응답에 에러 세부 정보 포함
- 필터에는 쿼리 파라미터, ID에는 경로 파라미터 사용
- 프론트엔드 API 클라이언트는 모든 에러 케이스 처리 (타임아웃, 네트워크, 검증, 속도 제한)

### GCP 통합

- 항상 Google Cloud 클라이언트 라이브러리 사용 (REST API 직접 사용 금지)
- 자격 증명 에러를 우아하게 처리
- 설정에 환경 변수 사용
- 로컬 테스트를 위한 Mock 모드 지원
- 일시적 에러에 대한 재시도 로직 추가

### 스키마 준수

- **ATI 메타데이터**: `tasks/schemas/ati_metadata_schema.json` 준수 필수
- **필수 필드**: hand_id, tournament_id, timestamp, description, hero_name, pot_bb, video_url
- **영문 전용**: 한글 텍스트 처리 불필요
- **임베딩**: 768 차원 (TextEmbedding-004)

### 성능 모범 사례 (프론트엔드)

- **이미지**: 항상 최적화를 위해 Next.js `<Image>` 컴포넌트 사용
- **지연 로딩**: 무거운 컴포넌트에 `dynamic()` 사용
- **코드 분할**: Next.js App Router로 자동
- **디바운스**: 검색 입력에 `useDebounce` 훅 사용
- **무한 스크롤**: 페이지네이션에 `useInfiniteScroll` 훅 사용
- **캐싱**: Next.js 내장 캐싱 활용 (fetch, React Cache)
- **번들 크기**: 초기 번들 < 200KB gzipped 유지

---

## 문제 해결

일반적인 문제와 해결 방법을 정리했습니다.

### 백엔드 문제

#### 1. "uvicorn not found" 오류

**증상**:
```
uvicorn : 용어가 cmdlet, 함수, 스크립트 파일 또는 실행할 수 있는 프로그램 이름으로 인식되지 않습니다.
```

**원인**: 가상환경이 활성화되지 않았거나 의존성이 설치되지 않음

**해결**:
```powershell
# 1. 가상환경 활성화
cd backend
.\venv\Scripts\Activate.ps1

# 2. 프롬프트 확인 (venv) 표시되어야 함
# (venv) PS D:\AI\claude01\archive-mam\backend>

# 3. 의존성 설치
pip install -r ../requirements-poc.txt

# 4. 서버 실행
uvicorn app.main:app --reload --port 9000
```

#### 2. "UnicodeDecodeError: 'cp949' codec" 오류

**증상**:
```
UnicodeDecodeError: 'cp949' codec can't decode byte 0xed
```

**원인**: Windows에서 UTF-8 파일을 cp949로 읽으려 함

**해결**:
```powershell
# UTF-8 환경변수 설정
$env:PYTHONUTF8=1

# 다시 설치
pip install -r ../requirements-poc.txt
```

#### 3. "Could not automatically determine credentials" 오류

**증상**:
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```

**원인**: GCP 인증이 설정되지 않음

**해결**:
```bash
# 1. gcloud CLI 설치 확인
gcloud --version

# 2. 인증
gcloud auth application-default login

# 3. 프로젝트 설정
gcloud config set project gg-poker-dev

# 4. API 활성화
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
```

#### 4. "Connection refused to localhost:11434" (Ollama)

**증상**:
```
httpx.ConnectError: [Errno 111] Connection refused
```

**원인**: Ollama 서버가 실행되지 않음

**해결**:
```powershell
# 1. Ollama 설치 확인
ollama --version

# 2. 설치 안 되어 있으면
# https://ollama.ai 에서 다운로드

# 3. Qwen3 모델 다운로드
ollama pull qwen3:8b

# 4. Ollama 서버 시작
ollama serve

# 5. 확인
ollama list
```

### 프론트엔드 문제

#### 1. "Module not found: Can't resolve '@/...'" 오류

**증상**:
```
Module not found: Can't resolve '@/lib/utils'
```

**원인**: TypeScript 경로 별칭 설정 문제

**해결**:
```powershell
# 1. tsconfig.json 확인
cd frontend
type tsconfig.json

# 2. paths 설정 확인
# {
#   "compilerOptions": {
#     "baseUrl": ".",
#     "paths": {
#       "@/*": ["./src/*"]
#     }
#   }
# }

# 3. 의존성 재설치
rm -rf node_modules
npm install

# 4. 서버 재시작
npm run dev -- -p 9001
```

#### 2. "Hydration failed" 오류

**증상**:
```
Hydration failed because the initial UI does not match what was rendered on the server
```

**원인**: Server Component에서 브라우저 API 사용

**해결**:
```tsx
// ❌ 나쁜 예
export default function MyComponent() {
  const [state, setState] = useState('');  // Server Component에서 useState 사용
  return <div>{state}</div>;
}

// ✅ 좋은 예
'use client';  // Client Component로 명시
export default function MyComponent() {
  const [state, setState] = useState('');
  return <div>{state}</div>;
}
```

#### 3. "CORS error" - API 호출 실패

**증상**:
```
Access to fetch at 'http://localhost:9000/api/search' from origin 'http://localhost:9001' has been blocked by CORS policy
```

**원인**: 백엔드 CORS 설정 누락

**해결**:
```python
# backend/app/main.py 확인
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9001",  # 프론트엔드 URL 추가
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 4. "Cannot find module" 테스트 오류

**증상**:
```
Error: Cannot find module '@testing-library/jest-dom'
```

**원인**: 테스트 환경 설정 누락

**해결**:
```powershell
# 1. vitest.setup.ts 확인
type vitest.setup.ts

# 2. 없으면 생성
@"
import '@testing-library/jest-dom';
"@ | Out-File -FilePath vitest.setup.ts -Encoding UTF8

# 3. 의존성 설치
npm install --save-dev @testing-library/jest-dom

# 4. 캐시 삭제 후 재실행
npm test -- --no-cache
```

### GCP 연결 문제

#### 1. BigQuery "Not Found" 오류

**증상**:
```
google.api_core.exceptions.NotFound: 404 Table not found
```

**원인**: BigQuery 테이블이 생성되지 않음

**해결**:
```bash
# 1. 프로젝트 확인
gcloud config get-value project

# 2. 테이블 목록 확인
bq ls gg-poker-dev:poker_archive_dev

# 3. 테이블 없으면 생성
bash create_bigquery_table.sh

# 4. 확인
bq show gg-poker-dev:poker_archive_dev.hand_summary
```

#### 2. Vertex AI 임베딩 오류

**증상**:
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**원인**: API 할당량 초과

**해결**:
```bash
# 1. 할당량 확인
gcloud services list --enabled | grep aiplatform

# 2. Google Cloud Console에서 할당량 확인
# https://console.cloud.google.com/iam-admin/quotas

# 3. Mock 모드로 테스트
# backend/.env 파일에서
ENABLE_MOCK_MODE=true
```

#### 3. Cloud Functions 권한 오류

**증상**:
```
Permission denied: Missing permission on resource
```

**원인**: IAM 역할 누락

**해결**:
```bash
# 권한 수정 스크립트 실행
bash scripts/gcp/setup/fix_permissions.sh

# 재배포
bash scripts/gcp/deploy/final_deploy.sh

# 10초 대기 (권한 전파)
```

### Ollama/LLM 문제

#### 1. Ollama 모델 다운로드 실패

**증상**:
```
Error: model 'qwen3:8b' not found
```

**해결**:
```bash
# 1. Ollama 재시작
# Ctrl+C로 중지 후

# 2. 모델 다운로드
ollama pull qwen3:8b

# 3. 확인
ollama list
# NAME          ID              SIZE
# qwen3:8b      xxxxx          4.7GB

# 4. Ollama 서버 재시작
ollama serve
```

#### 2. RAG 응답 느림

**증상**: RAG API 호출 시 30초 이상 걸림

**원인**: Ollama가 CPU에서 실행 중

**해결**:
```bash
# GPU 사용 확인 (Windows)
nvidia-smi

# Ollama GPU 버전 재설치
# https://ollama.ai 에서 GPU 버전 다운로드

# 또는 타임아웃 늘리기 (임시)
# backend/.env
LLM_TIMEOUT=60  # 기본 30초 → 60초
```

### 일반적인 문제

#### 1. 포트 충돌

**증상**:
```
Error: listen EADDRINUSE: address already in use :::9000
```

**해결**:
```powershell
# Windows에서 포트 사용 확인
netstat -ano | findstr :9000

# 프로세스 종료
taskkill /PID <PID번호> /F

# 또는 다른 포트 사용
# backend
uvicorn app.main:app --reload --port 9002

# frontend
npm run dev -- -p 9003
```

#### 2. PowerShell 실행 정책 오류

**증상**:
```
.\start_backend.ps1 cannot be loaded because running scripts is disabled
```

**해결**:
```powershell
# 실행 정책 변경 (한 번만)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 확인
Get-ExecutionPolicy

# 스크립트 실행
.\start_backend.ps1
```

#### 3. Git Bash vs PowerShell 명령어 차이

**PowerShell**:
```powershell
copy .env.example .env
type .env
```

**Git Bash / Mac / Linux**:
```bash
cp .env.example .env
cat .env
```

### 로그 확인 방법

**백엔드 로그**:
```bash
# 콘솔 출력 확인
# uvicorn 실행 중인 터미널

# 또는 파일 로그 (설정된 경우)
tail -f logs/app.log
```

**프론트엔드 로그**:
```
# 브라우저 Console
F12 → Console 탭

# 또는 터미널
# npm run dev 실행 중인 터미널
```

**Cloud Functions 로그**:
```bash
gcloud functions logs read index-ati-metadata \
  --gen2 \
  --region=us-central1 \
  --limit=50
```

### 자주 묻는 질문 (FAQ)

**Q: Mock 모드는 어떻게 사용하나요?**

A:
```bash
# backend/.env 파일에서
ENABLE_MOCK_MODE=true

# 서버 재시작
# mock_data/synthetic_ati/ 데이터 사용
```

**Q: 프로덕션 배포는 어떻게 하나요?**

A:
```bash
# 프론트엔드 (Vercel)
cd frontend
vercel --prod

# 백엔드 (Cloud Run)
cd backend
gcloud run deploy poker-archive-api \
  --source . \
  --region us-central1
```

**Q: 테스트는 어떻게 실행하나요?**

A:
```bash
# 백엔드
cd backend
pytest tests/ -v

# 프론트엔드
cd frontend
npm test              # 유닛 테스트
npm run e2e           # E2E 테스트
npm run test:coverage # 커버리지
```

---

## 성능 목표

| 지표 | 목표 | 현재 상태 |
|--------|--------|----------------|
| 검색 지연 시간 (p95) | <100ms | ✅ 달성 (<80ms) |
| RAG 지연 시간 (p95) | <3초 | ✅ 달성 (<2.5초) |
| ETL 지연 시간 | <5초 | ✅ 초과 달성 (<1초) |
| 검색 정확도 (P@5) | ≥85% | 🔄 테스트 진행 중 |
| LLM 답변 품질 | ≥4.0/5.0 | 🔄 평가 대기 중 |

---

## 다음 단계

### Phase 3: Video Archive Management UI (진행 중)
- ✅ 기본 검색 API
- ✅ Qwen3-8B RAG API
- ✅ BigQuery 통합
- 🚧 비디오용 GCS Signed URL
- 🚧 Cloud Run 배포

### Phase 4: 프로덕션 배포 (계획)
- ⬜ Vercel 프론트엔드 배포
- ⬜ Cloud Run 백엔드 배포
- ⬜ 필터 추가 (팟 크기, 태그, 플레이어)
- ⬜ 성능 최적화
- ⬜ 모니터링 설정

---

## 비용 개요 (현재 PoC)

| 서비스 | 사용량 | 비용/월 |
|---------|-------|------------|
| Cloud Functions | ~100회 호출 | $0 (무료 티어) |
| BigQuery | 10행, <1GB | $0 (무료 티어) |
| Vertex AI 임베딩 | ~50회 호출 | $0 (무료 티어) |
| Vertex AI Vector Search | 개발 인덱스 | ~$50 |
| GCS 저장소 | <1GB | $0 (무료 티어) |
| **총계** | | **~$50/월** |

**프로덕션 예상**: $96-222/월

---

## 참조

**GCP 문서**:
- [Vertex AI Vector Search](https://cloud.google.com/vertex-ai/docs/vector-search/overview)
- [Cloud Functions Gen2](https://cloud.google.com/functions/docs/2nd-gen/overview)
- [BigQuery 모범 사례](https://cloud.google.com/bigquery/docs/best-practices)

**프로젝트 문서**:
- `docs/README.md` - 프로젝트 개요 (사용자용)
- `docs/QUICKSTART.md` - 5분 빠른 시작 (사용자용)

**외부**:
- [Next.js 문서](https://nextjs.org/docs)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Qwen3 모델](https://qwenlm.github.io/)

---

## 빠른 참조

### 가장 일반적인 명령어

**프론트엔드 개발**:
```bash
cd frontend
npm install           # 의존성 설치
npm run dev          # 개발 서버 시작 (http://localhost:9001)
npm test             # 유닛 테스트 실행
npm run e2e          # E2E 테스트 실행
npm run type-check   # TypeScript 검증
npm run build        # 프로덕션 빌드
```

**백엔드 개발**:
```bash
cd backend
pip install -r ../requirements-poc.txt
uvicorn app.main:app --reload --port 9000  # 개발 서버 시작
pytest tests/        # 테스트 실행
```

**풀스택 테스트**:
```bash
# 터미널 1: 백엔드
cd backend && uvicorn app.main:app --reload --port 9000

# 터미널 2: 프론트엔드
cd frontend && npm run dev

# 터미널 3: E2E 테스트
cd frontend && npm run e2e:ui
```

### 프로젝트 구조 한눈에

```
archive-mam/
├── CLAUDE.md              # 개발자 가이드 (통합 문서)
├── README.md              # 프로젝트 개요 (사용자용)
│
├── docs/                  # 사용자 문서 (2개)
│   ├── README.md          # 프로젝트 개요
│   └── QUICKSTART.md      # 5분 빠른 시작
│
├── frontend/              # Next.js 16 + React 19 (Vercel)
│   ├── src/
│   │   ├── app/          # 페이지 (App Router)
│   │   ├── components/   # React 컴포넌트
│   │   ├── hooks/        # 커스텀 React 훅
│   │   ├── lib/          # 유틸리티, API 클라이언트
│   │   └── types/        # TypeScript 타입
│   ├── e2e/              # Playwright E2E 테스트
│   └── package.json
│
├── backend/              # FastAPI + RAG (Cloud Run)
│   ├── app/
│   │   ├── api/         # API 엔드포인트
│   │   ├── services/    # 비즈니스 로직
│   │   └── main.py      # FastAPI 앱
│   └── tests/
│
├── cloud_functions/      # GCP Cloud Functions
│   └── index_metadata/  # ETL 파이프라인
│
├── scripts/              # 유틸리티 스크립트
│   ├── gcp/             # GCP 관련 스크립트
│   │   ├── setup/       # 초기 설정 (complete_setup.sh, create_bigquery_table.sh 등)
│   │   ├── deploy/      # 배포 (deploy-cloud-run.sh, final_deploy.sh)
│   │   └── test/        # 테스트 (test_integration.sh, test_deployment.sh)
│   ├── vertex-ai/       # Vertex AI 설정
│   └── generate_synthetic_ati_data.py
│
├── tasks/               # AI 참조 문서
│   ├── prds/           # PRD 문서
│   ├── schemas/        # 데이터 스키마
│   └── references/     # 참조 자료
│
└── mock_data/          # 합성 테스트 데이터
    └── synthetic_ati/
```

### 기술 스택 요약

| 레이어 | 기술 |
|-------|-----------|
| **프론트엔드** | Next.js 16, React 19, TypeScript, Tailwind CSS |
| **백엔드** | FastAPI, Python 3.11, Pydantic |
| **데이터베이스** | BigQuery, Vertex AI Vector Search |
| **LLM** | Qwen3-8B (Ollama 통해) |
| **저장소** | GCS (영상 + 임베딩) |
| **배포** | Vercel (프론트엔드), Cloud Run (백엔드) |
| **테스트** | Vitest (유닛), Playwright (E2E), pytest (백엔드) |

---

**버전**: v5.0.0
**최종 업데이트**: 2025-11-20
**상태**: Phase 2 완료 (Backend + Frontend), Phase 3 진행 중 (Video Archive UI)
**연락처**: aiden.kim@ggproduction.net
