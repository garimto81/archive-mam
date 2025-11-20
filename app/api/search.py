"""
검색 API 엔드포인트
v4.0.0 - Vertex AI Vector Search
"""

import time
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, List

from app.models.schemas import SearchResponse
from app.services.search import SearchService


router = APIRouter()
search_service = SearchService()


@router.get("", response_model=SearchResponse)
async def search_hands(
    q: str = Query(..., min_length=1, max_length=500, description="검색 쿼리"),
    limit: int = Query(20, ge=1, le=100, description="결과 개수"),
    min_pot_bb: Optional[float] = Query(None, ge=0, description="최소 팟 크기 (BB)"),
    tournament_id: Optional[str] = Query(None, description="토너먼트 ID"),
    tags: Optional[str] = Query(None, description="태그 (쉼표 구분)")
):
    """포커 핸드 자연어 검색

    Args:
        q: 검색 쿼리 (영문, 자연어)
        limit: 결과 개수 (1-100)
        min_pot_bb: 최소 팟 크기 필터 (선택)
        tournament_id: 토너먼트 ID 필터 (선택)
        tags: 태그 필터, 쉼표 구분 (예: "BLUFF,HERO_CALL")

    Returns:
        SearchResponse (results, total, query, query_time_ms)

    Raises:
        400: 잘못된 쿼리
        500: 서버 에러

    Example:
        GET /api/search?q=junglemann+crazy+river+call&limit=20
        GET /api/search?q=high+stakes+bluff&min_pot_bb=100&tags=BLUFF
    """
    try:
        start_time = time.time()

        # 태그 파싱 (쉼표 구분)
        tag_list = None
        if tags:
            tag_list = [tag.strip().upper() for tag in tags.split(",")]

        # 검색 실행
        results = search_service.search(
            query=q,
            limit=limit,
            min_pot_bb=min_pot_bb,
            tournament_id=tournament_id,
            tags=tag_list
        )

        # 응답 생성
        query_time_ms = int((time.time() - start_time) * 1000)

        return SearchResponse(
            results=results,
            total=len(results),
            query=q,
            query_time_ms=query_time_ms
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error in search: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
