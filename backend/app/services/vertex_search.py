"""
Vertex AI Vector Search 서비스
Hybrid Search: BM25 + Vector (RRF)
"""

from google.cloud import aiplatform
from app.config import settings
import structlog
import json
import asyncio
from typing import List, Dict

logger = structlog.get_logger()


class VertexSearchService:
    """Vertex AI Vector Search 서비스"""

    def __init__(self):
        """Vertex AI 클라이언트 초기화"""
        if settings.enable_mock_mode:
            logger.info("vertex_search_mock_mode_enabled")
            self.mock_mode = True
        else:
            self.mock_mode = False
            aiplatform.init(
                project=settings.gcp_project,
                location=settings.gcp_location,
            )
            logger.info(
                "vertex_search_initialized",
                project=settings.gcp_project,
                index_id=settings.vertex_index_id,
                search_type=settings.search_type,
            )

    async def search(
        self, query: str, top_k: int = 5, similarity_threshold: float = 0.7
    ) -> list[dict]:
        """
        포커 핸드 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 개수
            similarity_threshold: 유사도 임계값

        Returns:
            검색 결과 리스트 (dict)
        """
        if self.mock_mode:
            return await self._mock_search(query, top_k)

        try:
            # Step 1: 쿼리 임베딩 생성 (TextEmbedding-004)
            query_embedding = await self._generate_embedding(query)

            # Step 2: Vertex AI Vector Search 호출
            results = await self._vector_search(query_embedding, top_k)

            # Step 3: 유사도 필터링
            filtered_results = [
                result for result in results if result.get("distance", 0) >= similarity_threshold
            ]

            logger.info(
                "vertex_search_success",
                query=query[:50],
                total_results=len(filtered_results),
                top_k=top_k,
            )

            return filtered_results[:top_k]

        except Exception as e:
            logger.error("vertex_search_error", error=str(e), query=query[:50])
            raise

    async def _generate_embedding(self, text: str) -> list[float]:
        """
        TextEmbedding-004로 텍스트 임베딩 생성

        Args:
            text: 임베딩할 텍스트 (검색 쿼리)

        Returns:
            768차원 임베딩 벡터
        """
        try:
            import vertexai
            from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

            # Vertex AI 초기화
            vertexai.init(
                project=settings.gcp_project,
                location=settings.gcp_location
            )

            # TextEmbedding-004 모델 로드
            model = TextEmbeddingModel.from_pretrained(settings.vertex_embedding_model)

            # 임베딩 생성 (RETRIEVAL_QUERY 타입 사용)
            input_obj = TextEmbeddingInput(text=text, task_type="RETRIEVAL_QUERY")
            embeddings = model.get_embeddings([input_obj])

            # 임베딩 벡터 추출
            embedding_vector = embeddings[0].values

            logger.info(
                "embedding_generated",
                text_length=len(text),
                vector_dimension=len(embedding_vector)
            )

            return embedding_vector

        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e), text=text[:100])
            # Fallback: 제로 벡터 반환 (검색은 실패하지만 서비스는 유지)
            return [0.0] * settings.vertex_embedding_dimension

    async def _vector_search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        """
        Vertex AI Vector Search 호출

        Args:
            query_embedding: 768차원 쿼리 임베딩 벡터
            top_k: 반환할 결과 개수

        Returns:
            검색 결과 리스트 (hand_id, distance 포함)
        """
        try:
            # Vertex AI Index Endpoint 로드
            endpoint = aiplatform.MatchingEngineIndexEndpoint(
                index_endpoint_name=settings.vertex_ai_index_endpoint
            )

            # Vector Search 수행
            response = endpoint.find_neighbors(
                deployed_index_id=settings.vertex_ai_deployed_index_id,
                queries=[query_embedding],
                num_neighbors=top_k * 2  # 필터링을 위해 더 많이 가져옴
            )

            # 결과 파싱
            results = []
            if response and len(response) > 0:
                for neighbor in response[0][:top_k]:
                    results.append({
                        "hand_id": neighbor.id,
                        "distance": neighbor.distance
                    })

            logger.info(
                "vector_search_complete",
                results_count=len(results),
                top_k=top_k
            )

            return results

        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            # Fallback: 빈 결과 반환
            return []

    async def _mock_search(self, query: str, top_k: int) -> list[dict]:
        """Mock 검색 (테스트용)"""
        logger.info("using_mock_search", query=query[:50])

        # mock_data/synthetic_ati/ 에서 샘플 데이터 로드
        try:
            # 첫 번째 핸드 파일을 샘플로 사용
            sample_file = f"{settings.test_data_path}/hand_001.json"
            with open(sample_file, "r", encoding="utf-8") as f:
                sample_hand = json.load(f)

            # 샘플 핸드를 top_k개만큼 반환
            mock_results = []
            for i in range(min(top_k, 5)):  # 최대 5개
                mock_results.append({
                    "hand_id": f"hand_{i+1:03d}",
                    "hero_name": sample_hand.get("hero", {}).get("name", "Unknown"),
                    "villain_name": None,
                    "description": sample_hand.get("description", "Mock hand description"),
                    "pot_bb": sample_hand.get("pot_size_bb", 100.0),
                    "street": sample_hand.get("street", "River"),
                    "action": sample_hand.get("action", "Call"),
                    "tournament": sample_hand.get("tournament", "WSOP Main Event"),
                    "tags": sample_hand.get("tags", []),
                    "video_url": None,
                    "timestamp": None,
                    "distance": 0.9 - (i * 0.1),  # 0.9, 0.8, 0.7, ...
                })

            return mock_results

        except Exception as e:
            logger.error("mock_search_error", error=str(e))
            # 하드코딩 샘플 반환
            return [
                {
                    "hand_id": "hand_001",
                    "hero_name": "Phil Ivey",
                    "villain_name": "Tom Dwan",
                    "description": "Ivey makes a huge bluff on the river",
                    "pot_bb": 150.0,
                    "street": "River",
                    "action": "Bluff",
                    "tournament": "High Stakes Poker",
                    "tags": ["bluff", "high-stakes"],
                    "video_url": None,
                    "timestamp": None,
                    "distance": 0.95,
                }
            ]

    async def semantic_autocomplete(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[str]:
        """
        Vertex AI 의미론적 검색으로 자동완성 제안 반환.

        Args:
            query: 검색 쿼리 (최소 2자)
            limit: 최대 결과 개수 (기본 5)
            similarity_threshold: 유사도 임계값 (기본 0.7)

        Returns:
            자동완성 제안 리스트 (유사도 순 정렬)

        Example:
            >>> service = VertexSearchService()
            >>> await service.semantic_autocomplete("Junglman", limit=3)
            ["Junglemann", "Daniel Dvoress", "Mikki Mase"]
        """
        try:
            # 1. 쿼리 임베딩 생성
            query_embedding = await self._generate_embedding(query)

            # 2. Vertex AI Vector Search (더 많이 가져와서 키워드 추출 후 필터링)
            similar_hands = await self._vector_search(
                query_embedding,
                top_k=limit * 2  # 키워드 추출 후 필터링을 위해 더 많이 가져옴
            )

            # 3. 키워드 추출 (선수명, 태그)
            keywords = self._extract_keywords(similar_hands, similarity_threshold)

            # 4. 중복 제거 및 정렬 (순서 유지하며 중복 제거)
            unique_keywords = list(dict.fromkeys(keywords))

            logger.info(
                "semantic_autocomplete_success",
                query=query[:50],
                total_keywords=len(unique_keywords),
                returned=min(limit, len(unique_keywords))
            )

            return unique_keywords[:limit]

        except Exception as e:
            logger.error(
                "semantic_autocomplete_error",
                error=str(e),
                query=query[:50]
            )
            return []  # Graceful degradation

    def _extract_keywords(
        self,
        hands: List[Dict],
        threshold: float
    ) -> List[str]:
        """
        핸드에서 키워드 추출 (선수명, 태그)

        Args:
            hands: 검색된 핸드 목록
            threshold: 유사도 임계값 (distance >= threshold인 것만)

        Returns:
            추출된 키워드 리스트 (유사도 순)
        """
        keywords = []

        for hand in hands:
            # 유사도 임계값 체크
            distance = hand.get("distance", 0.0)
            if distance < threshold:
                continue

            # Hero 이름 추출
            hero_name = hand.get("hero_name")
            if hero_name:
                keywords.append(hero_name)

            # Villain 이름 추출
            villain_name = hand.get("villain_name")
            if villain_name:
                keywords.append(villain_name)

            # 태그 추출
            tags = hand.get("tags", [])
            for tag in tags:
                if tag:  # 빈 태그 제외
                    keywords.append(tag)

        return keywords
