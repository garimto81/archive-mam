"""
비디오 URL 생성 API
v4.0.0
"""

from fastapi import APIRouter, HTTPException, status
from app.models.schemas import VideoURLResponse
from app.services.bigquery import BigQueryService
from app.services.storage import StorageService
from app.config import settings

router = APIRouter()
bq_service = BigQueryService()
storage_service = StorageService()


@router.get("/{hand_id}/url", response_model=VideoURLResponse)
async def get_video_url(hand_id: str):
    """핸드 비디오 Signed URL 생성

    Args:
        hand_id: 핸드 고유 ID

    Returns:
        VideoURLResponse (signed_url, expires_in)

    Raises:
        404: 핸드를 찾을 수 없음
        500: 서버 에러
    """
    try:
        # 1. BigQuery에서 핸드 조회
        hand = bq_service.get_hand_by_id(hand_id)

        if not hand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hand not found: {hand_id}"
            )

        # 2. GCS Signed URL 생성
        signed_url = storage_service.get_video_signed_url(
            hand_id,
            hand.video_url
        )

        return VideoURLResponse(
            video_url=signed_url,
            expires_in=settings.SIGNED_URL_EXPIRATION,
            hand_id=hand_id
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_video_url: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
