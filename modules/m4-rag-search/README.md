# M4 RAG Search Service

**POKER-BRAIN WSOP Archive System - M4 Module**

Vertex AI 기반 자연어 검색 엔진으로 포커 핸드를 시맨틱 검색합니다.

## 개요

- **모듈 ID**: M4
- **담당자**: David (RAG Search Developer)
- **버전**: 1.0.0 (Week 3-4 완료)
- **배포 플랫폼**: Cloud Run
- **주요 기술**: Python 3.11, Vertex AI, Flask, BigQuery, Vector Search

## 아키텍처

```
User Query ("Tom Dwan 블러프")
    ↓
Embedding Generation (Vertex AI TextEmbedding-004)
    ↓
Vector Search (BigQuery - 768-dim cosine similarity)
    ↓
Metadata Join (hand_summary)
    ↓
Re-ranking (user feedback)
    ↓
Top 20 Results
```

## 주요 기능

### Week 3-4 구현 (100%)

✅ **완료된 기능**:
1. **Mock Data Development Mode**
   - JSON 파일 기반 mock 데이터 로딩
   - 단순 텍스트 매칭으로 검색 시뮬레이션
   - Mock 관련도 점수 생성 (0.6-0.9)

2. **Flask API 서버 (8개 엔드포인트)**
   - POST /v1/search - 자연어 검색
   - GET /v1/search/autocomplete - 자동 완성
   - POST /v1/search/feedback - 사용자 피드백
   - GET /v1/similar/{hand_id} - 유사 핸드 찾기
   - POST /v1/admin/reindex - 재인덱싱
   - GET /v1/stats - 검색 통계
   - GET /health - 헬스 체크

3. **Environment Switching**
   - POKER_ENV=development: Mock 데이터 사용
   - POKER_ENV=production: Real Vertex AI 사용

4. **테스트 커버리지 80%+**
   - 유닛 테스트: 모든 서비스 컴포넌트
   - API 테스트: 모든 엔드포인트
   - Mock/Real 모드 테스트

5. **Docker 배포 준비**
   - Dockerfile with gunicorn
   - Health check 구현
   - Cloud Run 호환

📋 **Week 5 예정 (Production Mode)**:
- Vertex AI 실제 임베딩 생성
- BigQuery Vector Search 연동
- Re-ranking 알고리즘
- Cloud Run 배포 및 검증

## API 엔드포인트

### 1. POST /v1/search

자연어 쿼리로 포커 핸드 검색

**요청**:
```json
{
  "query": "Tom Dwan 블러프",
  "limit": 20,
  "filters": {
    "players": ["Tom Dwan"],
    "event_name_contains": "WSOP",
    "year_range": [2008, 2024],
    "pot_size_min": 100000
  },
  "include_proxy": true
}
```

**응답** (200 OK):
```json
{
  "query_id": "search-20241117-001",
  "total_results": 156,
  "processing_time_ms": 245,
  "results": [
    {
      "hand_id": "HAND_000001",
      "relevance_score": 0.94,
      "summary": "Tom Dwan, J4o, river all-in bluff vs Phil Hellmuth",
      "tournament_id": "WSOP_2024_032",
      "event_name": "2024 WSOP Main Event",
      "timestamp": "2025-09-24T14:19:14Z",
      "players": ["Tom Dwan", "Phil Hellmuth"],
      "pot_size": 45685,
      "proxy_url": "https://storage.googleapis.com/gg-proxy/wsop2024_d3.mp4"
    }
  ]
}
```

### 2. GET /v1/search/autocomplete

검색어 자동 완성

**요청**:
```
GET /v1/search/autocomplete?q=Tom%20D&limit=10
```

**응답** (200 OK):
```json
{
  "query": "Tom D",
  "suggestions": [
    {
      "text": "Tom Dwan",
      "type": "player",
      "count": 1250
    },
    {
      "text": "Tom Dwan 블러프",
      "type": "popular",
      "count": 342
    }
  ]
}
```

### 3. POST /v1/search/feedback

검색 결과 피드백 제출

**요청**:
```json
{
  "query_id": "search-20241117-001",
  "hand_id": "HAND_000001",
  "feedback": "relevant"
}
```

**응답** (200 OK):
```json
{
  "status": "ok",
  "message": "Feedback recorded"
}
```

### 4. GET /v1/similar/{hand_id}

유사한 핸드 찾기

**요청**:
```
GET /v1/similar/HAND_000001?limit=10
```

**응답** (200 OK):
```json
{
  "hand_id": "HAND_000001",
  "similar_hands": [
    {
      "hand_id": "HAND_000042",
      "relevance_score": 0.88,
      "tournament_id": "WSOP_2024_010"
    }
  ]
}
```

### 5. POST /v1/admin/reindex

전체 재인덱싱 (관리자 전용)

**요청**:
```json
{
  "event_id": null,
  "force": true
}
```

**응답** (200 OK):
```json
{
  "reindex_job_id": "reindex-20241117-001",
  "status": "started",
  "estimated_duration_sec": 7200
}
```

### 6. GET /v1/stats

검색 통계 조회

**요청**:
```
GET /v1/stats?period=24h
```

**응답** (200 OK):
```json
{
  "period": "24h",
  "total_searches": 1250,
  "unique_users": 45,
  "avg_processing_time_ms": 280,
  "top_queries": [
    {"query": "Tom Dwan", "count": 125}
  ]
}
```

### 7. GET /health

헬스 체크

**응답** (200 OK):
```json
{
  "status": "healthy",
  "environment": "development",
  "dependencies": {
    "bigquery": "disabled",
    "vertex_ai": "disabled",
    "mock_data": "healthy"
  }
}
```

## 로컬 개발

### 요구사항

- Python 3.11+
- pip
- (Optional) Docker for containerized development

### 설치

```bash
cd modules/m4-rag-search

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 환경 변수

개발 모드 (기본):
```bash
export POKER_ENV=development
export PORT=8004
```

프로덕션 모드:
```bash
export POKER_ENV=production
export GCP_PROJECT=gg-poker
export GCP_REGION=us-central1
```

### 실행

```bash
# Development mode (mock data)
python -m app.api

# Or with Flask
export FLASK_APP=app.api
flask run --port 8004
```

서버 시작 후:
- API: http://localhost:8004
- Health: http://localhost:8004/health

### 테스트

```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py -v

# Run with debugging
pytest tests/test_api.py -v -s
```

**목표 커버리지**: 80%+

## Docker 배포

### 빌드

```bash
# Build image
docker build -t m4-rag-search:latest .

# Build for specific environment
docker build -t m4-rag-search:prod --build-arg POKER_ENV=production .
```

### 실행

```bash
# Development mode
docker run -p 8004:8004 \
  -e POKER_ENV=development \
  m4-rag-search:latest

# Production mode
docker run -p 8004:8004 \
  -e POKER_ENV=production \
  -e GCP_PROJECT=gg-poker \
  m4-rag-search:latest
```

### Cloud Run 배포

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/gg-poker/m4-rag-search

# Deploy to Cloud Run
gcloud run deploy m4-rag-search \
  --image gcr.io/gg-poker/m4-rag-search \
  --platform managed \
  --region us-central1 \
  --set-env-vars POKER_ENV=production,GCP_PROJECT=gg-poker \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

## 프로젝트 구조

```
m4-rag-search/
├── app/
│   ├── __init__.py
│   ├── api.py                 # Flask API server
│   ├── config.py              # Configuration management
│   ├── bigquery_client.py     # BigQuery operations
│   ├── embedding_service.py   # Vertex AI embeddings
│   ├── vector_search.py       # Search logic
│   └── autocomplete.py        # Autocomplete service
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── test_api.py            # API endpoint tests
│   ├── test_embedding_service.py
│   ├── test_vector_search.py
│   └── test_bigquery_client.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## 개발 워크플로우

### Week 3-4: Mock Development (완료 ✅)

1. ✅ Mock 데이터 로딩 (JSON 파일)
2. ✅ Flask API 서버 (8개 엔드포인트)
3. ✅ 단순 텍스트 매칭 검색
4. ✅ 유닛 테스트 (80%+ 커버리지)
5. ✅ Docker 컨테이너화

### Week 5: Production Mode (예정)

1. [ ] Vertex AI 임베딩 생성
2. [ ] BigQuery Vector Search
3. [ ] Re-ranking 알고리즘
4. [ ] Cloud Run 배포
5. [ ] 통합 테스트 (E2E)

## Mock vs Production

### Development Mode (POKER_ENV=development)

- ✅ Mock 데이터 로딩 (JSON 파일)
- ✅ 단순 텍스트 매칭
- ✅ Mock 관련도 점수 (0.6-0.9)
- ✅ No Vertex AI API 호출
- ✅ No BigQuery 비용

### Production Mode (POKER_ENV=production)

- 🔄 Real BigQuery 조회
- 🔄 Vertex AI 임베딩 생성
- 🔄 Vector 유사도 검색
- 🔄 사용자 피드백 기반 Re-ranking

## 의존성

### Input (M1 Data Ingestion)
- BigQuery: `prod.hand_summary`
- 핸드 메타데이터 (hand_id, tournament_id, players, etc.)

### Output
- BigQuery: `prod.hand_embeddings`
- BigQuery: `prod.search_logs`
- BigQuery: `prod.search_feedback`

### External Services
- Vertex AI TextEmbedding-004 (768-dim vectors)
- BigQuery Vector Search

## 성능 목표

- **검색 응답 시간**: <500ms (P95)
- **임베딩 생성**: <200ms per query
- **Vector 검색**: <300ms for 100K hands
- **동시 사용자**: 100+ concurrent users

## 보안

- JWT 토큰 인증 (프로덕션)
- API Rate Limiting
- Input 검증 및 sanitization
- No secrets in code (environment variables)

## 모니터링

- Cloud Logging: 모든 API 요청
- Cloud Monitoring: Latency, Error rate
- BigQuery: 검색 로그 분석
- User feedback tracking

## 트러블슈팅

### Mock 데이터가 로드되지 않음

```bash
# Check mock data paths
ls -la ../../mock_data/bigquery/hand_summary_mock.json
ls -la ../../mock_data/embeddings/hand_embeddings_mock.json

# Verify file contents
head ../../mock_data/bigquery/hand_summary_mock.json
```

### 테스트 실패

```bash
# Run tests with verbose output
pytest tests/ -v -s

# Check coverage
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Docker 빌드 실패

```bash
# Check Docker logs
docker logs <container_id>

# Rebuild without cache
docker build --no-cache -t m4-rag-search:latest .
```

## 기여

1. Feature branch 생성: `git checkout -b feature/new-feature`
2. 변경 사항 커밋: `git commit -m "feat: Add new feature"`
3. 테스트 실행: `pytest tests/ -v --cov=app`
4. Push to branch: `git push origin feature/new-feature`
5. Pull Request 생성

## 라이센스

Proprietary - GG Production

## 연락처

- **담당자**: David (M4 RAG Search Developer)
- **이메일**: david@ggproduction.net
- **팀**: POKER-BRAIN Development Team

---

**Last Updated**: 2025-01-17 (Week 3-4 완료)
**Status**: ✅ Development Mode Complete (80%+ coverage)
**Next**: Week 5 - Production Mode Implementation
