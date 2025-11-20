"""
FastAPI 애플리케이션 설정
v4.0.0 - Vertex AI Vector Search + BigQuery
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # GCP 프로젝트
    GCP_PROJECT: str = "gg-poker-prod"
    GCP_REGION: str = "us-central1"

    # BigQuery
    BIGQUERY_DATASET: str = "poker_archive"
    BIGQUERY_TABLE: str = "hands"

    # GCS
    GCS_METADATA_BUCKET: str = "ati-metadata-prod"
    GCS_VIDEOS_BUCKET: str = "poker-videos-prod"

    # Vertex AI Vector Search
    VERTEX_AI_INDEX_ENDPOINT: str = os.getenv("VERTEX_AI_INDEX_ENDPOINT", "")
    VERTEX_AI_DEPLOYED_INDEX_ID: str = os.getenv("VERTEX_AI_DEPLOYED_INDEX_ID", "")

    # API 설정
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "ATI Poker Archive Search"
    VERSION: str = "4.0.0"

    # CORS
    CORS_ORIGINS: list = ["*"]  # 프로덕션에서는 특정 도메인만 허용

    # Signed URL 만료 시간 (초)
    SIGNED_URL_EXPIRATION: int = 3600  # 1시간

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
