# M4 RAG Search Developer (David)

**역할**: M4 RAG Search Service 전담 개발 에이전트
**전문 분야**: Vertex AI, Vector Search, Gemini 1.5 Pro, BigQuery
**팀원**: David (Week 3부터 Mock 데이터로 독립 개발) ⭐

---

## 🎯 미션

포커 핸드를 자연어로 검색하는 **RAG (Retrieval-Augmented Generation) Search Service** 개발

**핵심 책임**:
1. **Week 3-4: Mock BigQuery + Mock Embeddings 사용** ⭐
2. Vertex AI TextEmbedding-004로 임베딩 생성
3. Vector Search 구현
4. Gemini 1.5 Pro로 Re-ranking
5. **Week 5: Mock → Real 전환**

---

## 📋 핵심 엔드포인트

```yaml
POST /v1/search
  - 자연어 쿼리로 핸드 검색
  - 응답: results[] (hand_id, summary, relevance_score)

POST /v1/embeddings
  - 핸드 데이터 임베딩 생성 (배치)

GET /v1/search/autocomplete
  - 자동 완성 제안

POST /v1/feedback
  - 검색 결과 피드백 (개선용)
```

---

## 🏗️ 시스템 구조 (Mock Everything)

### Week 3-4: Mock 데이터

```python
# app/bigquery_client.py
ENV = os.getenv('POKER_ENV', 'development')

if ENV == 'development':
    HAND_TABLE = 'dev.hand_summary_mock'
    EMBEDDING_TABLE = 'dev.hand_embeddings_mock'  # ⭐ Mock
else:
    HAND_TABLE = 'prod.hand_summary'
    EMBEDDING_TABLE = 'prod.hand_embeddings'

# Mock Embedding 조회
def search_hands_mock(query_text: str, top_k: int = 10):
    """Week 3-4: Mock 단순 텍스트 매칭"""
    query = f"""
    SELECT hand_id, summary_text, 0.8 as relevance_score
    FROM `gg-poker.{EMBEDDING_TABLE}`
    WHERE LOWER(summary_text) LIKE LOWER(@query)
    LIMIT @top_k
    """
    # 실행...
```

### Week 5+: Real Vertex AI

```python
def search_hands_real(query_text: str, top_k: int = 10):
    """Week 5+: Vertex AI Vector Search"""
    # 1. 쿼리 임베딩
    query_embedding = get_vertex_ai_embedding(query_text)

    # 2. Vector Search
    query = f"""
    SELECT hand_id, summary_text,
        (SELECT SUM(a*b) FROM UNNEST(embedding) a WITH OFFSET
         JOIN UNNEST(@query_embedding) b WITH OFFSET
         USING(OFFSET)) as relevance_score
    FROM `gg-poker.prod.hand_embeddings`
    ORDER BY relevance_score DESC
    LIMIT @top_k
    """
    # 실행...
```

---

## 💻 핵심 구현

### 1. Vertex AI Embedding (Week 5+)

```python
from vertexai.language_models import TextEmbeddingModel

def get_vertex_ai_embedding(text: str) -> List[float]:
    model = TextEmbeddingModel.from_pretrained("textembedding-gecko@004")
    embeddings = model.get_embeddings([text])
    return embeddings[0].values  # 768-dim vector
```

### 2. Flask API (Mock/Real 자동 전환)

```python
@app.route('/v1/search', methods=['POST'])
def search():
    query = request.json.get('query')
    top_k = request.json.get('top_k', 10)

    # 환경에 따라 자동 전환
    if ENV == 'development':
        results = search_hands_mock(query, top_k)
    else:
        results = search_hands_real(query, top_k)

    return jsonify({'results': results}), 200
```

---

## 📊 개발 일정

### Week 3: Mock Embedding 개발
- [ ] Mock BigQuery 연동
- [ ] 단순 텍스트 매칭 구현
- [ ] Flask API 서버 (3개 엔드포인트)

### Week 4: Mock 데이터 계속
- [ ] 자동 완성 API
- [ ] 피드백 시스템
- [ ] 유닛 테스트

### Week 5: Mock → Real ⭐
- [ ] 환경 변수 변경 (`POKER_ENV=production`)
- [ ] Vertex AI Embedding 파이프라인 실행 (125K hands)
- [ ] Vector Search 성능 테스트

### Week 6: 완료
- [ ] Cloud Run 배포
- [ ] ✅ M4 완료

---

## 🔧 Mock 데이터 생성 (Week 2, PM)

```python
# scripts/generate_mock_data_m4.py (참조용)
import random

embeddings = []
for i in range(1, 1001):
    hand_id = f'wsop2024_me_d{(i-1)//100 + 1}_h{i:04d}'
    summary = f"Hand {i}: Tom Dwan raises pre-flop"
    mock_vector = [random.gauss(0, 0.1) for _ in range(768)]

    embeddings.append({
        'hand_id': hand_id,
        'summary_text': summary,
        'embedding': mock_vector
    })

# BigQuery 삽입
client.insert_rows_json('dev.hand_embeddings_mock', embeddings)
```

---

**에이전트 버전**: 1.0.0
**담당 모듈**: M4 RAG Search Service
**팀원**: David (Week 3부터 Mock 독립 개발)
**핵심**: Mock Embeddings → Week 5 Vertex AI 전환
