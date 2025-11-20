"""
핸드 상세 조회 API
v4.0.0
"""

from fastapi import APIRouter, HTTPException, status
from app.models.schemas import HandMetadata
from app.services.bigquery import BigQueryService

router = APIRouter()
bq_service = BigQueryService()


@router.get("/{hand_id}", response_model=HandMetadata)
async def get_hand(hand_id: str):
    """핸드 상세 정보 조회

    Args:
        hand_id: 핸드 고유 ID

    Returns:
        HandMetadata

    Raises:
        404: 핸드를 찾을 수 없음
        500: 서버 에러
    """
    try:
        hand = bq_service.get_hand_by_id(hand_id)

        if not hand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hand not found: {hand_id}"
            )

        return hand

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_hand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
