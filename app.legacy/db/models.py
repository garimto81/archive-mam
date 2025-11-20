"""
PostgreSQL 데이터베이스 모델 (SQLAlchemy ORM)
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Integer, Float, ARRAY, Text,
    TIMESTAMP, BigInteger, JSON, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Hand(Base):
    """포커 핸드 메타데이터"""
    __tablename__ = "hands"

    id = Column(String, primary_key=True)
    tournament_id = Column(String, ForeignKey("tournaments.id"), nullable=False)
    hand_number = Column(Integer, nullable=False)

    # 시간 정보
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    duration_seconds = Column(Integer)

    # 핸드 정보
    street = Column(String)  # PREFLOP, FLOP, TURN, RIVER
    pot_bb = Column(Float)
    hero_position = Column(String)
    villain_position = Column(String)

    # 플레이어 정보
    hero_name = Column(String)
    villain_name = Column(String)
    hero_stack_bb = Column(Float)
    villain_stack_bb = Column(Float)

    # 액션 정보
    action_sequence = Column(ARRAY(String))
    hero_action = Column(String)
    result = Column(String)  # WIN, LOSE, SPLIT

    # 태그 & 분류
    tags = Column(ARRAY(String))
    hand_type = Column(String)

    # 자연어 설명
    description = Column(Text)
    language_tokens = Column(TSVECTOR)

    # 멀티모달 임베딩 (1024차원)
    embedding = Column(Vector(1024))

    # 영상 메타데이터
    video_file_path = Column(String)
    video_start_time = Column(Float)
    video_end_time = Column(Float)
    thumbnail_url = Column(String)

    # 메타데이터
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 인덱스
    __table_args__ = (
        Index("hands_embedding_idx", "embedding", postgresql_using="hnsw"),
        Index("hands_language_tokens_idx", "language_tokens", postgresql_using="gin"),
        Index("hands_tournament_idx", "tournament_id"),
        Index("hands_timestamp_idx", "timestamp", postgresql_ops={"timestamp": "DESC"}),
        Index("hands_tags_idx", "tags", postgresql_using="gin"),
        Index("hands_pot_bb_idx", "pot_bb", postgresql_ops={"pot_bb": "DESC"}),
    )

    def to_dict(self) -> dict:
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "tournament_id": self.tournament_id,
            "hand_number": self.hand_number,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration_seconds": self.duration_seconds,
            "street": self.street,
            "pot_bb": self.pot_bb,
            "hero_position": self.hero_position,
            "villain_position": self.villain_position,
            "hero_name": self.hero_name,
            "villain_name": self.villain_name,
            "hero_stack_bb": self.hero_stack_bb,
            "villain_stack_bb": self.villain_stack_bb,
            "action_sequence": self.action_sequence,
            "hero_action": self.hero_action,
            "result": self.result,
            "tags": self.tags,
            "hand_type": self.hand_type,
            "description": self.description,
            "video_file_path": self.video_file_path,
            "video_start_time": self.video_start_time,
            "video_end_time": self.video_end_time,
            "thumbnail_url": self.thumbnail_url,
        }


class Tournament(Base):
    """토너먼트 정보"""
    __tablename__ = "tournaments"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    event_type = Column(String)  # WSOP, MPP, APL
    start_date = Column(TIMESTAMP(timezone=True))
    end_date = Column(TIMESTAMP(timezone=True))
    location = Column(String)
    buy_in = Column(Integer)
    total_entries = Column(Integer)

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "event_type": self.event_type,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "location": self.location,
            "buy_in": self.buy_in,
            "total_entries": self.total_entries,
        }


class Player(Base):
    """플레이어 정보"""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    nickname = Column(ARRAY(String))
    country = Column(String)

    # 통계
    total_hands = Column(Integer, default=0)
    famous_hands = Column(ARRAY(String))

    # 임베딩 (플레이어 스타일 벡터)
    player_embedding = Column(Vector(512))

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("players_name_trgm_idx", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "nickname": self.nickname,
            "country": self.country,
            "total_hands": self.total_hands,
            "famous_hands": self.famous_hands,
        }


class VideoFile(Base):
    """영상 파일 메타데이터"""
    __tablename__ = "video_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String, unique=True, nullable=False)
    tournament_id = Column(String, ForeignKey("tournaments.id"))

    # 파일 정보
    file_size_bytes = Column(BigInteger)
    duration_seconds = Column(Integer)
    resolution = Column(String)
    codec = Column(String)

    # 처리 상태
    processing_status = Column(String, default="pending")
    indexed_at = Column(TIMESTAMP(timezone=True))

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("video_files_tournament_idx", "tournament_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "tournament_id": self.tournament_id,
            "file_size_bytes": self.file_size_bytes,
            "duration_seconds": self.duration_seconds,
            "resolution": self.resolution,
            "codec": self.codec,
            "processing_status": self.processing_status,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
        }


class SearchQuery(Base):
    """검색 쿼리 로그 (분석용)"""
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(1024))

    # 검색 파라미터
    filters = Column(JSON)
    search_method = Column(String)  # hybrid, vector_only, bm25_only

    # 결과
    result_count = Column(Integer)
    top_result_id = Column(String)
    avg_score = Column(Float)

    # 사용자 피드백
    clicked_result_id = Column(String)
    feedback_score = Column(Integer)  # 1-5 rating

    # 성능 메트릭
    latency_ms = Column(Integer)

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "query_text": self.query_text,
            "filters": self.filters,
            "search_method": self.search_method,
            "result_count": self.result_count,
            "top_result_id": self.top_result_id,
            "avg_score": self.avg_score,
            "clicked_result_id": self.clicked_result_id,
            "feedback_score": self.feedback_score,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
