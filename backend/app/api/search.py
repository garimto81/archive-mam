"""
검색 API 엔드포인트
GET /api/search?query={query}&top_k={top_k}
"""

from fastapi import APIRouter, Query, HTTPException
from app.models import SearchRequest, SearchResponse, HandResult, ErrorResponse
from app.services.vertex_search import VertexSearchService
from app.config import settings
import structlog
import time

router = APIRouter()
logger = structlog.get_logger()

# Vertex Search 서비스 초기화 (싱글톤)
vertex_search = VertexSearchService()


@router.get("/search", response_model=SearchResponse, responses={500: {"model": ErrorResponse}})
async def search_hands(
    query: str = Query(..., description="검색 쿼리", min_length=1, max_length=500),
    top_k: int = Query(5, description="반환할 결과 개수", ge=1, le=20),
) -> SearchResponse:
    """
    포커 핸드 검색 API

    **기능**:
    - Vertex AI Vector Search (Hybrid: BM25 + Vector)
    - TextEmbedding-004로 쿼리 임베딩 생성
    - RRF (Reciprocal Rank Fusion)로 결과 결합

    **Example**:
    ```
    GET /api/search?query=Phil Ivey bluff&top_k=5
    ```
    """
    start_time = time.time()

    try:
        logger.info("search_request", query=query, top_k=top_k)

        # Vertex AI Vector Search 호출
        search_results = await vertex_search.search(
            query=query,
            top_k=top_k,
            similarity_threshold=settings.search_similarity_threshold,
        )

        # 응답 생성
        results = [
            HandResult(
                hand_id=result["hand_id"],
                hero_name=result["hero_name"],
                villain_name=result.get("villain_name"),
                description=result["description"],
                pot_bb=result["pot_bb"],
                street=result["street"],
                action=result["action"],
                tournament=result.get("tournament"),
                tags=result.get("tags", []),
                video_url=result.get("video_url"),
                timestamp=result.get("timestamp"),
                distance=result.get("distance"),
            )
            for result in search_results
        ]

        search_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "search_success",
            query=query,
            total_results=len(results),
            search_time_ms=search_time_ms,
        )

        return SearchResponse(
            query=query,
            total_results=len(results),
            results=results,
            search_time_ms=search_time_ms,
        )

    except Exception as e:
        logger.error("search_error", error=str(e), query=query)
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")
