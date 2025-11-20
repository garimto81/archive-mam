# 포커 아카이브 RAG 검색 시스템 - Backend (v1.3.0)

FastAPI 기반 백엔드 서버 (Vertex AI + Qwen3-8B)

---

## 빠른 시작

### 1. Python 가상 환경 설정

```bash
# 가상 환경 생성
python -m venv venv

# 활성화 (Windows)
venv\Scripts\activate

# 활성화 (Mac/Linux)
source venv/bin/activate
```

### 2. 의존성 설치

```bash
# PoC 의존성 설치
pip install -r ../requirements-poc.txt
```

### 3. 환경 변수 설정

```bash
# .env.poc 파일을 backend/.env로 복사
copy ..\.env.poc .env

# .env 파일 수정 (필수)
# - GCP_PROJECT: GCP 프로젝트 ID
# - GCS_BUCKET_*: GCS 버킷 이름
# - VERTEX_INDEX_ID: Vertex AI 인덱스 ID
# - VERTEX_INDEX_ENDPOINT_ID: Vertex AI 엔드포인트 ID
```

**Mock 모드 사용 (GCP 없이 테스트)**:
```bash
# .env 파일에서 다음 설정 변경
ENABLE_MOCK_MODE=true
```

### 4. FastAPI 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python -m app.main
```

서버가 http://localhost:8000 에서 실행됩니다.

### 5. API 문서 확인

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

---

## API 엔드포인트

### Health Check
```bash
GET http://localhost:8000/health
```

### 검색 API
```bash
GET http://localhost:8000/api/search?query=Phil Ivey bluff&top_k=5
```

### 핸드 상세 정보
```bash
GET http://localhost:8000/api/hands/hand_001
```

### RAG 답변 생성
```bash
POST http://localhost:8000/api/rag
Content-Type: application/json

{
  "query": "Phil Ivey의 블러프 전략은?",
  "top_k": 5,
  "use_thinking_mode": true
}
```

---

## 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 환경 변수 설정
│   ├── models.py            # Pydantic 모델
│   ├── api/                 # API 라우터
│   │   ├── search.py        # GET /api/search
│   │   ├── hands.py         # GET /api/hands/{id}
│   │   └── rag.py           # POST /api/rag
│   ├── services/            # 서비스 레이어
│   │   ├── llm_service.py   # Qwen3-8B LLM
│   │   ├── vertex_search.py # Vertex AI 검색
│   │   └── bigquery.py      # BigQuery 조회
│   └── utils/               # 유틸리티
└── tests/                   # 테스트 코드
```

---

## 개발 가이드

### 테스트 실행

```bash
# 모든 테스트
pytest tests/ -v

# 커버리지 포함
pytest tests/ -v --cov=app --cov-report=term-missing
```

### 코드 포맷팅

```bash
# Black
black app/ tests/

# Flake8
flake8 app/ tests/

# MyPy (타입 체크)
mypy app/
```

### Mock 모드 vs Production 모드

**Mock 모드** (`ENABLE_MOCK_MODE=true`):
- GCP 인증 불필요
- mock_data/ 폴더의 샘플 데이터 사용
- 로컬 개발 및 테스트용

**Production 모드** (`ENABLE_MOCK_MODE=false`):
- GCP 인증 필요 (`gcloud auth application-default login`)
- 실제 Vertex AI, BigQuery 사용
- 비용 발생

---

## 환경 변수

주요 환경 변수 (`.env.poc` 파일):

```bash
# Application
APP_NAME=poker-archive-rag-poc
APP_VERSION=1.3.0
ENVIRONMENT=development

# GCP
GCP_PROJECT=gg-poker-dev
GCS_BUCKET_ATI_METADATA=gg-poker-dev-ati-metadata
VERTEX_INDEX_ID=poker_hands_index_dev
VERTEX_INDEX_ENDPOINT_ID=poker_hands_endpoint_dev

# LLM (Qwen3-8B)
LLM_PROVIDER=ollama  # ollama | huggingface
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen3:8b

# Feature Flags
ENABLE_MOCK_MODE=false  # true: mock data, false: real GCP
```

전체 환경 변수 목록은 `.env.poc` 파일을 참조하세요.

---

## 트러블슈팅

### 1. Ollama 연결 오류
```
Error: Connection refused to http://localhost:11434
```

**해결**:
```bash
# Ollama 서비스 시작
ollama serve

# Qwen3-8B 모델 확인
ollama list
```

### 2. GCP 인증 오류
```
Error: Could not automatically determine credentials
```

**해결**:
```bash
# GCP 인증
gcloud auth application-default login

# 프로젝트 확인
gcloud config get-value project
```

### 3. Mock 데이터 없음
```
Error: mock_data/synthetic_ati/ not found
```

**해결**:
```bash
# 합성 데이터 생성 (루트 디렉토리에서)
python scripts/generate_synthetic_ati_data.py
```

---

## 성능 목표 (PoC)

- **검색 응답 시간**: <100ms (p95)
- **RAG 응답 시간**: <3초 (p95)
- **검색 정확도**: ≥85% (Precision@5)
- **LLM 답변 품질**: ≥4.0/5.0 (사람 평가)

---

## 다음 단계

1. **Ollama 설치**: `scripts/setup_ollama.bat` 실행
2. **GCP 인프라 구축**: POC_QUICK_START.md 참조 (Phase 1)
3. **ETL 파이프라인 구현**: Phase 2
4. **Perplexica UI 연동**: Phase 4

---

**문서 버전**: 1.3.0
**최종 업데이트**: 2025-11-18
