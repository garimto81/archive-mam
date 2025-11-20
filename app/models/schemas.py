"""
Pydantic 모델 정의
v4.0.0
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class HandMetadata(BaseModel):
    """포커 핸드 메타데이터"""

    hand_id: str = Field(..., description="고유 핸드 ID")
    tournament_id: Optional[str] = Field(None, description="토너먼트 ID")
    hand_number: Optional[int] = Field(None, description="핸드 번호")

    # 시간 정보
    timestamp: datetime = Field(..., description="핸드 발생 시각")
    duration_seconds: Optional[int] = Field(None, description="핸드 진행 시간 (초)")

    # 플레이어
    hero_name: str = Field(..., description="주인공 플레이어")
    villain_name: Optional[str] = Field(None, description="상대 플레이어")
    hero_position: Optional[str] = Field(None, description="주인공 포지션")
    villain_position: Optional[str] = Field(None, description="상대 포지션")
    hero_stack_bb: Optional[float] = Field(None, description="주인공 스택 (BB)")
    villain_stack_bb: Optional[float] = Field(None, description="상대 스택 (BB)")

    # 핸드 상세
    street: Optional[str] = Field(None, description="스트리트 (PREFLOP/FLOP/TURN/RIVER)")
    pot_bb: float = Field(..., description="팟 사이즈 (BB)")
    action_sequence: Optional[List[str]] = Field(None, description="액션 시퀀스")
    hero_action: Optional[str] = Field(None, description="주인공 액션")
    result: Optional[str] = Field(None, description="결과 (WIN/LOSE/SPLIT)")

    # 분류
    tags: Optional[List[str]] = Field(None, description="태그")
    hand_type: Optional[str] = Field(None, description="핸드 타입")

    # 설명
    description: str = Field(..., description="핸드 설명 (영문)")

    # 비디오
    video_url: str = Field(..., description="GCS 비디오 경로")
    video_start_time: Optional[float] = Field(None, description="비디오 시작 시각 (초)")
    video_end_time: Optional[float] = Field(None, description="비디오 종료 시각 (초)")
    thumbnail_url: Optional[str] = Field(None, description="썸네일 URL")

    # 메타데이터
    created_at: Optional[datetime] = Field(None, description="생성 시각")
    gcs_source_path: Optional[str] = Field(None, description="GCS 원본 경로")

    class Config:
        json_schema_extra = {
            "example": {
                "hand_id": "wsop_2024_hand_0001",
                "tournament_id": "wsop_2024_main",
                "hand_number": 421,
                "timestamp": "2024-07-15T14:32:15Z",
                "hero_name": "Phil Ivey",
                "villain_name": "Daniel Negreanu",
                "pot_bb": 145.5,
                "description": "Phil Ivey makes a hero call on the river with ace-high",
                "video_url": "gs://poker-videos-prod/wsop_2024/day3.mp4",
                "tags": ["HERO_CALL", "RIVER_DECISION"]
            }
        }


class SearchRequest(BaseModel):
    """검색 요청"""

    query: str = Field(..., min_length=1, max_length=500, description="검색 쿼리")
    limit: int = Field(20, ge=1, le=100, description="결과 수 제한")
    min_pot_bb: Optional[float] = Field(None, ge=0, description="최소 팟 사이즈 (BB)")
    tournament_id: Optional[str] = Field(None, description="토너먼트 ID 필터")
    tags: Optional[List[str]] = Field(None, description="태그 필터")


class SearchResult(BaseModel):
    """검색 결과 아이템"""

    hand: HandMetadata
    score: float = Field(..., ge=0, le=1, description="유사도 점수")
    rank: int = Field(..., ge=1, description="순위")


class SearchResponse(BaseModel):
    """검색 응답"""

    results: List[SearchResult]
    total: int = Field(..., ge=0, description="총 결과 수")
    query: str = Field(..., description="검색 쿼리")
    query_time_ms: int = Field(..., ge=0, description="쿼리 실행 시간 (밀리초)")


class VideoURLResponse(BaseModel):
    """비디오 URL 응답"""

    video_url: str = Field(..., description="Signed URL")
    expires_in: int = Field(..., description="만료 시간 (초)")
    hand_id: str = Field(..., description="핸드 ID")


class HealthResponse(BaseModel):
    """헬스 체크 응답"""

    status: str = Field(..., description="상태 (ok/error)")
    version: str = Field(..., description="버전")
    timestamp: datetime = Field(..., description="응답 시각")
