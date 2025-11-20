# Archive MAM - 포커 핸드 영상 검색 시스템

> AI 기반 포커 핸드 영상 검색 및 학습 시스템

[![Version](https://img.shields.io/badge/version-5.0.0-blue.svg)](https://github.com/your-repo/archive-mam)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎯 프로젝트 개요

GGProduction의 WSOP/MPP/APL 포커 대회 아카이브 영상을 **ATI 메타데이터 기반으로 자연어 검색**하는 시스템입니다.

### 🌐 GGProduction 영상 처리 생태계

이 프로젝트는 **3개 연결된 프로젝트 중 2번째**입니다 (인과관계 순서):

```
[0. qwen_hand_analysis] → [1. archive-mam ⭐] → [2. man_subclip]
   Gemini AI 핸드 분석      검색 & 아카이빙       영상 편집 플랫폼
```

**인과관계**:
- **0 → 1 (필수 ⭐)**: qwen_hand_analysis가 생성한 메타데이터를 archive-mam이 검색 인덱싱
- **1 → 2 (선택)**: archive-mam 검색 결과를 man_subclip에서 편집용으로 활용 가능

**상세 설명**: 개발자는 `CLAUDE.md`의 생태계 섹션 참조

### 핵심 원칙

**ATI (Automated Text Indexing)**:
- ✅ ATI가 이미 영상 분석 완료 → 메타데이터 (XML/JSON) 제공
- ✅ 텍스트 검색만 필요 → 영상 재분석 불필요
- ✅ 영문 메타데이터만 → 한글 형태소 분석 불필요

### 핵심 기능

- ✅ **자연어 검색**: "junglemann crazy river call", "hellmuth bluff"
- ✅ **하이브리드 검색**: Vector (semantic) + BM25 (keyword) + RRF (rank fusion)
- ✅ **실시간 인덱싱**: GCS Pub/Sub 트리거 (<1초)
- ✅ **GCP 네이티브**: Vertex AI Vector Search + BigQuery 완전 통합
- ✅ **검증된 UI**: Perplexica (Perplexity 오픈소스 클론, 13k+ stars)

---

## 📊 성능 목표

| 지표 | 목표 | 근거 |
|------|------|------|
| **검색 응답** | <100ms | Vertex AI Vector Search (Google Search 동일 기술) |
| **인덱싱** | <1초 | Pub/Sub 실시간 트리거 |
| **검색 정확도** | 85-95% | Hybrid search (BM25 + Vector + RRF) |
| **동시 사용자** | 10-100 | Auto-scaling (Cloud Run + Vertex AI) |

---

## 🏗️ 최종 아키텍처 (v4.0.0)

```
[ATI 분석기]
    ↓ 메타데이터 저장
[GCS JSON 파일] (원본 보관, 불변)
    ↓ Pub/Sub 트리거 (실시간)
[Cloud Functions]
  - JSON 파싱
  - Vertex AI Embedding API (TextEmbedding-004)
  - BM25 Sparse Vector 생성
    ↓
┌───────────┴───────────┐
↓                       ↓
[BigQuery]          [Vertex AI Vector Search]
- SQL 쿼리             - 하이브리드 검색 (<100ms)
- BI/분석              - BM25 + Vector + RRF
- 스키마 검증          - Auto-scaling
    ↓                       ↓
[Looker/Tableau]      [FastAPI Backend (Cloud Run)]
                            ↓
                      [Perplexica UI (Vercel)]
                      - 검색 바
                      - 핸드 카드 (썸네일)
                      - 비디오 플레이어
                      - 필터 (Pot Size, Tags, alpha)
```

### Tech Stack

**Search Engine**:
- **Vertex AI Vector Search** (GCP 네이티브)
  - TextEmbedding-004 (1024차원)
  - Hybrid search 내장 (BM25 + Vector + RRF)
  - Auto-scaling, <100ms 응답
  - Google Search 동일 기술

**Data Storage**:
- **GCS** (원본 JSON 보관)
- **BigQuery** (SQL 쿼리, BI 연동)
- Hybrid architecture (각 용도별 최적화)

**Backend API**:
- **FastAPI** (Python 3.11)
- **Cloud Run** (서버리스)
- `/api/search`, `/api/hands/{id}`, `/api/video/{id}/url`

**Frontend**:
- **Perplexica** (Next.js 14 + TypeScript, MIT 라이선스)
- GitHub: https://github.com/ItzCrazyKns/Perplexica
- 13,000+ stars, Perplexity UI 검증됨
- shadcn/ui + Tailwind CSS

**ETL**:
- Cloud Functions (GCS → BigQuery + Vertex AI)
- Pub/Sub (실시간 트리거)

---

## 💰 비용 분석

| 컴포넌트 | 솔루션 | 비용/월 (10만 핸드 기준) |
|---------|--------|-------------------------|
| **검색 엔진** | Vertex AI Vector Search | $70-145 |
| **데이터 저장** | GCS + BigQuery | $6-12 |
| **백엔드 API** | FastAPI (Cloud Run) | $10-30 |
| **ETL** | Cloud Functions + Pub/Sub | $10-15 |
| **프론트엔드** | Perplexica (Vercel) | $0-20 |
| **총합** | | **$96-222/월** |

**초기 구축 비용**: $0 (GCP 종량제)
**UI 개발 비용 절감**: $2000-5000 (Perplexica 사용)

---

## 🚀 Quick Start

### 1. 환경 설정

```bash
# Python 가상환경
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. GCP 설정

```bash
# GCP 프로젝트 설정
export GCP_PROJECT=gg-poker-prod
gcloud config set project $GCP_PROJECT

# 인증
gcloud auth application-default login

# 필요한 API 활성화
gcloud services enable \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  cloudfunctions.googleapis.com \
  pubsub.googleapis.com \
  storage.googleapis.com
```

### 3. GCS 버킷 생성

```bash
# 메타데이터 버킷
gsutil mb -p $GCP_PROJECT -c STANDARD -l us-central1 gs://ati-metadata-prod

# 영상 버킷
gsutil mb -p $GCP_PROJECT -c STANDARD -l us-central1 gs://poker-videos-prod
```

### 4. BigQuery 테이블 생성

```bash
# 테이블 생성
bq mk --dataset $GCP_PROJECT:poker_archive

bq mk --table $GCP_PROJECT:poker_archive.hands \
  app/db/bigquery_schema.json
```

### 5. Vertex AI 인덱스 생성

```bash
# 인덱스 생성 (Cloud Console에서 수동 또는 gcloud CLI)
# 상세 가이드: docs/vertex-ai-setup.md
```

### 6. Cloud Functions 배포

```bash
cd cloud_functions/index_metadata

gcloud functions deploy index-ati-metadata \
  --runtime python311 \
  --trigger-bucket ati-metadata-prod \
  --entry-point process_ati_metadata \
  --region us-central1
```

### 7. FastAPI 백엔드 실행 (로컬)

```bash
# 환경변수 설정
export GCP_PROJECT=gg-poker-prod
export VERTEX_AI_INDEX_ENDPOINT=projects/.../indexEndpoints/...

# 서버 실행
uvicorn app.main:app --reload --port 8000

# 테스트
curl http://localhost:8000/health
curl "http://localhost:8000/api/search?q=junglemann+river+call"
```

### 8. Perplexica UI 실행

```bash
# Perplexica 클론
git clone https://github.com/ItzCrazyKns/Perplexica.git
cd Perplexica

# 환경변수 설정
cp .env.example .env
# .env 파일에서 NEXT_PUBLIC_API_URL=http://localhost:8000 설정

# 의존성 설치 및 실행
npm install
npm run dev

# 브라우저에서 http://localhost:3000 열기
```

---

## 📁 프로젝트 구조

```
archive-mam/
├── app/                      # FastAPI 백엔드
│   ├── api/                  # API 엔드포인트
│   ├── db/                   # BigQuery 스키마
│   ├── search/               # Vertex AI 검색 로직
│   └── main.py
│
├── cloud_functions/          # GCS 트리거 함수
│   └── index_metadata/       # ATI 메타데이터 인덱싱
│       ├── main.py
│       └── requirements.txt
│
├── docs/                     # 문서
│   ├── vertex-ai-setup.md
│   ├── bigquery-schema.md
│   └── perplexica-customization.md
│
├── issues/                   # 아키텍처 결정 기록
│   ├── ISSUE-001-text-search-requirements.md
│   ├── ISSUE-002-english-only-requirements.md
│   ├── ISSUE-003-gcs-integration.md
│   └── ISSUE-004-final-architecture.md
│
├── tests/                    # 테스트
│
├── .env.example              # 환경변수 템플릿
├── requirements.txt
├── CLAUDE.md                 # Claude Code 가이드
├── FINAL_RECOMMENDATION_GCS.md     # 백엔드 + 검색 엔진 분석
├── UI_OPENSOURCE_RECOMMENDATION.md # 프론트엔드 UI 분석
├── METADATA_STORAGE_ANALYSIS.md    # 메타데이터 저장 방식 분석
└── README.md                 # 이 파일
```

---

## 🔍 검색 예시

### 자연어 검색

```bash
# API 호출
curl "http://localhost:8000/api/search?q=junglemann+crazy+river+call&limit=20"

# 응답
{
  "results": [
    {
      "hand_id": "wsop_2024_main_event_hand_3421",
      "score": 0.92,
      "hero_name": "Junglemann",
      "villain_name": "Phil Ivey",
      "pot_bb": 145.5,
      "description": "Junglemann makes an insane river call with ace-high...",
      "tags": ["HERO_CALL", "RIVER_DECISION", "HIGH_STAKES"],
      "video_url": "gs://poker-videos-prod/wsop_2024/main_event/day5_table3.mp4",
      "video_start": 3421.5,
      "video_end": 3482.0,
      "thumbnail_url": "https://..."
    },
    ...
  ],
  "total": 47,
  "query_time_ms": 78
}
```

### 필터 검색

```bash
curl "http://localhost:8000/api/search?q=bluff&min_pot_bb=100&tournament=wsop_2024&tag=BLUFF"
```

---

## 📚 관련 문서

**아키텍처 결정 기록**:
- `issues/ISSUE-001-text-search-requirements.md` - 텍스트 검색 요구사항
- `issues/ISSUE-002-english-only-requirements.md` - 영문 전용 요구사항
- `issues/ISSUE-003-gcs-integration.md` - GCS 통합 요구사항
- `issues/ISSUE-004-final-architecture.md` - 최종 아키텍처 결정

**기술 분석**:
- `FINAL_RECOMMENDATION_GCS.md` - 백엔드 + 검색 엔진 비교 분석
- `UI_OPENSOURCE_RECOMMENDATION.md` - 프론트엔드 UI 비교 분석
- `METADATA_STORAGE_ANALYSIS.md` - 메타데이터 저장 방식 분석
- `SOLUTION_COMPARISON.md` - 솔루션 비교 (PostgreSQL vs 대안)

**구현 가이드**:
- `docs/vertex-ai-setup.md` - Vertex AI Vector Search 설정
- `docs/bigquery-schema.md` - BigQuery 스키마 설계
- `docs/perplexica-customization.md` - Perplexica UI 커스터마이징

---

## 📈 구현 로드맵

### Phase 1: PoC (1주)
1. ✅ Vertex AI Vector Search 설정
2. ✅ Cloud Functions (GCS → Vertex AI + BigQuery)
3. ✅ FastAPI 백엔드 (검색 API)
4. ✅ Perplexica Fork (로컬 실행)

### Phase 2: 개발 (1주)
5. ⬜ Perplexica → FastAPI 연결
6. ⬜ 핸드 카드 UI (비디오 썸네일)
7. ⬜ 필터 UI (Pot Size, Tags, alpha)
8. ⬜ 비디오 플레이어 (GCS Signed URL)

### Phase 3: 배포 (2-3일)
9. ⬜ Cloud Run 배포 (FastAPI)
10. ⬜ Vercel 배포 (Perplexica)
11. ⬜ 통합 테스트
12. ⬜ Production 런칭

**예상 총 개발 시간**: **2주**

---

## 🤝 Contributing

Private repository - GGProduction 내부 프로젝트

---

## 📄 License

Private - All Rights Reserved

---

## 📧 Contact

- **Project Owner**: aiden.kim@ggproduction.net
- **Tech Lead**: Claude (AI Assistant)

---

**Version**: 4.0.0 (2025-01-18)
**Last Updated**: 2025-01-18
**Architecture Status**: APPROVED (ISSUE-004)
