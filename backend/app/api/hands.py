"""
핸드 상세 정보 API 엔드포인트
GET /api/hands/{hand_id}
"""

from fastapi import APIRouter, Path, HTTPException
from app.models import HandDetailResponse, ErrorResponse
from app.services.bigquery import BigQueryService
from app.config import settings
import structlog
import time

router = APIRouter()
logger = structlog.get_logger()

# BigQuery 서비스 초기화
bigquery_service = BigQueryService()


@router.get("/hands/{hand_id}", response_model=HandDetailResponse, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_hand_detail(
    hand_id: str = Path(..., description="핸드 ID", min_length=1)
) -> HandDetailResponse:
    """
    핸드 상세 정보 조회 API

    **기능**:
    - BigQuery에서 hand_id로 핸드 상세 정보 조회
    - 비디오 메타데이터 포함 (video_url, timestamp)

    **Example**:
    ```
    GET /api/hands/hand_001
    ```
    """
    start_time = time.time()

    try:
        logger.info("get_hand_detail_request", hand_id=hand_id)

        # BigQuery에서 핸드 조회
        hand = await bigquery_service.get_hand_by_id(hand_id)

        if not hand:
            raise HTTPException(status_code=404, detail=f"핸드 ID {hand_id}를 찾을 수 없습니다.")

        query_time_ms = (time.time() - start_time) * 1000

        logger.info("get_hand_detail_success", hand_id=hand_id, query_time_ms=query_time_ms)

        return HandDetailResponse(
            hand=hand,
            query_time_ms=query_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_hand_detail_error", error=str(e), hand_id=hand_id)
        raise HTTPException(status_code=500, detail=f"핸드 조회 중 오류 발생: {str(e)}")
