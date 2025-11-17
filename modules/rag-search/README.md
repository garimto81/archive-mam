# M4: RAG Search Service

**담당**: ML Engineer / Backend Engineer (David)
**버전**: 1.0.0
**배포**: Cloud Run

---

## 개요

Vertex AI 기반 자연어 검색 엔진입니다.

### 주요 기능

- ✅ Semantic Search (의미 기반 검색)
- ✅ TextEmbedding-004 임베딩
- ✅ Vector Search (100 neighbors)
- ✅ 사용자 피드백 Re-ranking
- ✅ 즐겨찾기 관리

---

## 검색 파이프라인

```
User Query ("Tom Dwan 블러프")
    ↓
TextEmbedding-004 (512-dim vector)
    ↓
Vertex AI Vector Search (100 neighbors)
    ↓
BigQuery Filter (players, year, pot_size)
    ↓
Re-ranking (feedback 기반)
    ↓
Top 20 Results (relevance_score 순)
```

**예상 처리 시간**: ~200-500ms

---

## API 스펙

**OpenAPI 3.0**: `openapi.yaml`

### 주요 엔드포인트

```bash
# 검색
POST /v1/search

# 자동 완성
GET /v1/search/autocomplete?q=Tom+D

# 피드백
POST /v1/search/feedback

# 즐겨찾기
GET /v1/favorites
```

---

## 로컬 개발

### Vertex AI 설정

```bash
# Vertex AI API 활성화
gcloud services enable aiplatform.googleapis.com

# Vector Search Index 생성
gcloud ai indexes create \
  --display-name=hand-embeddings \
  --metadata-schema-uri=gs://google-cloud-aiplatform/schema/matchingengine/metadata/nearest_neighbor_search_1.0.0.yaml \
  --dimensions=512 \
  --region=us-central1
```

### 환경 설정

```bash
pip install -r requirements.txt
```

**requirements.txt**:
```txt
google-cloud-aiplatform==1.38.1
google-cloud-bigquery==3.13.0
fastapi==0.104.1
uvicorn==0.24.0
pytest==7.4.3
```

---

## 핵심 로직

```python
# src/rag_engine.py
from google.cloud import aiplatform

def search_hands(query: str, filters: dict) -> list:
    # 1. Embedding
    model = aiplatform.TextEmbeddingModel.from_pretrained("textembedding-004")
    query_embedding = model.get_embeddings([query])[0].values

    # 2. Vector Search
    index = aiplatform.MatchingEngineIndex(index_name="hand-embeddings")
    neighbors = index.find_neighbors(
        queries=[query_embedding],
        num_neighbors=100
    )

    # 3. BigQuery Filter
    hand_ids = [n.id for n in neighbors[0]]
    results = bigquery_client.query(f"""
        SELECT * FROM prod.hand_summary
        WHERE hand_id IN UNNEST(@hand_ids)
          AND 'Tom Dwan' IN UNNEST(players)
        LIMIT 20
    """, job_config=QueryJobConfig(
        query_parameters=[ArrayQueryParameter("hand_ids", "STRING", hand_ids)]
    )).result()

    return list(results)
```

---

## 임베딩 생성 (초기 설정)

```python
# scripts/generate_embeddings.py
from google.cloud import aiplatform, bigquery

# BigQuery에서 hand_summary 조회
hands = bigquery_client.query("SELECT hand_id, searchable_summary_text FROM prod.hand_summary").result()

# TextEmbedding-004로 임베딩 생성
model = aiplatform.TextEmbeddingModel.from_pretrained("textembedding-004")

for hand in hands:
    embedding = model.get_embeddings([hand.searchable_summary_text])[0].values

    # BigQuery 업데이트
    bigquery_client.query(f"""
        UPDATE prod.hand_summary
        SET embedding = {embedding}
        WHERE hand_id = '{hand.hand_id}'
    """)
```

**예상 시간**: 100K hands → ~2시간

---

## 배포

```bash
gcloud run deploy rag-search-service \
  --source . \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2
```

---

**담당자**: aiden.kim@ggproduction.net
**최종 업데이트**: 2025-11-17
