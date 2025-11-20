"""
포커 아카이브 검색 시스템 - 환경 설정
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Application
    app_name: str = Field(default="archive-mam", alias="APP_NAME")
    app_version: str = Field(default="3.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")

    # API Server
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=4, alias="API_WORKERS")

    # PostgreSQL + pgvector
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/poker_archive",
        alias="DATABASE_URL"
    )
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")

    # Apache Kafka
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_topic_hands: str = Field(default="poker-hands", alias="KAFKA_TOPIC_HANDS")
    kafka_topic_videos: str = Field(default="poker-videos", alias="KAFKA_TOPIC_VIDEOS")
    kafka_consumer_group: str = Field(default="archive-consumer", alias="KAFKA_CONSUMER_GROUP")

    # Korean NLP
    korean_nlp_model: str = Field(
        default="jhgan/ko-sbert-multitask",
        alias="KOREAN_NLP_MODEL"
    )
    mecab_dic_path: Optional[str] = Field(
        default="/usr/local/lib/mecab/dic/mecab-ko-dic",
        alias="MECAB_DIC_PATH"
    )

    # Multimodal Embeddings
    clip_model: str = Field(
        default="openai/clip-vit-large-patch14",
        alias="CLIP_MODEL"
    )
    embedding_dim: int = Field(default=1024, alias="EMBEDDING_DIM")

    # Voyage AI (Optional)
    voyage_api_key: Optional[str] = Field(default=None, alias="VOYAGE_API_KEY")
    voyage_model: str = Field(default="voyage-multimodal-3", alias="VOYAGE_MODEL")

    # Haystack RAG
    haystack_telemetry_enabled: bool = Field(
        default=False,
        alias="HAYSTACK_TELEMETRY_ENABLED"
    )
    rag_top_k: int = Field(default=20, alias="RAG_TOP_K")
    rag_similarity_threshold: float = Field(default=0.7, alias="RAG_SIMILARITY_THRESHOLD")

    # Search Weights (Hybrid Search)
    search_vector_weight: float = Field(default=0.6, alias="SEARCH_VECTOR_WEIGHT")
    search_bm25_weight: float = Field(default=0.3, alias="SEARCH_BM25_WEIGHT")
    search_filter_weight: float = Field(default=0.1, alias="SEARCH_FILTER_WEIGHT")

    # Video Storage
    video_storage_path: str = Field(
        default="/mnt/nas/poker-videos",
        alias="VIDEO_STORAGE_PATH"
    )
    video_proxy_path: str = Field(
        default="/mnt/storage/proxy-videos",
        alias="VIDEO_PROXY_PATH"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        alias="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    # Cache
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins를 리스트로 반환"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
settings = Settings()
