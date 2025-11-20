"""
데이터베이스 연결 및 세션 관리
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.config import settings
from app.db.models import Base


# Database Engine
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # 연결 상태 확인
    echo=settings.debug,  # SQL 로깅
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session

    Usage:
        @app.get("/hands")
        def get_hands(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    데이터베이스 테이블 생성

    주의: 프로덕션에서는 Alembic 마이그레이션 사용 권장
    """
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    모든 테이블 삭제 (테스트용)

    경고: 프로덕션에서 사용 금지!
    """
    if settings.environment == "production":
        raise RuntimeError("Cannot drop database in production!")
    Base.metadata.drop_all(bind=engine)


# Health check
def check_db_connection() -> bool:
    """데이터베이스 연결 상태 확인"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
