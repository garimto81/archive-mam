"""
Pydantic 모델 정의
API 요청/응답에 사용되는 데이터 모델
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ====================
# 검색 관련 모델
# ====================

class SearchRequest(BaseModel):
    """검색 요청 모델"""
    query: str = Field(..., description="검색 쿼리", min_length=1, max_length=500)
    top_k: Optional[int] = Field(5, description="반환할 결과 개수", ge=1, le=20)
    similarity_threshold: Optional[float] = Field(0.7, description="유사도 임계값", ge=0.0, le=1.0)


class HandResult(BaseModel):
    """핸드 검색 결과 모델"""
    hand_id: str = Field(..., description="핸드 ID")
    hero_name: str = Field(..., description="Hero 이름")
    villain_name: Optional[str] = Field(None, description="Villain 이름")
    description: str = Field(..., description="핸드 설명")
    pot_bb: float = Field(..., description="팟 사이즈 (BB)")
    street: str = Field(..., description="스트리트 (Preflop/Flop/Turn/River)")
    action: str = Field(..., description="액션 (Bet/Call/Raise/Fold)")
    tournament: Optional[str] = Field(None, description="토너먼트명")
    tags: List[str] = Field(default_factory=list, description="태그 목록")
    video_url: Optional[str] = Field(None, description="비디오 URL")
    timestamp: Optional[str] = Field(None, description="비디오 타임스탬프")
    distance: Optional[float] = Field(None, description="검색 거리 (유사도)")


class SearchResponse(BaseModel):
    """검색 응답 모델"""
    query: str = Field(..., description="원본 쿼리")
    total_results: int = Field(..., description="총 결과 개수")
    results: List[HandResult] = Field(..., description="검색 결과 목록")
    search_time_ms: float = Field(..., description="검색 소요 시간 (밀리초)")


# ====================
# RAG 관련 모델
# ====================

class RAGRequest(BaseModel):
    """RAG 요청 모델"""
    query: str = Field(..., description="사용자 질문", min_length=1, max_length=1000)
    top_k: Optional[int] = Field(5, description="검색할 핸드 개수", ge=1, le=10)
    use_thinking_mode: Optional[bool] = Field(True, description="Qwen3 Thinking Mode 사용 여부")


class RAGResponse(BaseModel):
    """RAG 응답 모델"""
    query: str = Field(..., description="원본 질문")
    answer: str = Field(..., description="LLM 생성 답변")
    context_hands: List[HandResult] = Field(..., description="컨텍스트로 사용된 핸드 목록")
    total_time_ms: float = Field(..., description="총 소요 시간 (밀리초)")
    search_time_ms: float = Field(..., description="검색 소요 시간 (밀리초)")
    llm_time_ms: float = Field(..., description="LLM 생성 소요 시간 (밀리초)")


# ====================
# 핸드 상세 정보 모델
# ====================

class HandDetail(BaseModel):
    """핸드 상세 정보 모델 (BigQuery에서 조회)"""
    hand_id: str
    hero_name: str
    villain_name: Optional[str] = None
    description: str
    pot_bb: float
    street: str
    action: str
    hero_cards: Optional[str] = None
    board: Optional[str] = None
    tournament: Optional[str] = None
    year: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    video_file_path: Optional[str] = None
    video_url: Optional[str] = None
    timestamp: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class HandDetailResponse(BaseModel):
    """핸드 상세 정보 응답 모델"""
    hand: HandDetail
    query_time_ms: float


# ====================
# 에러 응답 모델
# ====================

class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    error: str = Field(..., description="에러 타입")
    message: str = Field(..., description="에러 메시지")
    details: Optional[dict] = Field(None, description="추가 에러 정보")


# ====================
# BigQuery 모델 (내부 사용)
# ====================

class HandSummaryRow(BaseModel):
    """BigQuery hand_summary 테이블 행 모델"""
    hand_id: str
    hero_name: str
    villain_name: Optional[str] = None
    description: str
    pot_bb: float
    street: str
    action: str
    hero_cards: Optional[str] = None
    board: Optional[str] = None
    tournament: Optional[str] = None
    year: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None  # 768-dim TextEmbedding-004
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class VideoFileRow(BaseModel):
    """BigQuery video_files 테이블 행 모델"""
    video_id: str
    file_path: str
    gcs_uri: Optional[str] = None
    proxy_gcs_uri: Optional[str] = None
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    codec: Optional[str] = None
    file_size_mb: Optional[float] = None
    created_at: Optional[str] = None
