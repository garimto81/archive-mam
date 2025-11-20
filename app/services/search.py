"""
Vertex AI Vector Search 서비스
v4.0.0 - text-embedding-004
"""

from typing import List, Optional
from google.cloud import aiplatform
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

from app.config import settings
from app.models.schemas import HandMetadata, SearchResult
from app.services.bigquery import BigQueryService


class SearchService:
    """Vertex AI Vector Search 서비스"""

    def __init__(self):
        # Vertex AI 초기화
        vertexai.init(
            project=settings.GCP_PROJECT,
            location=settings.GCP_REGION
        )

        # 엔드포인트 로드
        if not settings.VERTEX_AI_INDEX_ENDPOINT:
            raise ValueError(
                "VERTEX_AI_INDEX_ENDPOINT 환경변수가 설정되지 않았습니다.\n"
                "scripts/vertex-ai/deploy_index.py를 실행하세요."
            )

        self.endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=settings.VERTEX_AI_INDEX_ENDPOINT
        )

        # 임베딩 모델 (최신)
        self.embedding_model = TextEmbeddingModel.from_pretrained(
            "text-embedding-004"
        )

        # BigQuery 서비스
        self.bq_service = BigQueryService()

    def generate_query_embedding(self, query: str) -> List[float]:
        """쿼리 텍스트 → 임베딩 벡터 변환

        Args:
            query: 검색 쿼리 (영문)

        Returns:
            임베딩 벡터 (768차원)
        """
        # TextEmbeddingInput 사용 (최신 API)
        inputs = [TextEmbeddingInput(text=query, task_type="RETRIEVAL_QUERY")]
        embeddings = self.embedding_model.get_embeddings(inputs)
        return embeddings[0].values

    def search(
        self,
        query: str,
        limit: int = 20,
        min_pot_bb: Optional[float] = None,
        tournament_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """하이브리드 검색 (Vector + Metadata Filter)

        Args:
            query: 검색 쿼리
            limit: 결과 개수
            min_pot_bb: 최소 팟 크기 필터
            tournament_id: 토너먼트 ID 필터
            tags: 태그 필터

        Returns:
            검색 결과 (SearchResult 리스트)
        """
        # 1. 쿼리 임베딩 생성
        query_embedding = self.generate_query_embedding(query)

        # 2. Vector Search 실행
        vector_results = self.endpoint.find_neighbors(
            deployed_index_id=settings.VERTEX_AI_DEPLOYED_INDEX_ID,
            queries=[query_embedding],
            num_neighbors=limit * 3  # 필터링 고려하여 더 많이 조회
        )

        # 3. hand_id 추출
        hand_ids = []
        distance_map = {}  # hand_id → distance(score)

        for neighbor in vector_results[0]:
            hand_id = neighbor.id
            distance = neighbor.distance  # DOT_PRODUCT (높을수록 유사)

            hand_ids.append(hand_id)
            distance_map[hand_id] = distance

        if not hand_ids:
            return []

        # 4. BigQuery에서 메타데이터 조회
        hands = self.bq_service.get_hands_by_ids(hand_ids)

        # 5. 메타데이터 필터링
        filtered_hands = []
        for hand in hands:
            # min_pot_bb 필터
            if min_pot_bb is not None and hand.pot_bb < min_pot_bb:
                continue

            # tournament_id 필터
            if tournament_id is not None and hand.tournament_id != tournament_id:
                continue

            # tags 필터
            if tags is not None and hand.tags:
                if not any(tag in hand.tags for tag in tags):
                    continue

            filtered_hands.append(hand)

        # 6. SearchResult 생성 (score = distance)
        results = []
        for rank, hand in enumerate(filtered_hands[:limit], start=1):
            score = distance_map.get(hand.hand_id, 0.0)

            # DOT_PRODUCT distance → 0-1 score 변환
            # (이미 L2 normalized vectors이므로 cosine similarity와 동일)
            normalized_score = min(max(score, 0.0), 1.0)

            results.append(
                SearchResult(
                    hand=hand,
                    score=normalized_score,
                    rank=rank
                )
            )

        return results
