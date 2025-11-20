# Archive MAM - 포커 핸드 영상 검색 시스템

## 📖 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [시작하기](#시작하기)
4. [주요 기능](#주요-기능)
5. [문서 가이드](#문서-가이드)

---

## 프로젝트 개요

**"프로 포커 플레이어들의 핸드 영상을 AI로 검색하고 학습할 수 있는 시스템"**

### 문제점
- 유튜브에 포커 영상은 많지만 특정 상황을 찾기 어려움
- 텍스트 검색으로는 맥락 이해 불가
- 원하는 장면 찾기까지 시간 낭비

### 해결책
- **ATI 메타데이터**: 핸드별 상세 분석 정보
- **AI 검색**: 자연어로 의미 기반 검색
- **타임스탬프**: 영상에서 바로 해당 장면으로 이동

---

## 시스템 아키텍처

```
[사용자] ←→ [Next.js 프론트엔드 (Vercel)]
                 ↓
            [FastAPI 백엔드 (Cloud Run)]
               ↙          ↘
    [Vertex AI Search]  [BigQuery]
           ↓                ↓
    [Vector Index]    [핸드 메타데이터]
                          ↓
                    [GCS 영상]
```

### 기술 스택

| 레이어 | 기술 |
|--------|------|
| **프론트엔드** | Next.js 16, React 19, TypeScript, Tailwind CSS |
| **백엔드** | FastAPI, Python 3.11, Pydantic |
| **데이터베이스** | BigQuery, Vertex AI Vector Search |
| **LLM** | Qwen3-8B (Ollama) |
| **저장소** | GCS (영상 + 임베딩) |
| **배포** | Vercel (프론트엔드), Cloud Run (백엔드) |

---

## 시작하기

### 빠른 시작 (5분)

```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd archive-mam

# 2. 백엔드 실행 (포트 9000)
cd backend
python -m venv venv
venv\Scripts\Activate.ps1  # Windows
pip install -r ../requirements-poc.txt
copy ..\.env.poc .env
uvicorn app.main:app --reload --port 9000

# 3. 프론트엔드 실행 (포트 9001, 새 터미널)
cd frontend
npm install
npm run dev -- -p 9001
```

**접속 URL**:
- 프론트엔드: http://localhost:9001
- 백엔드 API 문서: http://localhost:9000/docs

### 자동 실행 스크립트

```powershell
# 루트 디렉토리에서
.\START_SERVERS.ps1
```

---

## 주요 기능

### 1. AI 검색
```
입력: "Phil Ivey가 블러프한 핸드"
  ↓
Vertex AI 의미 검색
  ↓
관련 핸드 5개 반환
```

### 2. RAG 답변
```
질문: "Phil Ivey의 블러프 전략은?"
  ↓
1. 관련 핸드 검색
2. Qwen3-8B에 전달
3. AI 답변 생성
```

### 3. 필터링
- 팟 크기 (100BB 이상)
- 플레이어 (Phil Ivey, Tom Dwan 등)
- 태그 (bluff, all-in, hero-call 등)

### 4. 영상 재생
- GCS 영상 스트리밍
- 타임스탬프로 정확한 위치 이동
- 핸드 타임라인 표시

---

## 문서 가이드

### 사용자 문서 (이 폴더)
- **README.md** (이 파일) - 프로젝트 개요 및 시작 가이드
- **QUICKSTART.md** - 5분 빠른 시작 가이드
- **TROUBLESHOOTING.md** - 문제 해결 가이드

### 개발자 문서
- **CLAUDE.md** (루트) - 개발자용 상세 가이드
- **backend/README.md** - 백엔드 개발 가이드
- **frontend/README.md** - 프론트엔드 개발 가이드

### 참조 문서 (tasks 폴더)
- **tasks/schemas/** - 데이터 스키마
- **tasks/prds/** - PRD 문서
- **tasks/references/** - 참조 자료

---

## 개발 워크플로우

### 로컬 개발
1. 백엔드 시작 (포트 9000)
2. 프론트엔드 시작 (포트 9001)
3. 코드 수정 후 자동 새로고침

### 테스트
```bash
# 백엔드 테스트
cd backend
pytest tests/

# 프론트엔드 테스트
cd frontend
npm test                    # 유닛 테스트
npm run e2e                # E2E 테스트
```

### 배포
```bash
# 프론트엔드 (Vercel)
cd frontend
vercel --prod

# 백엔드 (Cloud Run)
cd backend
gcloud run deploy
```

---

## 환경 변수

### 백엔드 (.env)
```bash
GCP_PROJECT=gg-poker-dev
BQ_DATASET=poker_archive_dev
VERTEX_AI_INDEX_ENDPOINT=projects/.../indexEndpoints/...
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:8b
```

### 프론트엔드 (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:9000
NEXT_PUBLIC_ENV=development
```

---

## 프로젝트 상태

| Phase | 상태 | 설명 |
|-------|------|------|
| Phase 1 | ✅ 완료 | GCS → BigQuery ETL 파이프라인 |
| Phase 1.5 | ✅ 완료 | Vertex AI 임베딩 생성 |
| Phase 2 | ✅ 완료 | FastAPI 백엔드 + Next.js 프론트엔드 |
| Phase 3 | 🚧 진행중 | Video Archive Management UI |
| Production | ⬜ 계획 | Vercel + Cloud Run 배포 |

---

## 주요 디렉토리

```
archive-mam/
├── docs/              # 사용자 문서 (이 폴더)
├── tasks/             # AI 참조 문서
├── backend/           # FastAPI 백엔드
├── frontend/          # Next.js 프론트엔드
├── cloud_functions/   # GCP Cloud Functions
├── scripts/           # 유틸리티 스크립트
└── mock_data/         # 테스트 데이터
```

---

## 문제 해결

문제 발생 시:
1. [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) 확인
2. [CLAUDE.md](../CLAUDE.md) 개발자 가이드 참조
3. 백엔드 로그 확인: `http://localhost:9000/docs`
4. 프론트엔드 콘솔 확인: F12 → Console

---

## 라이선스 및 연락처

- **Version**: v5.0.0
- **Last Updated**: 2025-01-20
- **Contact**: aiden.kim@ggproduction.net
